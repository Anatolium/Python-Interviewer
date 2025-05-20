# PythonPro-Interviewer
PythonPro Interviewer is a bot-trainer that will help you prepare for an interview for a Python developer position. The bot asks Python-related questions and checks your answers, helping you sharpen your skills and get ready for real interviews.

PythonPro Interviewer — это Telegram-бот для подготовки к собеседованиям на позицию Python-разработчика. Бот задает вопросы по Python, проверяет текстовые и голосовые ответы с помощью OpenAI GPT-4o и Whisper API, помогая оттачивать навыки и готовиться к реальным интервью. Вопросы хранятся в базе данных SQLite и загружаются из CSV-файла.

## Ключевые технологии
- **Бэкенд:** Python 3.8+
- **Фронтенд:** pyTelegramBotAPI для взаимодействия с пользователем
- **База данных:** SQLite
- **API:** OpenAI GPT-4o (оценка ответов), OpenAI Whisper (распознавание голоса)
- **Обработка аудио:** FFmpeg

## Запуск бота
Для успешной работы бота необходимо создать файл в проекте config.py и указать переменные окружения, пример:
>BOT_TOKEN = '123:ABC123'
>OPENAI_API_KEY = 'sk-proj-12345'
>OPENAI_WHISPER_API_KEY = 'sk-proj-12345'
>SYSTEM_PROMPT = ('You are an evaluator. Please respond in Russian to each input with a strict format: "<Верно/Неверно> || <Comment>". Where "<Верно/Неверно>" is either "Верно" or "Неверно" based on the evaluation of the input, "||" is a separator, and "<Comment>" is a large brief comment explaining the evaluation, up to 3000 characters. Consider that the interviewee is a Junior Python Developer. Provide motivation to Junior Python Developer. ')
>WHISPER_PROMPT = ('Jupyter, Anaconda, PostgreSQL, MySQL, SQLite, Redis, MongoDB, GraphQL, Jenkins, TravisCI, CircleCI, GitLab, Bitbucket, Heroku, DigitalOcean, Netlify, Vercel, Shell, PowerShell, CommandLine, CLI, IDE, VSCode, IntelliJ, DevOps, CI/CD, UnitTesting, TDD, BDD, Cypress, Mocha, Jest, Chai, Jasmine, Webpack, Babel, ESLint, Prettier, Flask, Django, TensorFlow, PyTorch, SciPy, Keras, OpenCV, ScikitLearn, FastAPI, Celery, Docker, AWS, Azure, Lambda, Serverless, Terraform, Ansible, SOLID, DRY, KISS, YAGNI, MVC, MVT, ORM, CRUD, JWT, OAuth, SSL, TLS, PEP8, PEP20, PyPI, Conda, Pipenv, Poetry')
>DB_NAME = 'interview.db'

PythonPro-Interviewer/
├── main.py
├── backend.py
├── init_db.py
├── db_from_csv.py
├── config.py
├── PythonTest.csv
├── interview.db


## Инструкция разворачивания на сервере:
#### Обновление списка пакетов
>sudo apt update
#### Установка pip
>sudo apt install python3-pip
#### Установка virtualenv для Python 3.8
>sudo apt install python3.8-venv
#### Клонирование репозитория
>git clone https://github.com/serge-auro/PythonPro-Interviewer.git
#### Переход в директорию проекта
>cd PythonPro-Interviewer/
##### Создание виртуального окружения
>python3 -m venv .venv
##### Активация виртуального окружения
>source .venv/bin/activate
##### Создание файла конфигурации
##### (предполагается, что содержимое config.py у вас уже есть и вы его добавите самостоятельно)
##### Установка необходимых пакетов
>pip install --upgrade pip
>pip install pyTelegramBotAPI openai requests python-dotenv ffmpeg-python
##### Установка ffmpeg
>sudo apt install ffmpeg
##### Инициализация базы данных: запустите в репозитории
>python3 init_db.py
##### Загрузка вопросов: запустить в репозитории
>python3 db_from_csv.py
##### Убедитесь, что файл easyoffer.csv находится в корне проекта
##### Запуск бота
>python3 main.py


### License
This project is licensed under the [Apache-2.0 license](http://www.apache.org/licenses).