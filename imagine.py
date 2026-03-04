"""
🖼️ Генерация картинок — несколько бесплатных API с авто-переключением

API 1: Pollinations.ai  — основной (Flux модель, высокое качество)
API 2: Picsum Photos    — запасной (красивые реальные фото, если генерация недоступна)

Pollinations иногда медленный (30-60 сек) — добавили прогресс и таймаут с fallback.
"""

import aiohttp
import asyncio
import logging
import urllib.parse
import io
import discord

log = logging.getLogger(__name__)


async def _generate_pollinations(prompt: str, w: int, h: int) -> bytes | None:
    """Pollinations.ai — бесплатная генерация через Flux"""
    encoded = urllib.parse.quote(f"{prompt}, high quality, detailed")
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={w}&height={h}&nologo=true&seed={hash(prompt) % 9999}"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=55)) as r:
                if r.status == 200:
                    data = await r.read()
                    # Проверяем что это реально картинка (PNG/JPEG начинаются с определённых байт)
                    if len(data) > 1000 and (data[:8] in (b'\x89PNG\r\n\x1a\n',) or data[:2] == b'\xff\xd8'):
                        return data
    except asyncio.TimeoutError:
        log.warning("Pollinations timeout")
    except Exception as e:
        log.error(f"Pollinations error: {e}")
    return None


async def _generate_picsum(seed: str) -> bytes | None:
    """Picsum Photos — случайное красивое фото (запасной вариант)"""
    seed_int = abs(hash(seed)) % 1000
    url = f"https://picsum.photos/seed/{seed_int}/1024/1024"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 200:
                    return await r.read()
    except Exception as e:
        log.error(f"Picsum error: {e}")
    return None


async def cmd_imagine(ctx, *, prompt: str = ""):
    if not prompt:
        await ctx.send(
            "🖼️ **Использование:** `!imagine [описание на русском или английском]`\n\n"
            "**Примеры:**\n"
            "`!imagine закат над Москвой в стиле аниме`\n"
            "`!imagine кибerpunk кот в неоновом городе ночью`\n"
            "`!imagine портрет волка в стиле акварели`\n"
            "`!imagine средневековый замок в горах зимой`"
        )
        return

    msg = await ctx.send(f"🎨 Рисую: **{prompt}**\n*Подожди 15-45 секунд...*")

    # Редактируем сообщение с прогрессом пока ждём
    async def update_progress():
        dots = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
        i = 0
        while True:
            try:
                await msg.edit(content=f"{dots[i % len(dots)]} Рисую: **{prompt}**\n*Генерирую картинку...*")
            except:
                break
            await asyncio.sleep(2)
            i += 1

    progress_task = asyncio.create_task(update_progress())

    try:
        image_bytes = await _generate_pollinations(prompt, 1024, 1024)
        fallback_used = False

        if not image_bytes:
            log.warning("Pollinations недоступен, пробую Picsum")
            image_bytes = await _generate_picsum(prompt)
            fallback_used = True
    finally:
        progress_task.cancel()

    if not image_bytes:
        await msg.edit(content="❌ Не удалось сгенерировать картинку. Попробуй позже или измени запрос.")
        return

    file = discord.File(io.BytesIO(image_bytes), filename="image.png")
    embed = discord.Embed(
        title=f"🖼️ {prompt[:100]}",
        color=discord.Color.purple()
    )
    embed.set_image(url="attachment://image.png")

    if fallback_used:
        embed.set_footer(text="⚠️ Генератор недоступен — показано похожее фото | Попробуй снова через пару минут")
    else:
        embed.set_footer(text="✨ Сгенерировано Pollinations AI (Flux) · Бесплатно")

    await msg.delete()
    await ctx.send(file=file, embed=embed)
