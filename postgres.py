import psycopg2
import psycopg2.extras
import traceback
import os
from pathlib import Path


db_connection_string = f"""host={os.getenv('PG_HOST')}
    port={os.getenv('PG_PORT')}
    sslmode={os.getenv('SSLMODE')}
    dbname={os.getenv('PG_DB')}
    user={os.getenv('PG_USER')}
    password={os.getenv('PG_PASSWORD')}
    target_session_attrs={os.getenv('TARGET_SESSION_ATTRS')}"""


class DB:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.connection = None
        self.connect()

    def connect(self):
        if not self.connection:
            try:
                self.connection = psycopg2.connect(self.connection_string)
            except (Exception, psycopg2.Error) as error:
                print("PostgreSQL error:", error)
        return self.connection

    def __enter__(self):
        return self

    def create_files_table(self):
        """Create table in db for files info."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS files (
                                     file_id SERIAL PRIMARY KEY,
                                     filename VARCHAR,
                                     client_id INT,
                                     creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                     file_group VARCHAR,
                                     file_path VARCHAR);""")
            self.connection.commit()
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            print("PostgreSQL error:", error)

    def get_list_of_files(self, client_id):
        files = []
        try:
            dict_cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            dict_cursor.execute(f"""SELECT filename, client_id, creation_date, file_group, file_id
                                     FROM files
                                    WHERE client_id = {client_id};""")
            files = dict_cursor.fetchall()
            dict_cursor.close()
        except (Exception, psycopg2.Error) as error:
            print("PostgreSQL error:", error)
        return files

    def insert_file_info_into_files_table(self, filename, client_id, file_group, file_path):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""INSERT INTO files (filename, client_id, file_group, file_path)
                              VALUES (%s, %s, %s, %s);""", (filename, client_id, file_group, file_path))
            self.connection.commit()
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            print("PostgreSQL error:", error)

    def get_file_path_from_files_table(self, file_id):
        file_path = ""
        try:
            cursor = self.connection.cursor()
            query = f"""SELECT file_path
                                  FROM files
                                 WHERE file_id = {file_id};"""
            cursor.execute(query)
            file_path = cursor.fetchone()[0]
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            print("PostgreSQL error:", error)
        return file_path

    def create_templates_table(self):
        """Create table in db for templates info."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS templates (
                                     file_id SERIAL PRIMARY KEY,
                                     filename VARCHAR,
                                     creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                     file_group VARCHAR,
                                     file_path VARCHAR);""")
            self.connection.commit()
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            print("PostgreSQL error:", error)

    def insert_file_info_into_templates_table(self, filename, file_group, file_path):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""INSERT INTO templates (filename, file_group, file_path)
                              VALUES (%s, %s, %s);""", (filename, file_group, file_path))
            self.connection.commit()
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            print("PostgreSQL error:", error)

    def get_list_of_templates(self):
        files = []
        try:
            dict_cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            dict_cursor.execute("""SELECT filename, file_group, file_id
                                     FROM templates;""")
            files = dict_cursor.fetchall()
            dict_cursor.close()
        except (Exception, psycopg2.Error) as error:
            print("PostgreSQL error:", error)
        return files

    def get_file_path_from_templates_table(self, file_id):
        file_path = ""
        try:
            cursor = self.connection.cursor()
            query = f"""SELECT file_path
                          FROM templates
                         WHERE file_id = {file_id};"""
            cursor.execute(query)
            file_path = cursor.fetchone()[0]
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            print("PostgreSQL error:", error)
        return file_path

    def create_client_files_table(self):
        """Create table in db for client files info."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS client_files (
                                     file_id SERIAL PRIMARY KEY,
                                     filename VARCHAR,
                                     client_id INT,
                                     creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                     file_group VARCHAR,
                                     file_path VARCHAR);""")
            self.connection.commit()
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            print("PostgreSQL error:", error)

    def insert_file_info_into_client_files_table(self, filename, client_id, file_group, file_path):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""INSERT INTO client_files (filename, client_id, file_group, file_path)
                              VALUES (%s, %s, %s, %s);""", (filename, client_id, file_group, file_path))
            self.connection.commit()
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            print("PostgreSQL error:", error)

    def get_list_of_client_files(self, client_id):
        files = []
        try:
            dict_cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            dict_cursor.execute(f"""SELECT filename, client_id, creation_date, file_group, file_id
                                     FROM client_files
                                    WHERE client_id = {client_id};""")
            files = dict_cursor.fetchall()
            dict_cursor.close()
        except (Exception, psycopg2.Error) as error:
            print("PostgreSQL error:", error)
        return files

    def get_file_path_from_client_files_table(self, file_id):
        file_path = ""
        try:
            cursor = self.connection.cursor()
            query = f"""SELECT file_path
                          FROM client_files
                         WHERE file_id = {file_id};"""
            cursor.execute(query)
            file_path = cursor.fetchone()[0]
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            print("PostgreSQL error:", error)
        return file_path

    def close(self):
        if self.connection:
            self.connection.close()

    def __exit__(self, exc_type, exc_value, tb):
        self.close()
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
            # return False # uncomment to pass exception through
        return True


if __name__ == "__main__":
    # Create dirs and db tables if they do not exist
    Path("./files_storage/files").mkdir(parents=True, exist_ok=True)
    Path("./files_storage/templates").mkdir(parents=True, exist_ok=True)
    Path("./files_storage/clients_files").mkdir(parents=True, exist_ok=True)
    with DB(db_connection_string) as db:
        db.create_files_table()
        db.create_templates_table()
        db.create_client_files_table()

