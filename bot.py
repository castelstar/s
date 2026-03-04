"""
Discord бот — Полная версия с приколюхами
Голос · Музыка · Погода · Картинки · Мемы · Игры · XP · Опросы
"""

import discord
from discord.ext import commands
import asyncio
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
BOT_NAME      = os.getenv("BOT_NAME", "Алиса")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states    = True
intents.guilds          = True
intents.members         = True
bot = commands.Bot(command_prefix="!", intents=intents)

class GuildState:
    def __init__(self):
        self.history = []; self.is_listening = False; self.text_channel = None

states: dict[int, GuildState] = {}
def state(gid): 
    if gid not in states: states[gid] = GuildState()
    return states[gid]

@bot.event
async def on_ready():
    log.info(f"✅ {bot.user} запущен!")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"скажи «{BOT_NAME}»"))

@bot.event
async def on_member_join(member):
    from extras import welcome_member
    await welcome_member(member, say)

@bot.event
async def on_message(message):
    if message.author.bot: return
    from extras import add_xp
    await add_xp(message, BOT_NAME)
    await bot.process_commands(message)
    low = message.content.lower(); bot_low = BOT_NAME.lower()
    if bot_low in low and not low.startswith("!"):
        s = state(message.guild.id); s.text_channel = message.channel
        query = low.replace(bot_low, "").strip(" ,!?.") or "Привет!"
        async with message.channel.typing():
            reply = await get_ai_response(query, s)
        await message.channel.send(reply)
        if message.guild.voice_client and message.guild.voice_client.is_connected():
            await say(message.guild.id, reply)

# ГОЛОС
@bot.command(name="join", aliases=["войди","зайди"])
async def cmd_join(ctx):
    if not ctx.author.voice: return await ctx.send("❌ Зайди в голосовой канал!")
    ch = ctx.author.voice.channel; state(ctx.guild.id).text_channel = ctx.channel
    if ctx.voice_client: await ctx.voice_client.move_to(ch)
    else: await ch.connect()
    await ctx.send(f"🎙️ В **{ch.name}**! `!помощь` — список команд.")

@bot.command(name="leave", aliases=["уйди","выйди"])
async def cmd_leave(ctx):
    if ctx.voice_client: await ctx.voice_client.disconnect(); await ctx.send("👋")
    else: await ctx.send("❌ Не в войсе.")

@bot.command(name="ask", aliases=["спроси","а"])
async def cmd_ask(ctx, *, q=""):
    if not q: return await ctx.send("Пример: `!ask как дела?`")
    s = state(ctx.guild.id)
    async with ctx.typing(): reply = await get_ai_response(q, s)
    await ctx.send(reply)
    if ctx.voice_client and ctx.voice_client.is_connected(): await say(ctx.guild.id, reply)

@bot.command(name="reset", aliases=["сброс"])
async def cmd_reset(ctx): state(ctx.guild.id).history = []; await ctx.send("🔄 История очищена!")

# МУЗЫКА
@bot.command(name="play", aliases=["играй","музыка","п"])
async def cmd_play(ctx, *, url=""):
    if not url: return await ctx.send("Пример: `!play lofi hip hop`")
    from music import cmd_play as f; await f(ctx, url)

@bot.command(name="skip", aliases=["скип","пропусти"])
async def cmd_skip(ctx):
    from music import cmd_skip as f; await f(ctx)

@bot.command(name="pause", aliases=["пауза"])
async def cmd_pause(ctx):
    from music import cmd_pause as f; await f(ctx)

@bot.command(name="resume", aliases=["продолжить"])
async def cmd_resume(ctx):
    from music import cmd_resume as f; await f(ctx)

@bot.command(name="queue", aliases=["очередь"])
async def cmd_queue(ctx):
    from music import cmd_queue as f; await f(ctx)

@bot.command(name="np", aliases=["играет"])
async def cmd_np(ctx):
    from music import cmd_nowplaying as f; await f(ctx)

@bot.command(name="volume", aliases=["громкость"])
async def cmd_volume(ctx, vol: int=70):
    from music import cmd_volume as f; await f(ctx, vol)

@bot.command(name="stopmusic", aliases=["стоп_музыку"])
async def cmd_stopmusic(ctx):
    from music import cmd_stop_music as f; await f(ctx)

# ПОГОДА
@bot.command(name="погода", aliases=["weather"])
async def cmd_weather(ctx, *, city=""):
    from weather import cmd_weather as f; await f(ctx, city=city, say_func=say)

# КАРТИНКИ
@bot.command(name="imagine", aliases=["нарисуй","img"])
async def cmd_imagine(ctx, *, prompt=""):
    from imagine import cmd_imagine as f; await f(ctx, prompt=prompt)

# ОПРОСЫ
@bot.command(name="опрос", aliases=["poll"])
async def cmd_poll(ctx, *, args=""):
    from extras import cmd_poll as f; await f(ctx, args=args)

@bot.command(name="итог_опроса", aliases=["endpoll"])
async def cmd_endpoll(ctx, message_id: int=0):
    from extras import cmd_endpoll as f; await f(ctx, message_id)

# XP
@bot.command(name="ранг", aliases=["rank","xp"])
async def cmd_rank(ctx):
    from extras import cmd_rank as f; await f(ctx)

@bot.command(name="топ", aliases=["leaderboard","рейтинг"])
async def cmd_top(ctx):
    from extras import cmd_leaderboard as f; await f(ctx)

