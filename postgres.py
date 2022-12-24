import psycopg2
import psycopg2.extras
import traceback
import os
import my_logger
import csv
from pathlib import Path
from io import StringIO
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

db_connection_string = f"""host={os.getenv('PG_HOST')}
        port={os.getenv('PG_PORT')}
        sslmode={os.getenv('SSLMODE')}
        dbname={os.getenv('PG_DB')}
        user={os.getenv('PG_USER')}
        password={os.getenv('PG_PASSWORD')}
        target_session_attrs={os.getenv('TARGET_SESSION_ATTRS')}"""
sqlalch_db_conn_str = (f'postgresql://{os.getenv("PG_USER")}:{os.getenv("PG_PASSWORD")}'
                       f'@{os.getenv("PG_HOST")}:{os.getenv("PG_PORT")}/{os.getenv("PG_DB")}')
connection_args = {'sslmode': os.getenv('SSLMODE'),
                   'target_session_attrs': os.getenv('TARGET_SESSION_ATTRS')}


# create logger
logger = my_logger.init_logger("postgres")


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

    def delete_from_table(self, table_name, file_id):
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"DELETE FROM {table_name} WHERE file_id = {file_id};")
            self.connection.commit()
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            logger.error(repr(error))

    def get_client_store_names(self, client_id):
        """Returns list of client store names from account_list table."""
        names = []
        try:
            cursor = self.connection.cursor()
            query = f"""SELECT name
                          FROM account_list
                         WHERE client_id = {client_id} AND status_1 = "Active";"""
            cursor.execute(query)
            for row in cursor.fetchall():
                names.append(row[0])
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            logger.error(repr(error))
        return names

    def delete_duplicates_from_data_analytics_bydays_main_table(self):
        """Delete duplicates from data_analytics_bydays_main table."""
        try:
            cursor = self.connection.cursor()
            delete_query = """DELETE FROM data_analytics_bydays_main 
                               WHERE ctid IN 
                                    (SELECT ctid 
                                       FROM (SELECT ctid,
                                                    row_number() OVER (PARTITION BY api_id, sku_id, date, region_id
                                                    ORDER BY id DESC) AS row_num
                                               FROM data_analytics_bydays_main
                                            ) t
                                      WHERE t.row_num > 1
                                    );"""
            cursor.execute(delete_query)
            self.connection.commit()
            cursor.close()
        except (Exception, psycopg2.Error) as e:
            print("PostgreSQL error:", e)

    def close(self):
        if self.connection:
            self.connection.close()

    def __exit__(self, exc_type, exc_value, tb):
        self.close()
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
            # return False # uncomment to pass exception through
        return True


def psql_insert_copy(table, conn, keys, data_iter):
    """
    Execute SQL statement inserting data

    Parameters
    ----------
    table : pandas.io.sql.SQLTable
    conn : sqlalchemy.engine.Engine or sqlalchemy.engine.Connection
    keys : list of str
        Column names
    data_iter : Iterable that iterates the values to be inserted
    """
    # gets a DBAPI connection that can provide a cursor
    dbapi_conn = conn.connection
    with dbapi_conn.cursor() as cur:
        s_buf = StringIO()
        writer = csv.writer(s_buf)
        writer.writerows(data_iter)
        s_buf.seek(0)

        columns = ', '.join(['"{}"'.format(k) for k in keys])
        if table.schema:
            table_name = '{}.{}'.format(table.schema, table.name)
        else:
            table_name = table.name

        sql = 'COPY {} ({}) FROM STDIN WITH CSV'.format(
            table_name, columns)
        cur.copy_expert(sql=sql, file=s_buf)


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
