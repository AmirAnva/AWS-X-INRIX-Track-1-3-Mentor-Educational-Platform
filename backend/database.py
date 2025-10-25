import sqlite3
import traceback
import MySQLdb
import bcrypt
import secrets


class SQLiteDB:
    def __init__(self, db_name):
        self.db_name = db_name
        self.connect()

    def connect(self):
        self.connection = sqlite3.connect(self.db_name, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row

    def execute(self, sql, args=None, tries=0):
        if args is not None:
            sql = sql % args
        try:
            cursor = self.cursor()
            cursor.execute(sql)
            self.connection.commit()
        except (AttributeError, MySQLdb.OperationalError):
            self.connect()
            if tries == 1:
                print(traceback.format_exc())
                return None
            self.execute(sql, args, tries + 1)
        return cursor

    def fetch(self, sql, args=None):
        cursor = self.execute(sql, args)
        rows = [dict(row) for row in cursor.fetchall()]
        return rows

    def cursor(self):
        return self.connection.cursor()

db = SQLiteDB("app_database.sqlite")

def build_databases():
    users_table = """create table if not exists users (
  `id` integer not null primary key autoincrement,
  `first_name` VARCHAR(255) not null,
  `last_name` VARCHAR(255) not null,
  `username` VARCHAR(255) not null,
  `password` VARCHAR(255) not null,
  `is_mentor` BOOLEAN not null default 0,
  `paired_id` INT null
);"""
    db.execute(users_table)
    
    sessions_table = """create table if not exists sessions (
    `session` VARCHAR(255) not null primary key,
    `user_id` INT not null,
    `expiry` DATETIME not null default (datetime('now', '+1 days'))
);"""
    db.execute(sessions_table)

class UserExistsException(Exception):
    pass

class UserNotFoundException(Exception):
    pass

class InvalidPasswordException(Exception):
    pass

class User:
    @staticmethod
    def new_mentor(first_name, last_name, username, password):
        User.new(first_name, last_name, username, password, 1)

    @staticmethod
    def new_student(first_name, last_name, username, password):
        User.new(first_name, last_name, username, password, 0)

    @staticmethod
    def new(first_name, last_name, username, password, is_mentor):
        rows = db.fetch("""select * from users where username = '%s';""" % (username))
        if len(rows) > 0:
            raise UserExistsException("Username already in use")
        
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        db.execute("""insert into users (first_name, last_name, username, password, is_mentor) values ('%s', '%s', '%s', '%s', %d);""", (first_name, last_name, username, hashed_pw, is_mentor))
    
    @staticmethod
    def from_credentials(username, password):
        select_sql = """select * from users where username = '%s';""" % (username)
        rows = db.fetch(select_sql)
        if len(rows) == 0:
            raise UserNotFoundException(f"User '{username}' not found")
        user = rows[0]
        if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            raise InvalidPasswordException(f"Invalid password for user '{username}'")
        
        session_token = secrets.token_hex(32)
        db.execute("""insert into sessions (session, user_id, expiry) values ('%s', %d, datetime('now', '+1 days'));""", (session_token, user['id']))

        return User(user, session_token)

    @staticmethod
    def from_id(user_id):
        select_sql = """select * from users where id = %d;""" % (user_id)
        rows = db.fetch(select_sql)
        if len(rows) == 0:
            return None
        user = rows[0]
        return User(user, None)
    
    @staticmethod
    def pair_users(mentor_id, student_id):
        student = User.from_id(student_id)
        mentor = User.from_id(mentor_id)
        if student is None or mentor is None:
            raise UserNotFoundException("One or both users not found")
        if student.paired_id is not None or mentor.paired_id is not None:
            raise Exception("One or both users are already paired")
        db.execute("""update users set paired_id = %d where id = %d;""", (student_id, mentor_id))
        db.execute("""update users set paired_id = %d where id = %d;""", (mentor_id, student_id))

    def __init__(self, sql_data, session_token):
        self.id = sql_data['id']
        self.first_name = sql_data['first_name']
        self.last_name = sql_data['last_name']
        self.username = sql_data['username']
        self.is_mentor = sql_data['is_mentor']
        self.paired_id = sql_data['paired_id']

        self.session_token = session_token

    def __str__(self):
        return f"User(id={self.id}, first_name={self.first_name}, last_name={self.last_name}, username={self.username}, is_mentor={self.is_mentor})"
    
    def get_paired_user(self):
        if self.paired_id is None:
            return None
        return User.from_id(self.paired_id)
    
    def pair_with(self, other_user):
        User.pair_users(self.id, other_user.id)
    

def pair_users(mentor_id, student_id):
    db.execute("""update users set paired_id = %d where id = %d;""", (student_id, mentor_id))
    db.execute("""update users set paired_id = %d where id = %d;""", (mentor_id, student_id))

build_databases()

if __name__ == "__main__":
    # User.new_mentor("Alice", "Smith", "alice", "password123")
    # User.new_student("Bob", "Johnson", "bob", "securepassword")

    

    print("Getting mentor:")
    mentor = User.from_credentials("alice", "password123")
    print(mentor)

    print("Getting student:")
    student = User.from_credentials("bob", "securepassword")
    print(student)
    
    print("Getting student pair")
    paired_student = mentor.get_paired_user()
    print(paired_student)

    print("Paring users...")
    mentor.pair_with(student)

    print("Getting student pair after pairing")
    paired_student = mentor.get_paired_user()
    print(paired_student)
