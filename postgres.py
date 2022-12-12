import psycopg2
import psycopg2.extras
import traceback
import os
import logging
from pathlib import Path


# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# create file and stream handlers and set level to debug
fh = logging.FileHandler(filename='files_load_api.log')
sh = logging.StreamHandler()
fh.setLevel(logging.DEBUG)
sh.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(module)s - %(funcName)s - %(message)s')
# add formatter to fh and sh
fh.setFormatter(formatter)
sh.setFormatter(formatter)
# add fh and sh to logger
logger.addHandler(fh)
logger.addHandler(sh)

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
                logger.critical(repr(error))
        return self.connection

    def __enter__(self):
        return self

    def create_client_report_files_table(self):
        """Create table in db for client_report_files info."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS client_report_files (
                                     file_id SERIAL PRIMARY KEY,
                                     filename VARCHAR,
                                     client_id INT,
                                     creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                     file_group VARCHAR,
                                     file_path VARCHAR);""")
            self.connection.commit()
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            logger.critical(repr(error))

    def get_list_of_client_report_files(self, client_id):
        files = []
        try:
            dict_cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            dict_cursor.execute(f"""SELECT filename, client_id, creation_date, file_group, file_id
                                     FROM client_report_files
                                    WHERE client_id = {client_id};""")
            files = dict_cursor.fetchall()
            dict_cursor.close()
        except (Exception, psycopg2.Error) as error:
            logger.error(repr(error))
        return files

    def insert_file_info_into_client_report_files_table(self, filename, client_id, file_group, file_path):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""INSERT INTO client_report_files (filename, client_id, file_group, file_path)
                              VALUES (%s, %s, %s, %s);""", (filename, client_id, file_group, file_path))
            self.connection.commit()
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            logger.error(repr(error))

    def get_file_path_from_client_report_files_table(self, file_id):
        file_path = ""
        try:
            cursor = self.connection.cursor()
            query = f"""SELECT file_path
                                  FROM client_report_files
                                 WHERE file_id = {file_id};"""
            cursor.execute(query)
            file_path = cursor.fetchone()[0]
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            logger.error(repr(error))
        return file_path

    def create_templates_table(self):
        """Create table in db for templates info."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS file_templates (
                                     file_id SERIAL PRIMARY KEY,
                                     filename VARCHAR,
                                     creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                     file_group VARCHAR,
                                     file_path VARCHAR);""")
            self.connection.commit()
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            logger.critical(repr(error))

    def insert_file_info_into_templates_table(self, filename, file_group, file_path):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""INSERT INTO file_templates (filename, file_group, file_path)
                              VALUES (%s, %s, %s);""", (filename, file_group, file_path))
            self.connection.commit()
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            logger.error(repr(error))

    def get_list_of_templates(self):
        files = []
        try:
            dict_cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            dict_cursor.execute("""SELECT filename, file_group, file_id
                                     FROM file_templates;""")
            files = dict_cursor.fetchall()
            dict_cursor.close()
        except (Exception, psycopg2.Error) as error:
            logger.error(repr(error))
        return files

    def get_file_path_from_templates_table(self, file_id):
        file_path = ""
        try:
            cursor = self.connection.cursor()
            query = f"""SELECT file_path
                          FROM file_templates
                         WHERE file_id = {file_id};"""
            cursor.execute(query)
            file_path = cursor.fetchone()[0]
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            logger.error(repr(error))
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
            logger.critical(repr(error))

    def insert_file_info_into_client_files_table(self, filename, client_id, file_group, file_path):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""INSERT INTO client_files (filename, client_id, file_group, file_path)
                              VALUES (%s, %s, %s, %s);""", (filename, client_id, file_group, file_path))
            self.connection.commit()
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            logger.error(repr(error))

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
            logger.error(repr(error))
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
            logger.error(repr(error))
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
    Path("./files_storage/client_report_files").mkdir(parents=True, exist_ok=True)
    Path("./files_storage/file_templates").mkdir(parents=True, exist_ok=True)
    Path("./files_storage/clients_files").mkdir(parents=True, exist_ok=True)
    with DB(db_connection_string) as db:
        # db.create_client_report_files_table()
        # db.create_templates_table()
        # db.create_client_files_table()
        conn = db.connect()
        cur = conn.cursor()
        cur.execute('SELECT version()')
        print(cur.fetchone())
        cur.close()
