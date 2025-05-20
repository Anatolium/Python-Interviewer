import telebot
import os
import threading
import time
from config import BOT_TOKEN, DB_NAME
import logging
from telebot import types
from backend import (
    init_user as backend_init_user,
    get_report as backend_get_report,
    skip_timer as backend_skip_timer,
    get_question as backend_get_question,
    process_answer as backend_process_answer,
    update_user_stat,
    clear_user_stat as be_clear_user_stat,
    get_notify,
    initialize_database,
    audio_to_text
)

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

bot = telebot.TeleBot(BOT_TOKEN)
user_states = {}
logging.info("PythonPro Interviewer is being started")

# Декоратор - Обработчик ошибок
def error_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error in {func.__name__}: {str(e)}")
            if args and args[0] and hasattr(args[0], 'chat'):
                bot.send_message(args[0].chat.id, "Произошла ошибка. Пожалуйста, попробуйте снова.")
                show_menu(args[0].chat.id)
        return
    return wrapper

# Обработчик команды /start
@bot.message_handler(commands=['start'])
@error_handler
def handle_start(message):
    user_id = message.from_user.id
    logging.info(f"Received /start command from user {user_id}")
    backend_init_user(user_id)
    bot.send_message(user_id, "Приветствую! Я ваш бот-интервьюер по Python")
    show_menu(user_id)

# Функция для отображения основного меню
def show_menu(user_id):
    logging.info(f"Showing menu for user {user_id}")
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button_start_interview = types.KeyboardButton("🚀 Начать интервью")
    button_request_report = types.KeyboardButton("📊 Запросить отчет")
    button_reset_result = types.KeyboardButton("🔄 Обнулить результат")
    button_description = types.KeyboardButton("ℹ️ Описание бота")
    markup.add(button_start_interview, button_request_report, button_reset_result, button_description)
    bot.send_message(user_id, "Выберите действие:", reply_markup=markup)
    logging.info(f"Menu sent to user {user_id}")

# Функция для начала интервью
@error_handler
def start_interview(user_id):
    logging.info(f"Starting interview for user {user_id}")
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button_skip = types.KeyboardButton("⛔️ Пропустить вопрос")
    button_end_interview = types.KeyboardButton("🏁 Завершить интервью")
    markup.add(button_skip, button_end_interview)

    question = backend_get_question(user_id)
    if isinstance(question, dict) and "name" in question and "id" in question:
        user_states[user_id] = ("waiting_for_answer", question)
        bot.send_message(user_id, question["name"], reply_markup=markup)
        logging.info(f"Question sent to user {user_id}: {question['name']}")
    else:
        bot.send_message(user_id, "Все вопросы пройдены! Хотите начать заново?", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(types.KeyboardButton("🔄 Начать заново")))
        logging.info(f"No questions available for user {user_id}: {question}")
        user_states[user_id] = ("waiting_for_restart", None)

# Функция для обработки ответов
@error_handler
def handle_answer(message):
    user_id = message.from_user.id
    user_state = user_states.get(user_id)
    logging.info(f"Handling answer from user {user_id}")

    if user_state and user_state[0] == "waiting_for_answer":
        question = user_state[1]
        if message.content_type == 'text':
            user_response = message.text
            response_type = "text"
            logging.info(f"Received text answer from user {user_id}: {user_response}")
        elif message.content_type == 'voice':
            try:
                # Получаем информацию о файле
                logging.info(f"Fetching file info for voice message from user {user_id}")
                file_info = bot.get_file(message.voice.file_id)
                if not file_info or not hasattr(file_info, 'file_path'):
                    logging.error(f"Failed to get file info for voice message from user {user_id}")
                    bot.send_message(user_id, "Ошибка при получении аудиофайла. Попробуйте снова.")
                    return
                # Загружаем файл
                logging.info(f"Downloading voice file: {file_info.file_path}")
                file = bot.download_file(file_info.file_path)
                if not file:
                    logging.error(f"Failed to download voice file for user {user_id}")
                    bot.send_message(user_id, "Ошибка при загрузке аудиофайла. Попробуйте снова.")
                    return
                # Сохраняем файл
                audio_path = f"temp_{user_id}.ogg"
                # Удаляем старый файл, если он существует
                if os.path.exists(audio_path):
                    try:
                        os.remove(audio_path)
                        logging.info(f"Removed old temporary file: {audio_path}")
                    except Exception as e:
                        logging.error(f"Failed to remove old temporary file {audio_path}: {str(e)}")
                logging.info(f"Saving voice file to: {audio_path}")
                with open(audio_path, "wb") as f:
                    f.write(file)
                # Проверяем, что файл создан
                if not os.path.exists(audio_path):
                    logging.error(f"Audio file was not created: {audio_path}")
                    bot.send_message(user_id, "Ошибка при сохранении аудиофайла. Попробуйте снова.")
                    return
                bot.send_message(user_id, "Распознаю аудио, ожидайте...")
                user_response = audio_to_text(audio_path)
                response_type = "text"  # Изменено: распознанный текст передается как текст
                if user_response is None:
                    logging.error(f"Failed to transcribe audio for user {user_id}")
                    bot.send_message(user_id, "Не удалось распознать аудио. Попробуйте снова.")
                    return
                logging.info(f"Transcribed audio for user {user_id}: {user_response}")
            except Exception as e:
                logging.error(f"Error processing voice for user {user_id}: {str(e)}")
                bot.send_message(user_id, f"Ошибка при обработке аудио: {str(e)}")
                # Очистка временного файла при ошибке
                if 'audio_path' in locals() and os.path.exists(audio_path):
                    try:
                        os.remove(audio_path)
                        logging.info(f"Cleaned up temporary file: {audio_path}")
                    except Exception as e:
                        logging.error(f"Failed to clean up temporary file {audio_path}: {str(e)}")
                return
        else:
            bot.send_message(user_id, "Отправьте текст или голосовое сообщение.")
            return

        bot.send_message(user_id, "Ваш ответ принят. Ожидайте проверку...")
        try:
            result, comment = backend_process_answer(user_id, user_response, response_type)
            bot.send_message(user_id, result)
            bot.send_message(user_id, comment)
            update_user_stat(user_id, question['id'], 1 if result.lower() == "верно" else 0)
            user_states[user_id] = ("menu", None)
        except Exception as e:
            logging.error(f"Error processing answer for user {user_id}: {str(e)}")
            bot.send_message(user_id, "Ошибка при обработке ответа. Попробуйте снова.")

        start_interview(user_id)
    elif user_state and user_state[0] == "waiting_for_restart":
        if message.text == "🔄 Начать заново":
            restart_interview(user_id)
    else:
        bot.send_message(user_id, "Выберите действие из меню.")

