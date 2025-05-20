BOT_TOKEN = "<your bot token>"

OPENAI_API_KEY = "<your openai API key>"

OPENAI_WHISPER_API_KEY = "<your openai whisper API key>"

SYSTEM_PROMPT = ('You are an evaluator. Please respond in Russian to each input with a strict format: "<Верно/Неверно> '
                 '|| <Comment>". Where "<Верно/Неверно>" is either "Верно" or "Неверно" based on the evaluation of '
                 'the input, "||" is a separator, and "<Comment>" is a large brief comment explaining the '
                 'evaluation, up to 3000 characters. Consider that the interviewee is a Junior Python Developer. '
                 'Provide motivation to Junior Python Developer. '
                 'Provide feedback that is suitable for a beginner, including suggestions for '
                 'improvement and basic explanations of any errors. The input is in Russian, but might contain '
                 'professional terminology in English - please, try to distinguish that accordingly.')

WHISPER_PROMPT = ('Jupyter, Anaconda, PostgreSQL, MySQL, SQLite, Redis, MongoDB, '
                  'GraphQL, Jenkins, TravisCI, CircleCI, GitLab, Bitbucket, Heroku, DigitalOcean, Netlify, Vercel, '
                  'Shell, PowerShell, CommandLine, CLI, IDE, VSCode, IntelliJ, DevOps, CI/CD, '
                  'UnitTesting, TDD, BDD, Cypress, Mocha, Jest, Chai, Jasmine, Webpack, Babel, ESLint, Prettier, '
                  'Flask, Django, TensorFlow, PyTorch, SciPy, Keras, OpenCV, ScikitLearn, FastAPI, Celery, '
                  'Docker, AWS, Azure, Lambda, Serverless, Terraform, Ansible, SOLID, DRY, KISS, '
                  'YAGNI, MVC, MVT, ORM, CRUD, JWT, OAuth, SSL, TLS, PEP8, PEP20, PyPI, Conda, Pipenv, Poetry')

DB_NAME = 'interview.db'
