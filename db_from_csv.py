import sqlite3
import csv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

csv_file_path = 'PythonTest.csv'
sqlite_db_path = 'interview.db'
table_name = 'question'

def db_from_csv():
    conn = sqlite3.connect(sqlite_db_path)
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM {table_name}')  # Очистка таблицы
    with open(csv_file_path, 'r', newline='', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)  # Пропуск заголовка
        for row in csv_reader:
            rate, name, theme = row
            cursor.execute('''
                INSERT INTO question (name, theme, active, rate)
                VALUES (?, ?, ?, ?)
            ''', (name, theme, 1, int(rate)))
    conn.commit()
    conn.close()
    logging.info("Questions loaded from CSV successfully")

def view_tables(name_table):
    conn = sqlite3.connect(sqlite_db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {name_table} LIMIT 5")
    rows = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]
    logging.info(f"Table {name_table} columns: {column_names}")
    for row in rows:
        logging.info(row)
    conn.close()
