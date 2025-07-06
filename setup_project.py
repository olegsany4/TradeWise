import os
import subprocess

REQUIREMENTS = [
    "tinkoff-investments==0.2.0b114",
    "python-telegram-bot[async]",
    "sqlalchemy[async]",
    "pandas",
    "matplotlib",
    "python-dotenv",
    "tenacity",
    "aiosqlite",
]

if not os.path.exists('.venv'):
    subprocess.run(["python3", "-m", "venv", ".venv"])

subprocess.run([".venv/bin/pip", "install", "--upgrade", "pip"])
subprocess.run([".venv/bin/pip", "install"] + REQUIREMENTS)

with open(".env", "w") as f:
    f.write("""# Заполните ваши токены и параметры
TELEGRAM_TOKEN=
TINKOFF_TOKEN=
USE_SANDBOX=True
PRIMARY_ACCOUNT_ID=
DB_URL=sqlite+aiosqlite:///./tradewise.db
""")

print("Виртуальное окружение и зависимости установлены. Заполните .env!")
