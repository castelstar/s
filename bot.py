"""
Discord голосовой бот «Алиса» — ПОЛНОСТЬЮ БЕСПЛАТНАЯ версия

Что используем и почему бесплатно:
- Discord API — бесплатно всегда
- edge-tts (Microsoft Edge TTS) — бесплатно, не нужен ключ
- Google Speech Recognition — бесплатно (через интернет)
- YandexGPT Lite через Yandex Cloud — при регистрации дают 4000₽ грант на 60 дней
  (1000 токенов = 0.10₽, т.е. 4000₽ хватит на ~40 миллионов токенов!)
  Если грант кончится — бот переключается на встроенные ответы без AI
"""

import discord
from discord.ext import commands
import asyncio
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# --- Настройки ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
BOT_NAME      = os.getenv("BOT_NAME", "Алиса")

# --- Настройка Discord ---
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states    = True
intents.guilds          = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- Состояние по серверам ---
class GuildState:
    def __init__(self):
        self.voice_client      = None
        self.is_listening      = False
        self.history           = []   # история диалога
        self.text_channel      = None
        self.tts_playing       = False

states: dict[int, GuildState] = {}

def state(gid: int) -> GuildState:
    if gid not in states:
        states[gid] = GuildState()
    return states[gid]


# ════════════════════════════════════
#  СОБЫТИЯ
# ════════════════════════════════════

@bot.event
async def on_ready():
    log.info(f"✅ Бот {bot.user} запущен!")
    log.info(f"🤖 Имя ассистента: {BOT_NAME}")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=f"скажи «{BOT_NAME}»"
        )
    )


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content
    low     = content.lower()
    bot_low = BOT_NAME.lower()

    # Обрабатываем команды (! в начале)
    await bot.process_commands(message)

    # Реагируем на имя без команды
    if bot_low in low and not low.startswith("!"):
        s = state(message.guild.id)
        s.text_channel = message.channel

        # Убираем имя из запроса
        query = low.replace(bot_low, "").strip(" ,!?.")
        if not query:
            query = "Привет!"

        async with message.channel.typing():
            reply = await get_ai_response(query, s)

        await message.channel.send(reply)

        # Если бот в войсе — озвучить
        if message.guild.voice_client and message.guild.voice_client.is_connected():
            await say(message.guild.id, reply)


# ════════════════════════════════════
#  КОМАНДЫ
# ════════════════════════════════════

@bot.command(name="join", aliases=["войди", "зайди", "подключись"])
async def cmd_join(ctx):
    """Зайти в твой голосовой канал"""
    if not ctx.author.voice:
        await ctx.send("❌ Ты не в голосовом канале! Зайди в войс и повтори.")
        return

    ch = ctx.author.voice.channel
    s  = state(ctx.guild.id)
    s.text_channel = ctx.channel

    if ctx.voice_client:
        await ctx.voice_client.move_to(ch)
        vc = ctx.voice_client
    else:
        vc = await ch.connect()

    s.voice_client = vc

    msg = await ctx.send(
        f"🎙️ Привет! Я **{BOT_NAME}**.\n"
        f"Напиши `!слушай` — и я начну слышать тебя.\n"
        f"Или просто напиши **{BOT_NAME}, [вопрос]** в чат — я отвечу!"
    )
    await say(ctx.guild.id, f"Привет! Я {BOT_NAME}, готова помочь!")


@bot.command(name="leave", aliases=["уйди", "выйди", "пока"])
async def cmd_leave(ctx):
    if ctx.voice_client:
        s = state(ctx.guild.id)
        s.is_listening = False
        s.history      = []
        await say(ctx.guild.id, "До свидания!")
        await asyncio.sleep(2)
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Ушла. Позови командой `!join` когда понадоблюсь!")
    else:
        await ctx.send("❌ Я сейчас не в голосовом канале.")


@bot.command(name="listen", aliases=["слушай", "слушать", "включи"])
async def cmd_listen(ctx):
    if not ctx.voice_client:
        await ctx.send("❌ Сначала позови меня: `!join`")
        return

    s = state(ctx.guild.id)
    s.is_listening = True
    s.text_channel = ctx.channel

    await ctx.send(
        f"👂 **Слушаю!** Говори в микрофон.\n"
        f"Бот распознаёт речь и реагирует на слово **«{BOT_NAME}»**.\n"
        f"*(Для полного STT нужна доп. библиотека — см. README)*\n"
        f"Пока что пиши **{BOT_NAME}, вопрос** в текстовый чат — отвечу и голосом!"
    )
    await say(ctx.guild.id, "Слушаю! Можешь говорить.")


@bot.command(name="stop", aliases=["стоп", "замолчи", "хватит"])
async def cmd_stop(ctx):
    s = state(ctx.guild.id)
    s.is_listening = False

    # Прервать воспроизведение если играет
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()

    await ctx.send("⏸️ Остановлена. Напиши `!слушай` чтобы продолжить.")


