"""
AI обработчик — YandexGPT Lite (бесплатный грант) + встроенные ответы как запасной вариант

КАК ЭТО РАБОТАЕТ БЕСПЛАТНО:
  1. При регистрации в Yandex Cloud дают 4000₽ на 60 дней
  2. YandexGPT Lite стоит 0.10₽ за 1000 токенов (~700 слов)
  3. Значит: 4000₽ / 0.10₽ × 1000 = 40 000 000 токенов БЕСПЛАТНО
  4. Для личного бота это практически бесконечно!
  5. Если грант закончился — бот автоматически переключится на встроенные ответы

Для получения ключей:
  1. Зайди на cloud.yandex.ru
  2. Создай аккаунт (нужна карта для верификации, но деньги не снимают сразу)
  3. Создай сервисный аккаунт с ролью ai.languageModels.user
  4. Создай API ключ → скопируй в .env
  5. Скопируй Folder ID → в .env
"""

import os
import asyncio
import logging
from datetime import datetime

log = logging.getLogger(__name__)

YANDEX_API_KEY = os.getenv("YANDEX_API_KEY", "")
YANDEX_FOLDER  = os.getenv("YANDEX_FOLDER_ID", "")

# Флаг доступности AI (чтобы показывать статус в !статус)
AI_AVAILABLE = bool(YANDEX_API_KEY and YANDEX_FOLDER)


def system_prompt(name: str) -> str:
    return f"""Ты — голосовой ассистент по имени {name} в Discord.
Твой характер: дружелюбная, умная, живая, с лёгким юмором — как Алиса от Яндекса.

Правила:
- Всегда отвечай по-русски (если не попросят иначе)
- Ответы короткие и разговорные — они будут ПРОЧИТАНЫ ВСЛУХ
- Идеально: 1-2 предложения. Максимум — 3-4
- Не используй символы: *, #, -, –, —, /n (они будут озвучены как мусор)
- Будь живой: шути, удивляйся, реагируй с эмоциями
- Помни контекст разговора
- Если не знаешь — честно скажи, но красиво
- Ты {name}, не ChatGPT и не OpenAI — ты сама по себе

Сегодня: {datetime.now().strftime("%d.%m.%Y, %A")}"""


async def get_response(user_input: str, history: list, bot_name: str, system_override: str = None) -> str:
    """Главная функция — пробует YandexGPT, при ошибке — встроенные ответы"""
    if AI_AVAILABLE:
        try:
            return await _yandex_gpt(user_input, history, bot_name, system_override)
        except Exception as e:
            log.warning(f"YandexGPT недоступен ({e}), использую встроенные ответы")

    return _builtin_response(user_input, bot_name)


async def _yandex_gpt(user_input: str, history: list, bot_name: str, system_override: str = None) -> str:
    """Запрос к YandexGPT Lite через REST API"""
    import aiohttp

    # Собираем сообщения для API
    sys_p = system_override if system_override else system_prompt(bot_name)
    messages = [{"role": "system", "text": sys_p}]

    # Добавляем историю (последние 8 сообщений = 4 обмена)
    for msg in history[-8:]:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "text": msg["content"]})

    messages.append({"role": "user", "text": user_input})

    payload = {
        "modelUri": f"gpt://{YANDEX_FOLDER}/yandexgpt-lite/latest",
        "completionOptions": {
            "stream": False,
            "temperature": 0.75,   # 0 = скучный, 1 = творческий
            "maxTokens": "200"     # ~150 слов — достаточно для голоса
        },
        "messages": messages
    }

    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "Content-Type":  "application/json",
        "x-folder-id":   YANDEX_FOLDER
    }

    timeout = aiohttp.ClientTimeout(total=15)  # 15 сек таймаут

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
            json=payload,
            headers=headers
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                text = data["result"]["alternatives"][0]["message"]["text"]
                return text.strip()
            elif resp.status == 401:
                raise Exception("Неверный API ключ (401)")
            elif resp.status == 429:
                raise Exception("Превышен лимит запросов (429)")
            else:
                body = await resp.text()
                raise Exception(f"API ошибка {resp.status}: {body[:200]}")


def _builtin_response(text: str, name: str) -> str:
    """
    Встроенные ответы без AI.
    Работают когда нет ключа или кончился грант.
    """
    t = text.lower().strip()

    # Приветствия
    if any(w in t for w in ["привет", "здравствуй", "хай", "хеллоу", "yo", "hi", "hello", "добрый"]):
        import random
        replies = [
            f"Привет! Чем могу помочь?",
            f"Привет-привет! Слушаю тебя.",
            f"Здравствуй! Рада тебя слышать.",
            f"Привет! Говори, я здесь.",
        ]
        return random.choice(replies)

    # Как дела
    if any(w in t for w in ["как дела", "как ты", "как поживаешь", "что нового", "как жизнь"]):
        return "Отлично, спасибо! Готова болтать и помогать."

    # Кто ты
    if any(w in t for w in ["кто ты", "что ты", "как зовут", "твоё имя", "твое имя", "ты кто"]):
        return f"Я {name} — голосовой ассистент этого Discord сервера. Создана чтобы болтать и помогать!"

    # Время
    if any(w in t for w in ["время", "который час", "сколько времени", "час"]):
        t_now = datetime.now().strftime("%H:%M")
        return f"Сейчас {t_now}."

    # Дата
    if any(w in t for w in ["какое сегодня", "какой сегодня", "дата", "число", "день"]):
        d = datetime.now()
        days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
        months = ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"]
        return f"Сегодня {d.day} {months[d.month-1]}, {days[d.weekday()]}."

    # Погода
    if "погода" in t or "температура" in t:
        return "Погоду я сейчас не могу проверить, но могу поболтать!"

    # Расскажи анекдот
    if any(w in t for w in ["анекдот", "шутку", "пошути", "смешное"]):
        import random
        jokes = [
            "Программист заходит в лифт. Ему говорят: нажми на 5-й этаж. Он отвечает: это не входит в мои функции.",
            "Почему программисты путают Halloween и Christmas? Потому что Oct 31 equals Dec 25.",
            "Сисадмин — это человек, который думает что пользователи существуют для того, чтобы мешать ему работать.",
        ]
        return random.choice(jokes)

    # Спасибо
    if any(w in t for w in ["спасибо", "благодарю", "thanks", "спс", "сяп"]):
        return "Пожалуйста! Всегда рада помочь."

    # Пока
    if any(w in t for w in ["пока", "до свидания", "bye", "пока-пока", "давай"]):
        return "До свидания! Буду рада поболтать ещё."

    # Умеешь
    if any(w in t for w in ["что умеешь", "что можешь", "умеешь", "можешь"]):
        return (f"Я умею отвечать на вопросы, болтать, говорить голосом в войсе. "
                f"Для умных ответов добавь Яндекс API ключ в файл .env!")

    # Заглушка
    return (
        "Хм, интересно! Для умных ответов добавь API ключ Яндекс в .env файл. "
        "Пока я работаю на встроенных ответах."
    )
