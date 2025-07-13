# Технический аудит Telegram-бота TradeWise

## 1. Технологический стек
- **Библиотеки**:
  - `python-telegram-bot` (вероятно v20+, используется `telegram.ext.Application`)
  - `SQLAlchemy` (async, используется ORM)
  - `tinkoff.invest` (асинхронный клиент)
  - `pandas`, `numpy`, `matplotlib`, `tabulate` (аналитика, форматирование, графики)
  - `.env` через `python-dotenv`
- **СУБД**: SQLite (асинхронно через `sqlite+aiosqlite`)
- **ORM**: SQLAlchemy 2.x (async)
- **Асинхронность**: Весь проект построен на async/await
- **Веб-хуки/поллинг**: Используется polling (`app.run_polling()`)
- **Кэширование**: Не реализовано

## 2. Архитектурная карта
```
TradeWise/
├── main.py                # Точка входа, регистрация хендлеров
├── config.py              # Конфиги и переменные окружения
├── handlers/              # Telegram-команды
│   ├── common.py
│   ├── portfolio.py
│   ├── quotes.py
│   ├── backtest.py
│   └── strategy.py
├── db/                    # Модели и инициализация БД
│   ├── models.py
│   └── init_db.py
├── tinkoff_api/           # Интеграция с Tinkoff Invest API
│   ├── service.py
│   ├── accounts.py
│   ├── client.py
│   ├── instruments.py
│   ├── historical.py
│   ├── orders.py
│   └── utils.py
├── strategies/            # Торговые стратегии
│   ├── base.py
│   └── ma.py
├── utils/                 # Вспомогательные утилиты
│   ├── formatters.py
│   ├── decorators.py
│   └── mocks.py
```

- **Модульность**: handlers, utils, db, tinkoff_api, strategies — разделены корректно.
- **FSM**: Явной реализации конечных автоматов состояний нет (есть задел в `handlers/strategy.py`), хранилище состояний отсутствует.

## 3. Критические проблемы
1. **Нет хранения состояний FSM**  
   - `handlers/strategy.py:6`  
   - **Почему важно**: нельзя реализовать сложные сценарии взаимодействия с пользователем (опросы, пошаговые формы)
   - **Исправление**: Внедрить FSMContext из `python-telegram-bot` или стороннее хранилище (Redis, БД)
   - **Сложность**: medium

2. **Нет rate-limiting и защиты от спама**  
   - `main.py`, все handlers
   - **Почему важно**: возможен флуд, DDoS, блокировка Telegram API
   - **Исправление**: Добавить middleware/декоратор с лимитом частоты
   - **Сложность**: low

3. **Отсутствует централизованная обработка ошибок**  
   - `main.py`, все handlers
   - **Почему важно**: падение одного хендлера может привести к остановке polling
   - **Исправление**: Добавить глобальный error handler, логирование в Sentry/лог-файл
   - **Сложность**: low

4. **Нет валидации пользовательского ввода**  
   - `handlers/portfolio.py`, `handlers/quotes.py`, `handlers/backtest.py`
   - **Почему важно**: возможны ошибки при некорректных параметрах
   - **Исправление**: Добавить парсинг и валидацию аргументов
   - **Сложность**: low

5. **Потенциальные блокирующие вызовы**  
   - `handlers/backtest.py:8-15` (matplotlib)
   - **Почему важно**: matplotlib не async, может блокировать event loop
   - **Исправление**: Использовать offload в thread pool
   - **Сложность**: medium

6. **Нет тестов и CI/CD**  
   - В проекте отсутствуют тесты и пайплайны
   - **Почему важно**: сложно гарантировать стабильность при доработках
   - **Исправление**: Добавить pytest, GitHub Actions
   - **Сложность**: medium

## 4. Позитивные практики
- `db/models.py`: Чистые async-модели SQLAlchemy, нормализованная структура
- `utils/formatters.py`: Универсальный форматтер портфеля через tabulate
- `tinkoff_api/client.py`: Абстракция над Tinkoff Invest API, легко расширять
- `strategies/base.py` и `ma.py`: Расширяемая архитектура для стратегий
- `utils/decorators.py`, `tinkoff_api/utils.py`: Декораторы для авторизации

