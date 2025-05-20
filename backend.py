import sqlite3
from datetime import datetime, timedelta
import requests
import io
from config import BOT_TOKEN, OPENAI_API_KEY, SYSTEM_PROMPT, OPENAI_WHISPER_API_KEY, WHISPER_PROMPT, DB_NAME
from openai import OpenAI
import random
import ffmpeg
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TYPE = ("text", "audio", "empty")
client = OpenAI(api_key=OPENAI_WHISPER_API_KEY)


def initialize_database():
    from init_db import init_db
    init_db()
    logging.info("Database initialized successfully")


def init_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO user (id, active) VALUES (?, ?)", (user_id, 1))
    conn.commit()
    conn.close()
    logging.info(f"User {user_id} initialized successfully")
    return user_id


def get_report(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    query = '''
        SELECT 
            COUNT(*) AS total_questions,
            SUM(CASE WHEN correct = 1 THEN 1 ELSE 0 END) AS correct_answers,
            SUM(CASE WHEN correct = 0 THEN 1 ELSE 0 END) AS incorrect_answers
        FROM user_stat
        WHERE user_id = ?
    '''
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    total_questions, correct_answers, incorrect_answers = result
    if total_questions == 0:
        report = "Количество заданных вопросов: 0\nПравильных ответов: 0%\nНеправильных: 0%"
    else:
        correct_percentage = round((correct_answers / total_questions) * 100)
        incorrect_percentage = 100 - correct_percentage
        report = (f"Количество заданных вопросов: {total_questions}\n"
                  f"Правильных ответов: {correct_percentage}%\n"
                  f"Неправильных: {incorrect_percentage}%")
    conn.close()
    return report


def get_question(user_id):
    try:
        questions = get_unresolved_questions(user_id)
        if not questions:
            questions = get_all_active_questions()
        if not questions:
            return "Все вопросы были уже правильно отвечены или нет доступных активных вопросов."
        total_weights = sum(rate for _, _, rate in questions)
        question_id, question_text, _ = random.choices(questions, weights=[rate for _, _, rate in questions], k=1)[0]
        question = {"id": question_id, "name": question_text}
        logging.info(f"{user_id} - {question_id}: {question_text}")
        set_timer(user_id, question_id)
        return question
    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
        return "Произошла ошибка при работе с базой данных. Пожалуйста, попробуйте позже."


def process_answer(user_id, data, type: TYPE):
    if not isinstance(user_id, int) or user_id <= 0:
        return "Ошибка", "Некорректный идентификатор пользователя."
    if type not in TYPE:
        return "Ошибка", "Некорректный тип ответа."
    try:
        result = get_active_question(user_id)
        if not result:
            logging.warning(f"No active question found for user {user_id}")
            return "Ошибка", "Активный вопрос не найден."
        question_id, question_text = result
        logging.info(f"Processing answer for user {user_id}, question {question_id}: {question_text}")
        if type == "audio":
            user_answer = data  # Данные уже распознаны как текст
            if not user_answer:
                return "Ошибка", "Распознанный текст пуст."
        elif type == "empty":
            user_answer = "я не знаю"
        else:
            user_answer = data
        logging.info(f"process_answer->gpt : {user_answer}")
        user_response = ask_chatgpt((question_text, user_answer))
        if user_response['result'] not in ["Верно", "Неверно"]:
            return "Ошибка", "Некорректный формат ответа от ChatGPT."
        correct = user_response['result'] == "Верно"
        update_user_stat(user_id, question_id, correct)
        skip_question(user_id)
        return user_response['result'], user_response['comment']
    except sqlite3.Error as e:
        logging.error(f"SQLite error for user {user_id}: {str(e)}")
        return "Ошибка", f"Ошибка при сохранении вашего ответа: {str(e)}"
    except Exception as e:
        logging.error(f"Unexpected error for user {user_id}: {str(e)}")
        return "Ошибка", f"Неизвестная ошибка: {str(e)}"


def ask_chatgpt(question_pack: tuple):
    user_question, user_answer = question_pack
    ask_content = f"Question: {user_question}\nAnswer: {user_answer}"
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": ask_content}
        ]
    )
    gpt_answer_content = completion.choices[0].message.content
    result, comment = gpt_answer_content.split(' || ')
    return {"result": result.strip(), "comment": comment.strip()}


def download_audio_file(file_id, bot_token=BOT_TOKEN):
    file_url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
    response = requests.get(file_url)
    if response.status_code != 200:
        logging.error(f"Failed to get file info: {response.status_code}")
        return None
    file_path = response.json().get('result', {}).get('file_path')
    if not file_path:
        logging.error("Failed to get file path.")
        return None
    download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
    audio_response = requests.get(download_url)
    if audio_response.status_code != 200:
        logging.error(f"Failed to download file: {audio_response.text}")
        return None
    voice_file = f"voice_{file_id}.ogg"
    with open(voice_file, 'wb') as f:
        f.write(audio_response.content)
    logging.info(f"File downloaded successfully and saved as {voice_file}")
    return voice_file


