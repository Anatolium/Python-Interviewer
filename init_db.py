import sqlite3
import logging
from config import BOT_TOKEN, DB_NAME

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    create_user_table = '''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY,
            active BOOLEAN DEFAULT 1,
            date_created DATE DEFAULT CURRENT_DATE,
            user_lvl TEXT DEFAULT 'junior',
            user_minute INTEGER DEFAULT 2,
            UNIQUE(id)
        )
    '''
    create_question_table = '''
        CREATE TABLE IF NOT EXISTS question (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            active BOOLEAN DEFAULT 1,
            theme TEXT,
            rate INTEGER,
            UNIQUE(id)
        )
    '''
    create_user_stat_table = '''
        CREATE TABLE IF NOT EXISTS user_stat (
            user_id INTEGER,
            question_id INTEGER,
            correct BOOLEAN,
            timestamp DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (question_id) REFERENCES question (id),
            UNIQUE(user_id, question_id)
        )
    '''
    create_user_notify_table = '''
        CREATE TABLE IF NOT EXISTS user_notify (
            user_id INTEGER,
            question_id INTEGER,
            timedate TEXT,
            active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES user (id),
            UNIQUE(user_id, question_id)
        )
    '''

    cursor.execute(create_user_table)
    cursor.execute(create_question_table)
    cursor.execute(create_user_stat_table)
    cursor.execute(create_user_notify_table)

    conn.commit()
    conn.close()
    logging.info("Database tables created successfully")
