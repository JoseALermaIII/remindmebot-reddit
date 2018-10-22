#! python3
# -*- coding: utf-8 -*-
"""Setup the MySQL-compatible database.

This module provides various functions for managing the MySQL-compatible database.
The database and tables can be created. Table data and properties can also be viewed.
"""

import mysql.connector as mysql

import configparser
import logging.config
import datetime

# Logger
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logging.raiseExceptions = True  # Production mode if False (no console sys.stderr output)
logger = logging.getLogger('database')

# Read database.ini file
config = configparser.ConfigParser()
config.read("database.ini")

root_user = False  # Change to True if first time setup
if root_user:
    DB_USER = config.get('root', 'user')
    DB_PASS = config.get('root', 'password')

    bot_name = config.get('bot', 'user')
    bot_passwd = config.get('bot', 'password')
    DB_NAME = config.get('bot', 'database')
else:
    DB_USER = config.get('bot', 'user')
    DB_PASS = config.get('bot', 'password')
    DB_NAME = config.get('bot', 'database')

# Setup MySQL-compatible database
mysql_connection = mysql.connect(user=DB_USER, password=DB_PASS, database=DB_NAME)
cursor = mysql_connection.cursor()


def main():
    # Create the clashcaller database
    create_database(DB_NAME)

    # Select the clashcaller database
    cursor.execute(f'USE {DB_NAME};')

    # Show the tables
    print(get_tables(DB_NAME))

    # Create message table
    cmd = 'CREATE TABLE message_date (id INT UNSIGNED NOT NULL AUTO_INCREMENT, ' \
          'permalink VARCHAR(100), message VARCHAR(100), new_date DATETIME, ' \
          'userID VARCHAR(20), PRIMARY KEY(id));'
    create_table(DB_NAME, cmd)

    # Describe message table
    cursor.execute('DESCRIBE message_date;')
    print(cursor.fetchall())

    # Create comment list table
    cmd = 'CREATE TABLE comment_list (id MEDIUMINT NOT NULL AUTO_INCREMENT, list VARCHAR(35), ' \
          'PRIMARY KEY(id));'
    create_table(DB_NAME, cmd)

    # Describe comment list table
    cursor.execute('DESCRIBE comment_list;')
    print(cursor.fetchall())

    # Fetch list column from comment_list
    cursor.execute('SELECT list FROM comment_list;')
    print(cursor.fetchall())

    # Grant database bot permissions
    if root_user:
        try:
            cmd = f'GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER, ' \
                  f'CREATE TEMPORARY TABLES, LOCK TABLES ON {DB_NAME}.* TO \'{bot_name}\'@localhost ' \
                  f'IDENTIFIED BY \'{bot_passwd}\';'
            cursor.execute(cmd)
        except mysql.Error as err:
            logger.error(f'Grant bot permission err: {err}')


def create_database(db_name: str) -> bool:
    """Create database

    Function creates database with given database name.

    Args:
        db_name:    Name to give new database.

    Returns:
        True if successful, False otherwise.
    """
    try:
        cursor.execute(f'CREATE DATABASE {db_name};')
    except mysql.Error as err:
        logger.error(f'create_database: {err}')
        return False
    return True


def get_tables(db_name: str) -> list:
    """Return table list of given database.

    Function returns a list with the names of the tables.

    Args:
        db_name:    Database to get list of tables.

    Returns:
        table_names: List of table names.
    """
    table_names = []
    try:
        cursor.execute(f'USE {db_name}')
        cursor.execute('SHOW TABLES;')
        tables = cursor.fetchall()

        for table in tables:
            table_names.append(str(table[0]))
    except mysql.Error as err:
        logger.error(f'get_tables: {err}')
    return table_names


def create_table(db_name: str, specs: str) -> bool:
    """Create table in database.

    Function creates table in given database with given command.

    Args:
        db_name:    Database to make table in.
        specs:    Instructions containing table specifications.

    Example:
        ::
            specs = 'CREATE TABLE message_date (id INT UNSIGNED NOT NULL AUTO_INCREMENT, ' \
                    'permalink VARCHAR(100), message VARCHAR(100), new_date DATETIME, ' \
                    'userID VARCHAR(20), PRIMARY KEY(id));'
            db_name = database

            create_table(db_name, specs)

    Returns:
        True if successful, False otherwise.
    """
    try:
        cursor.execute(f'USE {db_name}')
        cursor.execute(specs)

    except mysql.Error as err:
        logger.error(f'create_table: {err}')
        return False
    return True


def drop_table(db_name: str, tbl_name: str) -> bool:
    """Drop table from database.

    Function drops given table from given database.

    Args:
        db_name:    Database to drop table from.
        tbl_name:   Table to drop.

    Returns:
        True if successful, False otherwise.
    """
    try:
        cursor.execute(f'USE {db_name};')
        cursor.execute(f'DROP TABLE IF EXISTS {tbl_name};')

        if tbl_name in get_tables(db_name):
            return False
    except mysql.Error as err:
        logger.error(f'drop_table: {err}')
        return False
    return True


def save_comment_data(link: str, msg: str, exp: datetime, uid: str) -> bool:
    """Saves given comment data into message_date table.

    Function uses given inputs to create a dictionary to quicksave
    data to the message_date table.

    Args:
        link:   Comment permalink.
        msg:    Comment message.
        exp:    Expiration datetime object.
        uid:    Comment author UserID.

    Returns:
        True for success, false otherwise.
    """
    try:
        add_comment = 'INSERT INTO message_date (permalink, message, new_date, userID) ' \
                      'VALUES (%(l)s, %(m)s, %(d)s, %(u)s)'
        comment_data = {
            'l': link,
            'm': msg,
            'd': exp,
            'u': uid
        }

        cursor.execute(add_comment, comment_data)
        mysql_connection.commit()
    except mysql.Error as err:
        logger.error(f'save_comment_data: {err}')
        return False
    return True


def save_comment_id(cid: str) -> bool:
    """Saves comment id into comment_list table.

    Function saves given comment id into the comment_list table.

    Args:
        cid:    Comment id to save.

    Returns:
        True for success, false otherwise.
    """
    try:
        add_comment_id = 'INSERT INTO comment_list (list) VALUES (%s)'

        cursor.execute(add_comment_id, cid)
        mysql_connection.commit()
    except mysql.Error as err:
        logger.error(f'save_comment_id: {err}')
        return False
    return True


def find_comment_id(cid: str) -> bool:
    """Check comment_list table for comment id.

    Function checks comment_list table for given comment id.

    Args:
        cid:    Comment id to search for.

    Returns:
        True for success, false otherwise.
    """
    try:
        query = 'SELECT list FROM comment_list;'

        cursor.execute(query)
        mysql_connection.commit()

        ids = cursor.fetchall()
        if cid not in ids:
            return False

    except mysql.Error as err:
        logger.error(f'find_comment_id: {err}')
        return False
    return True


# If run directly, instead of imported as a module, run main():
if __name__ == '__main__':
    main()