# Функция для пропуска вопроса
@error_handler
def skip_question(user_id):
    logging.info(f"Skipping question for user {user_id}")
    backend_skip_timer(user_id)
    user_states[user_id] = ("menu", None)
    start_interview(user_id)

# Функция для завершения интервью
@error_handler
def end_interview(user_id):
    logging.info(f"Ending interview for user {user_id}")
    backend_skip_timer(user_id)
    user_states[user_id] = ("menu", None)
    show_menu(user_id)

# Функция для перезапуска интервью
@error_handler
def restart_interview(user_id):
    logging.info(f"Restarting interview for user {user_id}")
    be_clear_user_stat(user_id)
    start_interview(user_id)

# Функция для очистки статистики
@error_handler
def clear_user_stat(user_id):
    be_clear_user_stat(user_id)
    bot.send_message(user_id, "Ваш результат был обнулен.")
    show_menu(user_id)

# Словарь для обработки текстовых сообщений
commands = {
    "🚀 Начать интервью": lambda message: start_interview(message.from_user.id),
    "📊 Запросить отчет": lambda message: bot.send_message(message.from_user.id, backend_get_report(message.from_user.id)),
    "🔄 Обнулить результат": lambda message: clear_user_stat(message.from_user.id),
    "ℹ️ Описание бота": lambda message: bot.send_message(message.from_user.id, "Я - ваш бот, предназначенный для тренировки навыков интервью по Python."),
    "⛔️ Пропустить вопрос": lambda message: skip_question(message.from_user.id),
    "🏁 Завершить интервью": lambda message: end_interview(message.from_user.id),
    "🔄 Начать заново": lambda message: restart_interview(message.from_user.id)
}

# Обработчик текстовых и голосовых сообщений
@bot.message_handler(content_types=['text', 'voice'])
@error_handler
def handle_text_and_voice(message):
    user_id = message.from_user.id
    logging.info(f"Received message from user {user_id}: {message.text if message.content_type == 'text' else 'voice'}")
    if message.content_type == 'text' and message.text in commands:
        commands[message.text](message)
    elif user_states.get(user_id) and user_states[user_id][0] in ["waiting_for_answer", "waiting_for_restart"]:
        handle_answer(message)
    else:
        bot.send_message(user_id, "Пожалуйста, выберите действие из меню.")

# Таймер для проверки уведомлений
def check_timers():
    import sqlite3
    from datetime import datetime
    while True:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            SELECT user_id, question_id
            FROM user_notify
            WHERE timedate <= ? AND active = 1
        ''', (current_time,))
        notifications = cursor.fetchall()
        for user_id, question_id in notifications:
            logging.info(f"Timer expired for user {user_id}, question {question_id}")
            if user_states.get(user_id, [None])[0] == "waiting_for_answer":
                bot.send_message(user_id, "Время вышло.")
                get_notify(user_id)
                user_states[user_id] = ("menu", None)
                start_interview(user_id)
        conn.close()
        time.sleep(60)

# Инициализация базы данных и загрузка вопросов
initialize_database()
from db_from_csv import db_from_csv
db_from_csv()

# Запуск таймера в отдельном потоке
timer_thread = threading.Thread(target=check_timers, daemon=True)
timer_thread.start()

# Основной цикл
while True:
    try:
        logging.info("Starting bot polling")
        bot.polling(none_stop=True)
    except Exception as e:
        logging.error(f"Polling error: {str(e)}")
        time.sleep(1)
