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
  `paired_id` INT null,
  `pairing_group_id` INT null
);"""
    db.execute(users_table)
    
    sessions_table = """create table if not exists sessions (
    `session` VARCHAR(255) not null primary key,
    `user_id` INT not null,
    `expiry` DATETIME not null default (datetime('now', '+1 days'))
);"""
    db.execute(sessions_table)

    messages_table = """create table if not exists messages (
    `id` integer not null primary key autoincrement,
    `pairing_group_id` INT not null,
    `sender_id` INT not null,
    `message` TEXT not null,
    `timestamp` DATETIME not null default (datetime('now'))
);"""
    db.execute(messages_table)

    # Pairing group id will be -1 for templates
    assignments_table = """create table if not exists assignments (
    `id` integer not null primary key autoincrement,
    `pairing_group_id` INT not null,
    `title` VARCHAR(255) not null,
    `description` TEXT not null,
    `creation_date` DATETIME not null default (datetime('now')),
    `due_date` DATETIME not null,
    `is_draft` BOOLEAN not null default 1,
    `type` VARCHAR(50) not null,
    `data` TEXT not null
);"""
    db.execute(assignments_table)

    submissions_table = """create table if not exists submissions (
    `id` integer not null primary key autoincrement,
    `assignment_id` INT not null,
    `data` TEXT not null,
    `submission_date` DATETIME not null default (datetime('now'))
);"""
    db.execute(submissions_table)

    scratchpad_table = """create table if not exists scratchpad (
    `id` integer not null primary key autoincrement,
    `pairing_group_id` INT not null,
    `title` VARCHAR(255) not null,
    `content` TEXT not null,
    `linked_assignment_id` INT null,
    `last_modified` DATETIME not null default (datetime('now'))
);"""
    db.execute(scratchpad_table)



class UserExistsException(Exception):
    pass

class UserNotFoundException(Exception):
    pass

class InvalidPasswordException(Exception):
    pass

class AssignmentNotFoundException(Exception):
    pass

class AssignmentSubmissionException(Exception):
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
        rows = db.fetch("""select * from users where username = '%s';""", (username))
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
        rows = db.fetch("""select * from users where id = %d;""", (user_id))
        if len(rows) == 0:
            return None
        user = rows[0]
        return User(user, None)
    
    @staticmethod
    def from_session(session_token):
        rows = db.fetch("""select u.* from users u join sessions s on u.id = s.user_id where s.session = '%s' and s.expiry > datetime('now');""", (session_token))
        if len(rows) == 0:
            return None
        user = rows[0]
        return User(user, session_token)
    
    @staticmethod
    def pair_users(mentor_id, student_id):
        student = User.from_id(student_id)
        mentor = User.from_id(mentor_id)
        if student is None or mentor is None:
            raise UserNotFoundException("One or both users not found")
        if student.paired_id is not None or mentor.paired_id is not None:
            raise Exception("One or both users are already paired")

        max_group_id_rows = db.fetch("""select max(pairing_group_id) as max_id from users;""")
        max_group_id = max_group_id_rows[0]['max_id']
        if max_group_id is None:
            max_group_id = 0
        new_group_id = max_group_id + 1
        db.execute("""update users set paired_id = %d, pairing_group_id = %d where id = %d;""", (student_id, new_group_id, mentor_id))
        db.execute("""update users set paired_id = %d, pairing_group_id = %d where id = %d;""", (mentor_id, new_group_id, student_id))


    def __init__(self, sql_data, session_token):
        self.id = sql_data['id']
        self.first_name = sql_data['first_name']
        self.last_name = sql_data['last_name']
        self.username = sql_data['username']
        self.is_mentor = sql_data['is_mentor']
        self.paired_id = sql_data['paired_id']
        self.pairing_group_id = sql_data['pairing_group_id']

        self.session_token = session_token

    def __str__(self):
        return f"User(id={self.id}, first_name={self.first_name}, last_name={self.last_name}, username={self.username}, is_mentor={self.is_mentor})"
    
    def get_paired_user(self):
        rows = db.fetch("""select paired_id from users where id = %d;""", (self.id))
        self.paired_id = rows[0]['paired_id']
        if self.paired_id is None:
            return None
        return User.from_id(self.paired_id)
    
    def is_authenticated(self):
        if self.session_token is None:
            return False
        select_sql = """select * from sessions where session = '%s' and expiry > datetime('now');""" % (self.session_token)
        rows = db.fetch(select_sql)
        return len(rows) > 0
    
    def get_session_token(self):
        return self.session_token
    
    def pair_with(self, other_user):
        User.pair_users(self.id, other_user.id)


    # For the conversation feature
    def get_conversation_history(self, limit=50):
        messages = db.fetch("""select * from messages where pairing_group_id = %d order by timestamp desc limit %d;""", (self.pairing_group_id, limit))
        return messages[::-1]

    def send_to_paired(self, message):
        if self.paired_id is None:
            raise UserNotFoundException("User is not paired with anyone")
        db.execute("""insert into messages (pairing_group_id, sender_id, message) values (%d, %d, '%s');""", (self.pairing_group_id, self.id, message))


    # For assignments
    def get_assignments(self):
        # get assignments where pairing_group_id matches user's pairing_group_id or is -1
        assignments = db.fetch("""select * from assignments where pairing_group_id = %d or pairing_group_id = -1;""", (self.pairing_group_id))
        # if they aren't a mentor, hide drafts and templates
        if not self.is_mentor:
            assignments = [a for a in assignments if a['is_draft'] == 0 and a['pairing_group_id'] != -1]

        assignment_objs = []
        for a in assignments:
            assignment_objs.append(Assignment(a))
            
        return assignment_objs
    
    def submit_assignment(self, assignment_id, data):
        # TODO fix
        assignment_rows = db.fetch("""select * from assignments where id = %d;""", (assignment_id))
        if len(assignment_rows) == 0:
            raise AssignmentNotFoundException("Assignment not found")
        assignment = assignment_rows[0]
        if assignment['pairing_group_id'] != self.pairing_group_id and assignment['pairing_group_id'] != -1:
            raise AssignmentSubmissionException("User not allowed to submit this assignment")
        db.execute("""insert into submissions (assignment_id, data) values (%d, '%s');""", (assignment_id, data))

    # For scratchpad
    def get_scratchpads(self):
        scratchpads = db.fetch("""select * from scratchpad where pairing_group_id = %d;""", (self.pairing_group_id))
        for i in range(len(scratchpads)):
            scratchpads[i] = Scratchpad(scratchpads[i])
        return scratchpads
    

class Assignment:
    @staticmethod
    def new(creator):
        pairing_group_id = creator.pairing_group_id
        if pairing_group_id is None:
            raise Exception("User must be paired to create an assignment")
        cursor = db.execute("""insert into assignments (pairing_group_id, title, description, due_date, is_draft, type, data) values (%d, '', '', datetime('now', '+7 days'), 1, '', '');""", (pairing_group_id))
        assignment_id = cursor.lastrowid
        return Assignment.from_id(assignment_id)
    
    @staticmethod
    def from_id(assignment_id):
        rows = db.fetch("""select * from assignments where id = %d;""", (assignment_id))
        if len(rows) == 0:
            return None
        sql_data = rows[0]
        return Assignment(sql_data)

    def __init__(self, sql_data):
        self.id = sql_data['id']
        self.pairing_group_id = sql_data['pairing_group_id']
        self.title = sql_data['title']
        self.description = sql_data['description']
        self.creation_date = sql_data['creation_date']
        self.due_date = sql_data['due_date']
        self.is_draft = sql_data['is_draft']
        self.type = sql_data['type']
        self.data = sql_data['data']


    def set_title(self, title):
        db.execute("""update assignments set title = '%s' where id = %d;""", (title, self.id))
        self.title = title

    def set_description(self, description):
        db.execute("""update assignments set description = '%s' where id = %d;""", (description, self.id))
        self.description = description

    def set_due_date(self, due_date):
        db.execute("""update assignments set due_date = '%s' where id = %d;""", (due_date, self.id))
        self.due_date = due_date

    def publish(self):
        db.execute("""update assignments set is_draft = 0 where id = %d;""", (self.id))
        self.is_draft = 0

    def unpublish(self):
        db.execute("""update assignments set is_draft = 1 where id = %d;""", (self.id))
        self.is_draft = 1

class Scratchpad:
    @staticmethod
    def new(user, title, content, linked_assignment_id=None):
        pairing_group_id = user.pairing_group_id
        if pairing_group_id is None:
            raise Exception("User must be paired to create a scratchpad")
        db.execute("""insert into scratchpad (pairing_group_id, title, content, linked_assignment_id) values (%d, '%s', '%s', %s);""", (pairing_group_id, title, content, linked_assignment_id if linked_assignment_id is not None else 'NULL'))
    
    @staticmethod
    def from_id(scratchpad_id):
        rows = db.fetch("""select * from scratchpad where id = %d;""", (scratchpad_id))
        if len(rows) == 0:
            return None
        sql_data = rows[0]
        return Scratchpad(sql_data)

    def __init__(self, sql_data):
        self.id = sql_data['id']
        self.pairing_group_id = sql_data['pairing_group_id']
        self.title = sql_data['title']
        self.content = sql_data['content']
        self.linked_assignment_id = sql_data['linked_assignment_id']
        self.last_modified = sql_data['last_modified']

    def set_title(self, title):
        db.execute("""update scratchpad set title = '%s' where id = %d;""", (title, self.id))
        self.title = title

    def set_content(self, content):
        db.execute("""update scratchpad set content = '%s', last_modified = datetime('now') where id = %d;""", (content, self.id))
        self.content = content

if __name__ == "__main__":
    import os
    
    if os.path.exists("app_database.sqlite"):
        os.remove("app_database.sqlite")
    build_databases()

    User.new_mentor("Alice", "Smith", "alice", "password123")
    User.new_student("Bob", "Johnson", "bob", "securepassword")

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

    print("Creating an assignment...")
    assignment = Assignment.new(mentor)
    print("Assignment created with ID:", assignment.id)

