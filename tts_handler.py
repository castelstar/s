"""
TTS — синтез речи через edge-tts (БЕСПЛАТНО, без ключей)

Что такое edge-tts:
  Microsoft Edge использует нейросетевой TTS когда читает страницы вслух.
  Библиотека edge-tts обращается к этому же API.
  Это АБСОЛЮТНО БЕСПЛАТНО и без регистрации.

Голоса для русского языка:
  - ru-RU-SvetlanaNeural  — женский, спокойный (по умолчанию, похож на Алису!)
  - ru-RU-DariyaNeural    — женский, мягкий
  - ru-RU-DmitryNeural    — мужской

Если edge-tts не работает — используем gTTS (Google TTS, тоже бесплатно).
"""

import os
import asyncio
import tempfile
import logging
from pathlib import Path

log = logging.getLogger(__name__)

# Голос бота
VOICE = os.getenv("TTS_VOICE", "ru-RU-SvetlanaNeural")

# Папка для временных файлов
TMP = Path(tempfile.gettempdir()) / "alisa_tts"
TMP.mkdir(exist_ok=True)


async def synth(text: str) -> str | None:
    """
    Синтезировать текст в аудио файл.
    Возвращает путь к MP3 файлу или None при ошибке.
    """
    if not text or not text.strip():
        return None

    # Чистим текст от символов которые плохо читаются
    text = _clean(text)

    # Ограничение длины (edge-tts не любит очень длинные тексты)
    if len(text) > 400:
        text = text[:397] + "..."

    try:
        return await _edge_tts(text)
    except Exception as e:
        log.warning(f"edge-tts не работает: {e}, пробую gTTS...")
        try:
            return await _gtts(text)
        except Exception as e2:
            log.error(f"gTTS тоже не работает: {e2}")
            return None


async def _edge_tts(text: str) -> str:
    """Microsoft Edge TTS — основной, бесплатный"""
    import edge_tts
    import uuid

    out = str(TMP / f"tts_{uuid.uuid4().hex[:8]}.mp3")

    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate="+5%",    # чуть быстрее стандартного
        volume="+0%"
    )
    await communicate.save(out)

    # Чистим старые файлы (держим только последние 10)
    _cleanup()

    return out


async def _gtts(text: str) -> str:
    """Google TTS — запасной, тоже бесплатный"""
    from gtts import gTTS
    import uuid

    out = str(TMP / f"tts_{uuid.uuid4().hex[:8]}.mp3")

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: gTTS(text=text, lang="ru").save(out))

    return out


def _clean(text: str) -> str:
    """Убираем символы которые мешают TTS"""
    import re
    # Убираем markdown
    text = re.sub(r"[*_`~>#]", "", text)
    # Убираем лишние пробелы
    text = re.sub(r"\s+", " ", text)
    # Убираем ссылки
    text = re.sub(r"https?://\S+", "ссылка", text)
    return text.strip()


def _cleanup():
    """Удаляем старые TTS файлы"""
    import time
    now = time.time()
    files = sorted(TMP.glob("tts_*.mp3"), key=lambda f: f.stat().st_mtime)
    # Удаляем файлы старше 10 минут или если их больше 15
    for f in files[:-15]:
        try:
            f.unlink()
        except:
            pass
    for f in TMP.glob("tts_*.mp3"):
        try:
            if now - f.stat().st_mtime > 600:
                f.unlink()
        except:
            pass
