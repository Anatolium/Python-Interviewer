import sqlite3
import schedule
import time
from backend import get_notify
from datetime import datetime
from config import DB_NAME
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("PythonPro Interviewer notify is being started")

def notify_users():
    conn = sqlite3.connect(DB_NAME)
    try:
        cursor = conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        query = '''
            SELECT user_id, question_id
            FROM user_notify
            WHERE timedate <= ? AND active = 1
        '''
        cursor.execute(query, (current_time,))
        notifications = cursor.fetchall()
        for user_id, question_id in notifications:
            logging.info(f"Sending notification to user {user_id} for question {question_id}")
            get_notify(user_id)
            cursor.execute('''
                UPDATE user_notify
                SET active = 0
                WHERE user_id = ? AND question_id = ?
            ''', (user_id, question_id))
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
    finally:
        conn.close()

# Расписание: проверка каждую минуту
schedule.every(1).minutes.do(notify_users)

# Запуск в отдельном потоке
def run_notify():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    run_notify()
