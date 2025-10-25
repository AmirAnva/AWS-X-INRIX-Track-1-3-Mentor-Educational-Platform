import sqlite3
import traceback
import MySQLdb

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
            print("Executing: " + sql)
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
    pass