@bot.command(name="ask", aliases=["спроси", "скажи", "а"])
async def cmd_ask(ctx, *, question: str = ""):
    """Задать вопрос текстом, ответ придёт в чат и голосом"""
    if not question:
        await ctx.send(f"Использование: `!ask [вопрос]`\nПример: `!ask как дела?`")
        return

    s = state(ctx.guild.id)
    s.text_channel = ctx.channel

    async with ctx.typing():
        reply = await get_ai_response(question, s)

    await ctx.send(reply)

    if ctx.voice_client and ctx.voice_client.is_connected():
        await say(ctx.guild.id, reply)


@bot.command(name="reset", aliases=["сброс", "забудь", "очисти"])
async def cmd_reset(ctx):
    s = state(ctx.guild.id)
    s.history = []
    await ctx.send("🔄 История очищена. Начнём заново!")
    if ctx.voice_client and ctx.voice_client.is_connected():
        await say(ctx.guild.id, "Хорошо, начинаем с чистого листа!")


@bot.command(name="статус", aliases=["status", "инфо"])
async def cmd_status(ctx):
    from ai_handler import AI_AVAILABLE
    s = state(ctx.guild.id)
    embed = discord.Embed(title=f"📊 Статус {BOT_NAME}", color=discord.Color.green())
    embed.add_field(name="🧠 AI",         value="✅ YandexGPT" if AI_AVAILABLE else "⚠️ Встроенные ответы",  inline=True)
    embed.add_field(name="🔊 TTS",        value="✅ edge-tts (бесплатно)",        inline=True)
    embed.add_field(name="👂 Слушаю",     value="✅" if s.is_listening else "❌",  inline=True)
    embed.add_field(name="🎙️ В войсе",   value="✅" if ctx.voice_client else "❌", inline=True)
    embed.add_field(name="💬 История",    value=f"{len(s.history)//2} сообщений",  inline=True)
    await ctx.send(embed=embed)


@bot.command(name="help_bot", aliases=["помощь", "команды", "хелп"])
async def cmd_help(ctx):
    embed = discord.Embed(
        title=f"🤖 {BOT_NAME} — Команды",
        color=discord.Color.blue()
    )
    embed.add_field(name="🎙️ Голос", value=(
        "`!join` / `!войди` — Зайти в канал\n"
        "`!leave` / `!уйди` — Выйти\n"
        "`!listen` / `!слушай` — Начать слушать\n"
        "`!stop` / `!стоп` — Остановить"
    ), inline=False)
    embed.add_field(name="💬 Общение", value=(
        f"`!ask [вопрос]` — Спросить\n"
        f"Напиши **{BOT_NAME}, вопрос** — автоответ\n"
        "`!reset` / `!сброс` — Забыть историю"
    ), inline=False)
    embed.add_field(name="ℹ️ Прочее", value=(
        "`!статус` — Показать статус бота\n"
        "`!помощь` — Эта справка"
    ), inline=False)
    embed.set_footer(text="Всё бесплатно: edge-tts + YandexGPT Lite (4000₽ грант)")
    await ctx.send(embed=embed)


# ════════════════════════════════════
#  AI И TTS
# ════════════════════════════════════

async def get_ai_response(user_input: str, s: GuildState) -> str:
    from ai_handler import get_response
    reply = await get_response(user_input, s.history, BOT_NAME)

    # Сохраняем в историю (последние 20 сообщений)
    s.history.append({"role": "user",      "content": user_input})
    s.history.append({"role": "assistant", "content": reply})
    if len(s.history) > 20:
        s.history = s.history[-20:]

    return reply


async def say(guild_id: int, text: str):
    """Озвучить текст в голосовом канале"""
    guild = bot.get_guild(guild_id)
    if not guild or not guild.voice_client or not guild.voice_client.is_connected():
        return

    # Ждём пока закончится предыдущая фраза
    while guild.voice_client.is_playing():
        await asyncio.sleep(0.3)

    try:
        from tts_handler import synth
        audio_path = await synth(text)
        if audio_path:
            guild.voice_client.play(
                discord.FFmpegPCMAudio(audio_path),
                after=lambda e: log.debug(f"TTS done: {e or 'ok'}")
            )
    except Exception as e:
        log.error(f"Ошибка TTS: {e}")


# ════════════════════════════════════
#  ЗАПУСК
# ════════════════════════════════════

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        log.error("❌ Не найден DISCORD_TOKEN в файле .env!")
        log.error("   Скопируй .env.example → .env и заполни токен")
        exit(1)

    log.info("🚀 Запускаю бота...")
    bot.run(DISCORD_TOKEN)