def convert_audio_to_wav(ogg_file_path):
    if not os.path.exists(ogg_file_path):
        logging.error(f"Input file does not exist: {ogg_file_path}")
        return None
    wav_data = io.BytesIO()
    try:
        # Проверяем формат входного файла
        probe = ffmpeg.probe(ogg_file_path)
        logging.info(f"Input file probe: {probe}")
        if 'streams' not in probe or not probe['streams']:
            logging.error("No audio streams found in input file")
            return None
        # Конвертация с явным указанием кодеков
        stream = ffmpeg.input(ogg_file_path)
        stream = ffmpeg.output(stream, 'pipe:', format='wav', acodec='pcm_s16le', ar=16000, loglevel='error')
        stream = ffmpeg.overwrite_output(stream)
        process = ffmpeg.run_async(stream, pipe_stdout=True, pipe_stderr=True)
        output, error = process.communicate()
        if process.returncode != 0:
            logging.error(f"FFmpeg conversion failed: {error.decode()}")
            return None
        wav_data.write(output)
        wav_data.seek(0)
        # Проверяем, что данные не пусты
        if wav_data.getbuffer().nbytes == 0:
            logging.error("FFmpeg produced empty output")
            return None
        return wav_data
    except ffmpeg.Error as e:
        logging.error(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error in convert_audio_to_wav: {str(e)}")
        return None


def audio_to_text(file_path):
    try:
        if not os.path.exists(file_path):
            logging.error(f"Audio file does not exist: {file_path}")
            return None
        logging.info(f"Starting audio transcription for file: {file_path}")
        wav_data = convert_audio_to_wav(file_path)
        if not wav_data:
            logging.error("Failed to convert audio to WAV format")
            return None
        # Проверяем, что wav_data - это BytesIO с данными
        if not isinstance(wav_data, io.BytesIO) or wav_data.getbuffer().nbytes == 0:
            logging.error("Invalid WAV data")
            return None
        # Whisper API ожидает файлоподобный объект с именем
        wav_data.name = "audio.wav"
        response = client.audio.transcriptions.create(
            file=wav_data,
            model="whisper-1",
            prompt=WHISPER_PROMPT,
            language="ru"
        )
        logging.info(f"Transcription response: {response.text}")
        return response.text
    except Exception as e:
        logging.error(f"Error during transcription: {str(e)}")
        return None
    finally:
        # Удаляем файл только после успешной обработки
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logging.info(f"Temporary file removed: {file_path}")
        except Exception as e:
            logging.error(f"Failed to remove temporary file {file_path}: {str(e)}")


def get_notify(user_id):
    logging.info(f"Processing timeout for user {user_id}")
    result = get_active_question(user_id)
    if result:
        question_id, question_text = result
        process_answer(user_id, "я не знаю", "empty")
        skip_question(user_id)
    else:
        logging.warning(f"No active question for timeout for user {user_id}")


def set_timer(user_id, question_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    current_datetime = datetime.now() + timedelta(minutes=2)
    timedate = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("INSERT OR REPLACE INTO user_notify (user_id, question_id, timedate, active) VALUES (?, ?, ?, ?)",
                   (user_id, question_id, timedate, 1))
    conn.commit()
    conn.close()
    logging.info(f"Timer set for user {user_id}, question {question_id}")


def skip_timer(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    query = '''
        UPDATE user_notify
        SET active = 0
        WHERE user_id = ? AND active = 1
    '''
    cursor.execute(query, (user_id,))
    conn.commit()
    conn.close()
    logging.info(f"Timer skipped for user {user_id}")


def get_unresolved_questions(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    query = '''
        SELECT q.id, q.name, q.rate
        FROM question q
        LEFT JOIN user_stat us ON q.id = us.question_id AND us.user_id = ? AND us.correct = 1
        WHERE us.question_id IS NULL AND q.active = 1
    '''
    cursor.execute(query, (user_id,))
    questions = cursor.fetchall()
    conn.close()
    return questions


def get_all_active_questions():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, rate FROM question WHERE active = 1')
    questions = cursor.fetchall()
    conn.close()
    return questions


def get_active_question(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    query = '''
        SELECT qq.id, qq.name
        FROM user_notify as un, question as qq
        WHERE un.question_id = qq.id
          AND qq.active = 1
          AND un.active = 1
          AND un.user_id = ? LIMIT 1
    '''
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result


def update_user_stat(user_id, question_id, correct):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO user_stat (user_id, question_id, correct, timestamp) VALUES (?, ?, ?, ?)",
        (user_id, question_id, correct, datetime.now()))
    conn.commit()
    conn.close()


def clear_user_stat(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_stat WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def skip_question(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE user_notify SET active = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    logging.info(f"Question skipped for user {user_id}")