## 5. Рекомендации по развитию
### Оптимизация и масштабирование
- Перейти на webhooks для продакшн (меньше нагрузки, быстрее реакции)
- Внедрить Redis для FSM и rate-limiting
- Добавить кэширование инструментов и портфеля (Redis, in-memory)
- Вынести тяжелые вычисления (бэктесты) в Celery/очереди

### Технический долг (приоритет: high → low)
1. FSM и хранение состояний (high)
2. Rate-limiting и антифлуд (high)
3. Централизованный error handler (high)
4. Асинхронный offload для matplotlib (medium)
5. Валидация пользовательского ввода (medium)
6. Тесты и CI/CD (medium)
7. Кэширование и оптимизация N+1 (low)

### Roadmap новых фич
- FSM для сложных сценариев (опросы, wizard)
- Webhook-режим для продакшн
- Микросервисная интеграция (выделить сервисы для стратегий, бэктестов)
- Мониторинг (Sentry, Prometheus)
- Админ-панель для управления пользователями и логами

## 6. Сниппеты для рефакторинга
### FSM (python-telegram-bot)
```python
from telegram.ext import ConversationHandler

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('strategy', strategy_start)],
    states={
        CHOOSING: [MessageHandler(filters.TEXT, choose_strategy)],
        CONFIGURING: [MessageHandler(filters.TEXT, configure_strategy)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
app.add_handler(conv_handler)
```

### Rate-limiting декоратор
```python
import time
from functools import wraps
RATE_LIMIT = {}

def rate_limit(seconds=2):
    def decorator(func):
        @wraps(func)
        async def wrapper(update, context, *args, **kwargs):
            user_id = update.effective_user.id
            now = time.time()
            if user_id in RATE_LIMIT and now - RATE_LIMIT[user_id] < seconds:
                await update.message.reply_text('Слишком часто!')
                return
            RATE_LIMIT[user_id] = now
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator
```

### Асинхронный offload matplotlib
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

def plot_equity_curve(results):
    import matplotlib.pyplot as plt
    import io
    fig, ax = plt.subplots()
    ax.plot(results['equity_curve'])
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return buf

async def backtest(update, context):
    ...
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        buf = await loop.run_in_executor(pool, plot_equity_curve, results)
    await update.message.reply_photo(buf, caption="Результаты бэктеста")
```

---

## Логирование
- Все ключевые действия пользователя логируются как в консоль (терминал), так и в базу данных (таблица `action_logs`).
- Для логирования используется утилита `utils/logger.py`.
- Пример логируемых событий: запуск бота, запрос портфеля, котировок, бэктеста, стратегий.

---

**Аудит проведён: 2024-06-08.**
Senior Python Developer

---

## Внесённые изменения (2024-06-08)

1. **SQL-инъекции**
   - В проекте используется SQLAlchemy ORM и асинхронные сессии, что защищает от SQL-инъекций. Прямых небезопасных SQL-запросов не обнаружено.

2. **Rate-limiting**
   - Добавлен декоратор `@rate_limit()` (см. `utils/rate_limit.py`).
   - Декоратор применён ко всем основным хендлерам (`handlers/common.py`, `handlers/portfolio.py`, `handlers/quotes.py`, `handlers/backtest.py`, `handlers/strategy.py`).
   - Теперь каждый пользователь может вызывать команды не чаще, чем раз в 0.5 секунды.

3. **Миграция на RedisStorage**
   - Добавлен модуль `utils/redis_storage.py` с примером асинхронного хранения пользовательских данных в Redis.
   - В `requirements.txt` добавлен пакет `aioredis`.
   - Для полноценной FSM-интеграции потребуется доработка логики состояний.

---

## Архитектура
- Фреймворк: python-telegram-bot v20.7
- Хранилище состояний: Redis через кастомный Persistence (utils/ptb_persistence.py)

## Зависимости
- Требуется установленный Redis server 6.2+
- Python-библиотеки: `redis>=4.5.0`

---