# ПРИКОЛЮХИ
@bot.command(name="мем", aliases=["meme","mem"])
async def cmd_meme(ctx):
    from extras import cmd_meme as f; await f(ctx)

@bot.command(name="анекдот", aliases=["joke","анек"])
async def cmd_joke(ctx):
    from extras import cmd_joke as f; await f(ctx)

@bot.command(name="шар", aliases=["ball","судьба"])
async def cmd_ball(ctx, *, question=""):
    from extras import cmd_ball as f; await f(ctx, question=question)

@bot.command(name="пд", aliases=["truthordare"])
async def cmd_tod(ctx, *, choice=""):
    from extras import cmd_truth_or_dare_choice as f; await f(ctx, choice)

@bot.command(name="ктоты", aliases=["личность","whoareyou"])
async def cmd_who(ctx, member: discord.Member=None):
    from extras import cmd_who_are_you as f; await f(ctx, member)

@bot.command(name="некролог", aliases=["obituary","rip"])
async def cmd_obit(ctx, member: discord.Member=None):
    from extras import cmd_obituary as f; await f(ctx, member)

@bot.command(name="гороскоп", aliases=["horoscope","звёзды"])
async def cmd_horoscope(ctx, *, sign=""):
    from extras import cmd_horoscope as f; await f(ctx, sign=sign)

@bot.command(name="рулетка", aliases=["roulette","удача"])
async def cmd_roulette(ctx):
    from extras import cmd_roulette as f; await f(ctx)

@bot.command(name="бой", aliases=["fight","драка","vs"])
async def cmd_fight(ctx, opponent: discord.Member=None):
    from extras import cmd_fight as f; await f(ctx, opponent)

@bot.command(name="rpg", aliases=["игра","приключение"])
async def cmd_rpg(ctx, *, action=""):
    from extras import cmd_rpg as f; await f(ctx, action=action, bot_name=BOT_NAME)

# ПОМОЩЬ
@bot.command(name="help_bot", aliases=["помощь","команды","хелп"])
async def cmd_help(ctx):
    embed = discord.Embed(title=f"🤖 {BOT_NAME} — Все команды", color=discord.Color.blue())
    embed.add_field(name="🎙️ Голос & AI", value=f"`!join` `!leave` `!ask [вопрос]`\nНапиши **{BOT_NAME}, вопрос** — автоответ\n`!reset` — забыть историю", inline=False)
    embed.add_field(name="🎵 Музыка", value="`!play [ссылка/название]` — Включить\n`!skip` `!pause` `!resume` `!queue` `!np`\n`!volume 80` `!stopmusic`", inline=False)
    embed.add_field(name="🎮 Игры", value=(
        "`!шар [вопрос]` — 🎱 Шар судьбы\n"
        "`!пд` — 🤔 Правда или Действие\n"
        "`!бой @юзер` — ⚔️ Эпичный бой\n"
        "`!рулетка` — 🎰 Испытай удачу\n"
        "`!ктоты [@юзер]` — 🎭 Личность дня\n"
        "`!некролог [@юзер]` — 💀 Некролог\n"
        "`!rpg` — ⚔️ Текстовая RPG игра"
    ), inline=False)
    embed.add_field(name="😂 Контент", value="`!мем` `!анекдот` `!гороскоп [знак]`\n`!imagine [описание]` `!погода [город]`", inline=False)
    embed.add_field(name="📊 Сервер", value="`!опрос Вопрос? | Вар1 | Вар2`\n`!ранг` `!топ`", inline=False)
    embed.set_footer(text="✅ Всё бесплатно!")
    await ctx.send(embed=embed)

@bot.command(name="статус", aliases=["status"])
async def cmd_status(ctx):
    from ai_handler import AI_AVAILABLE
    from music import current as mc
    cur = mc.get(ctx.guild.id)
    embed = discord.Embed(title=f"📊 {BOT_NAME}", color=discord.Color.green())
    embed.add_field(name="🧠 AI", value="✅ YandexGPT" if AI_AVAILABLE else "⚠️ Встроенные", inline=True)
    embed.add_field(name="🎵 Музыка", value=f"▶️ {cur.title[:20]}" if cur else "—", inline=True)
    embed.add_field(name="🎙️ Войс", value="✅" if ctx.voice_client else "❌", inline=True)
    await ctx.send(embed=embed)

# AI И TTS
async def get_ai_response(user_input: str, s: GuildState) -> str:
    from ai_handler import get_response
    reply = await get_response(user_input, s.history, BOT_NAME)
    s.history.append({"role": "user", "content": user_input})
    s.history.append({"role": "assistant", "content": reply})
    if len(s.history) > 20: s.history = s.history[-20:]
    return reply

async def say(guild_id: int, text: str):
    guild = bot.get_guild(guild_id)
    if not guild or not guild.voice_client or not guild.voice_client.is_connected(): return
    if guild.voice_client.is_playing(): return
    try:
        from tts_handler import synth
        path = await synth(text)
        if path: guild.voice_client.play(discord.FFmpegPCMAudio(path), after=lambda e: None)
    except Exception as e: log.error(f"TTS: {e}")

if __name__ == "__main__":
    if not DISCORD_TOKEN: log.error("❌ Не найден DISCORD_TOKEN в .env!"); exit(1)
    log.info("🚀 Запускаю бота...")
    bot.run(DISCORD_TOKEN)
