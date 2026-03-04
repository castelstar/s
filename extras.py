"""
Все приколюхи, игры и развлечения бота.

😂 Мемы          — imgflip + встроенная коллекция (без Reddit!)
🎱 Шар судьбы    — !шар [вопрос]
🤔 Правда/Действие — !пд
🎭 Чья личность  — !ты кто
💀 Некролог      — !некролог @юзер
🔮 Гороскоп      — !гороскоп [знак]
🎰 Рулетка       — !рулетка
🤣 Анекдот       — !анекдот
💪 Бой           — !бой @юзер
📊 Опросы        — !опрос
🏆 XP система    — автоматически
👋 Приветствия   — автоматически
⚔️ RPG           — !rpg
"""

import discord
import asyncio
import random
import json
import os
import logging
from pathlib import Path
from datetime import datetime

log = logging.getLogger(__name__)


# ════════════════════════════════════════════════
#  😂 МЕМЫ — только рабочие источники
# ════════════════════════════════════════════════

# Большая встроенная коллекция — работает ВСЕГДА без интернета
MEMES = [
    # Программисты
    ("Когда исправил один баг и появилось 3 новых", "https://i.imgflip.com/26am.jpg"),
    ("Когда код работает но ты не знаешь почему", "https://i.imgflip.com/3si4n4.jpg"),
    ("Senior vs Junior разработчик", "https://i.imgflip.com/1bij.jpg"),
    ("Когда продакшн упал в пятницу вечером", "https://i.imgflip.com/30b1gx.jpg"),
    ("Тестирование в разработке vs продакшне", "https://i.imgflip.com/1g8my4.jpg"),
    # Жизнь
    ("Я: лягу спать в 22:00. Я в 3 ночи:", "https://i.imgflip.com/4t0m5.jpg"),
    ("Понедельник утром", "https://i.imgflip.com/2wifvo.jpg"),
    ("Когда выходной но ты ничего не сделал", "https://i.imgflip.com/2gnfar.jpg"),
    ("Пятница vs Понедельник", "https://i.imgflip.com/3oevdk.jpg"),
    ("Я и моя прокрастинация", "https://i.imgflip.com/2hgfw.jpg"),
    # Дискорд
    ("Когда бот наконец заработал", "https://i.imgflip.com/4fhsge.jpg"),
    ("Войс канал в 3 ночи", "https://i.imgflip.com/3lmzyx.jpg"),
    ("Когда пишешь в общий чат но никто не отвечает", "https://i.imgflip.com/1otk96.jpg"),
]

# Imgflip публичный API — работает надёжно
IMGFLIP_MEMES_URL = "https://api.imgflip.com/get_memes"


async def cmd_meme(ctx):
    """!мем — случайный мем (всегда работает)"""
    import aiohttp

    msg = await ctx.send("😂 Ищу мем...")

    # Пробуем imgflip API
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(IMGFLIP_MEMES_URL, timeout=aiohttp.ClientTimeout(total=6)) as r:
                if r.status == 200:
                    data = await r.json()
                    if data.get("success"):
                        memes_list = data["data"]["memes"]
                        # Берём случайный мем из топ-100
                        meme = random.choice(memes_list[:100])
                        embed = discord.Embed(
                            title=meme["name"],
                            color=discord.Color.orange()
                        )
                        embed.set_image(url=meme["url"])
                        embed.set_footer(text=f"imgflip.com · 👍 {meme.get('captions', 0)} использований")
                        try:
                            await msg.delete()
                        except Exception:
                            pass
                        await ctx.send(embed=embed)
                        return
    except Exception as e:
        log.warning(f"Imgflip недоступен: {e}")

    # Fallback — встроенные мемы
    title, img_url = random.choice(MEMES)
    embed = discord.Embed(title=title, color=discord.Color.orange())
    embed.set_image(url=img_url)
    embed.set_footer(text="😄 Мем из встроенной коллекции")
    try:
        await msg.delete()
    except Exception:
        pass
    await ctx.send(embed=embed)


# ════════════════════════════════════════════════
#  🎱 ШАР СУДЬБЫ
# ════════════════════════════════════════════════

BALL_ANSWERS = [
    # Положительные
    ("🟢", "Бесспорно!"),
    ("🟢", "Именно так!"),
    ("🟢", "Без сомнений!"),
    ("🟢", "Да — определённо!"),
    ("🟢", "По всем признакам — да!"),
    ("🟢", "Можешь рассчитывать на это!"),
    ("🟡", "Скорее всего — да!"),
    ("🟡", "Хорошие перспективы!"),
    ("🟡", "Знаки указывают — да!"),
    # Нейтральные
    ("🟠", "Пока неясно, спроси позже..."),
    ("🟠", "Не могу предсказать сейчас!"),
    ("🟠", "Сосредоточься и спроси снова!"),
    # Отрицательные
    ("🔴", "Не рассчитывай на это!"),
    ("🔴", "Мой ответ — нет!"),
    ("🔴", "По всем признакам — нет!"),
    ("🔴", "Очень сомнительно!"),
    ("🔴", "Весьма маловероятно..."),
]


async def cmd_ball(ctx, *, question: str = ""):
    if not question:
        await ctx.send("🎱 Использование: `!шар [твой вопрос]`\nПример: `!шар я сегодня выспался?`")
        return
    emoji, answer = random.choice(BALL_ANSWERS)
    embed = discord.Embed(color=discord.Color.dark_purple())
    embed.add_field(name="❓ Вопрос", value=question, inline=False)
    embed.add_field(name=f"{emoji} Шар отвечает", value=f"**{answer}**", inline=False)
    embed.set_footer(text="🎱 Магический шар судьбы")
    await ctx.send(embed=embed)


# ════════════════════════════════════════════════
#  🤣 АНЕКДОТЫ
# ════════════════════════════════════════════════

JOKES = [
    "Программист заходит в лифт.\nЕму говорят: «Нажми на 5-й этаж».\nОн отвечает: «Это не входит в мои функции».",
    "— Как называется группа людей, которая стоит перед компьютером?\n— Очередь к программисту.",
    "Вчера написал код такой чистый, что даже не захотелось его комментировать.\nСегодня пытаюсь понять что он делает.",
    "— Папа, почему солнце встаёт на востоке?\n— Работает? Работает. Не трогай.",
    "Сисадмин — это человек, который думает, что пользователи существуют чтобы мешать ему работать.",
    "QA Engineer заходит в бар. Заказывает 0 пива. Заказывает 999999 пив. Заказывает -1 пиво. Заказывает NULL пиво.\nБар не взрывается. QA идёт домой довольный.",
    "Был такой баг... написал `if (true)` — и всё сломалось.",
    "— Почему программисты путают Halloween и Christmas?\n— Потому что Oct 31 = Dec 25!",
    "Встречаются два программиста:\n— Как дела?\n— Если не считать пятницы — undefined.",
    "Мой код работает. Не знаю почему. Боюсь трогать.",
    "— Сынок, ты чем занимаешься?\n— Пишу программу, мама.\n— А долго ещё?\n— Ну это зависит от компилятора.",
    "Гит blame показывает что виновный — ты сам три года назад.",
]


async def cmd_joke(ctx):
    """!анекдот — случайный анекдот"""
    joke = random.choice(JOKES)
    embed = discord.Embed(
        description=joke,
        color=discord.Color.yellow()
    )
    embed.set_author(name="🤣 Анекдот")
    await ctx.send(embed=embed)


# ════════════════════════════════════════════════
#  🤔 ПРАВДА ИЛИ ДЕЙСТВИЕ
# ════════════════════════════════════════════════

TRUTHS = [
    "Какой самый неловкий момент в твоей жизни?",
    "Кого из людей на этом сервере ты считаешь самым умным?",
    "Что ты никогда не сделаешь снова?",
    "Какой твой самый большой страх?",
    "Что ты скрываешь от своих родителей?",
    "Какую песню ты слушаешь втайне?",
    "Кому из участников сервера ты бы написал первым если бы мир заканчивался?",
    "Что тебе больше всего нравится в себе?",
    "Какой твой самый странный талант?",
    "Если бы ты мог стереть одно воспоминание — что бы это было?",
    "Какая твоя самая большая ложь в жизни?",
    "На каком сайте ты проводишь больше всего времени?",
]

DARES = [
    "Напиши случайному человеку в лс: «Ты думал я не замечу? Я всё вижу» и жди ответа!",
    "Отправь последний скрин из галереи (если не стыдно 😏)",
    "Напиши следующее сообщение КАПСЛОКОМ",
    "Измени никнейм на «Я ЛЮБИТЕЛЬ АНИМЕ» на 10 минут",
    "Позвони другу и спой ему куплет любой песни",
    "Напиши комплимент каждому участнику в войсе",
    "Расскажи историю про свой самый позорный день",
    "Имитируй голос любого участника сервера",
    "Следующие 5 минут отвечай только голосовыми в чат",
    "Напиши статус: «Ищу друзей» на 15 минут",
    "Придумай рэп-куплет про этот сервер прямо сейчас",
    "Поставь реакцию 👍 на 10 случайных сообщений в чате",
]


async def cmd_truth_or_dare(ctx):
    """!пд — случайное правда или действие"""
    is_truth = random.random() > 0.5
    if is_truth:
        text  = random.choice(TRUTHS)
        title = "🤔 ПРАВДА"
        color = discord.Color.blue()
    else:
        text  = random.choice(DARES)
        title = "💀 ДЕЙСТВИЕ"
        color = discord.Color.red()

    embed = discord.Embed(
        title=f"{title} для {ctx.author.display_name}",
        description=text,
        color=color
    )
    embed.set_footer(text="!пд — другой вопрос | !пд правда — только правда | !пд действие — только действие")
    await ctx.send(embed=embed)


async def cmd_truth_or_dare_choice(ctx, choice: str = ""):
    choice = choice.lower()
    if "правда" in choice or "truth" in choice:
        text  = random.choice(TRUTHS)
        title = "🤔 ПРАВДА"
        color = discord.Color.blue()
    elif "действие" in choice or "dare" in choice:
        text  = random.choice(DARES)
        title = "💀 ДЕЙСТВИЕ"
        color = discord.Color.red()
    else:
        await cmd_truth_or_dare(ctx)
        return

    embed = discord.Embed(
        title=f"{title} для {ctx.author.display_name}",
        description=text,
        color=color
    )
    await ctx.send(embed=embed)


# ════════════════════════════════════════════════
#  🎭 КТО ТЫ? — случайная "личность"
# ════════════════════════════════════════════════

PERSONALITIES = [
    ("🧠 Гений-отшельник", "Ты умнее всех в комнате и все об этом знают. Особенно ты."),
    ("😴 Профессиональный прокрастинатор", "Сделаю завтра. Или послезавтра. Точно на этой неделе."),
    ("🎮 Игровой бог", "В реальной жизни — нуб. В игре — легенда."),
    ("☕ Кофейный маньяк", "До первой чашки ты — зомби. После третьей — CEO."),
    ("🕵️ Тихий наблюдатель", "Ты знаешь всё про всех, но молчишь. Страшная сила."),
    ("🤡 Клоун сервера", "Ты смешной. Иногда специально."),
    ("📱 Мем-лорд", "Ты думаешь мемами. Ты дышишь мемами. Ты И ЕСТЬ мем."),
    ("🦁 Лидер без армии", "Ты рождён командовать. Жаль что никто не слушается."),
    ("🧟 Ночной житель", "Днём — нет. Ночью — о да."),
    ("🎵 Тайный музыкант", "Слушаешь странную музыку. В наушниках. Никому не показываешь плейлист."),
    ("💬 Болтун-рекордсмен", "Слова закончатся у всех. Только не у тебя."),
    ("🦥 Мастер релакса", "Стресс? Не слышал. Проблемы решаются сами. Ты просто ждёшь."),
    ("🔥 Хаотичное добро", "Помогаешь всем. Но делаешь это как-то... странно."),
    ("🧙 Загадочный тип", "Никто не знает чем ты занимаешься. Даже ты не всегда понимаешь."),
    ("⚡ Энергетик на ногах", "Ты всегда в движении. Ты не можешь просто сидеть. Зачем сидеть?!"),
]


async def cmd_who_are_you(ctx, member: discord.Member = None):
    """!ктоты [@юзер] — случайная личность"""
    target = member or ctx.author
    personality, desc = random.choice(PERSONALITIES)

    # Псевдо-случайный но стабильный для каждого юзера (один раз в день разный)
    day_seed = int(datetime.now().strftime("%Y%m%d")) + target.id
    random.seed(day_seed)
    personality, desc = random.choice(PERSONALITIES)
    random.seed()  # сбрасываем seed

    embed = discord.Embed(
        title=f"{personality}",
        description=f"{target.mention} — **{personality}**\n\n{desc}",
        color=discord.Color.blurple()
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.set_footer(text="Обновляется каждый день!")
    await ctx.send(embed=embed)


# ════════════════════════════════════════════════
#  💀 НЕКРОЛОГ
# ════════════════════════════════════════════════

DEATH_REASONS = [
    "был(а) убит(а) собственным прокрастинацией",
    "скончался(ась) от передоза мемами",
    "пал(а) в бою с понедельником",
    "был(а) поглощён(а) YouTube в 3 ночи",
    "не смог(ла) пережить очередного обновления Discord",
    "умер(ла) ожидая ответа в чате",
    "погиб(ла) в попытке понять документацию",
    "ушёл(ушла) в другой мир после 5-го красного быка подряд",
    "был(а) сожран(а) рекомендациями TikTok",
    "скончался(ась) от смущения после случайного голосового",
    "не выдержал(а) звука уведомлений в 2 ночи",
    "пал(а) жертвой собственного WiFi",
]

LAST_WORDS = [
    "«Ещё одну серию...»",
    "«Я только проверю телефон»",
    "«Это последний мем, клянусь»",
    "«Лягу спать в 22:00»",
    "«Завтра точно начну»",
    "«Я не зависим от интернета»",
    "«Это простое задание»",
]


async def cmd_obituary(ctx, member: discord.Member = None):
    """!некролог [@юзер] — смешной некролог"""
    target = member or ctx.author
    reason     = random.choice(DEATH_REASONS)
    last_words = random.choice(LAST_WORDS)
    age        = random.randint(18, 99)

    embed = discord.Embed(
        title="💀 НЕКРОЛОГ",
        color=discord.Color.dark_gray()
    )
    embed.add_field(
        name=f"🪦 {target.display_name}",
        value=(
            f"**{age} лет**\n\n"
            f"Здесь покоится **{target.display_name}**, который(ая) {reason}.\n\n"
            f"Последние слова: *{last_words}*\n\n"
            f"Нам будет не хватать его/её постов в чате."
        ),
        inline=False
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.set_footer(text="😔 Покойся с миром | !некролог @юзер")
    await ctx.send(embed=embed)


# ════════════════════════════════════════════════
#  💪 БОЙ между участниками
# ════════════════════════════════════════════════

FIGHT_MOVES = [
    "ударил мемом", "применил тактику игнора", "бросил клавиатуру",
    "использовал способность «нытьё»", "активировал режим «не моя проблема»",
    "кинул в противника монитором", "применил дзюдзюцу прокрастинации",
    "включил режим «я устал»", "бросил пустой энергетик",
    "использовал технику «мамин аргумент»",
]

FIGHT_RESULTS = [
    "{winner} победил(а) используя силу лени!",
    "{winner} выиграл(а) после 47-раундовой битвы мемами!",
    "{winner} нокаутировал(а) соперника аргументом!",
    "{loser} сдался(ась) и ушёл(ушла) в другой войс!",
    "{winner} победил(а) с результатом {hp} HP!",
]


async def cmd_fight(ctx, opponent: discord.Member = None):
    """!бой @юзер — бой двух участников"""
    if not opponent:
        await ctx.send("Использование: `!бой @юзер`")
        return
    if opponent == ctx.author:
        await ctx.send("😂 Бороться с самим собой? Ну ладно... ТЫ ПРОИГРАЛ САМИ СЕБЕ!")
        return
    if opponent.bot:
        await ctx.send(f"🤖 {opponent.display_name} — бот. Он не может проигрывать по закону роботов.")
        return

    attacker = ctx.author
    defender = opponent

    hp_a = random.randint(40, 100)
    hp_d = random.randint(40, 100)

    lines = [f"⚔️ **{attacker.display_name}** VS **{defender.display_name}**\n"]

    rounds = 0
    while hp_a > 0 and hp_d > 0 and rounds < 5:
        rounds += 1
        dmg_a = random.randint(10, 30)
        dmg_d = random.randint(10, 30)
        move_a = random.choice(FIGHT_MOVES)
        move_d = random.choice(FIGHT_MOVES)
        hp_d  -= dmg_a
        hp_a  -= dmg_d
        lines.append(
            f"**Раунд {rounds}:**\n"
            f"➡️ {attacker.display_name} {move_a} → -{dmg_a} HP\n"
            f"⬅️ {defender.display_name} {move_d} → -{dmg_d} HP\n"
            f"❤️ {attacker.display_name}: {max(0,hp_a)} | {defender.display_name}: {max(0,hp_d)}\n"
        )

    winner = attacker if hp_a >= hp_d else defender
    loser  = defender if winner == attacker else attacker
    result_tmpl = random.choice(FIGHT_RESULTS)
    result = result_tmpl.format(winner=winner.display_name, loser=loser.display_name, hp=max(0, max(hp_a, hp_d)))
    lines.append(f"\n🏆 **{result}**")

    embed = discord.Embed(
        title="⚔️ БОЙ",
        description="\n".join(lines),
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)


# ════════════════════════════════════════════════
#  🎰 РУЛЕТКА
# ════════════════════════════════════════════════

ROULETTE_RESULTS = [
    ("💀", "СМЕРТЬ! Ты выбываешь из чата на... 0 секунд. Повезло.", discord.Color.dark_red()),
    ("🎉", "ДЖЕКПОТ! Ты получаешь виртуальные 1000 монет!", discord.Color.gold()),
    ("😐", "Ничего. Просто... ничего. Барабан равнодушен к тебе.", discord.Color.greyple()),
    ("🔥", "ОГОНЬ! Ты сегодня в ударе!", discord.Color.orange()),
    ("🍀", "УДАЧА! Этот день будет хорошим!", discord.Color.green()),
    ("💩", "Упс. Ну бывает.", discord.Color.dark_gray()),
    ("👑", "КОРОНА! Ты король/королева сегодняшнего дня!", discord.Color.gold()),
    ("🤡", "Клоун. Просто клоун.", discord.Color.red()),
    ("🦄", "ЕДИНОРОГ! Это редкость. Ты особенный.", discord.Color.purple()),
    ("☕", "Тебе нужен кофе. Срочно.", discord.Color.dark_orange()),
]


async def cmd_roulette(ctx):
    """!рулетка — испытай удачу"""
    msg = await ctx.send("🎰 Крутим барабан...")
    await asyncio.sleep(1.5)

    emoji, text, color = random.choice(ROULETTE_RESULTS)
    embed = discord.Embed(
        title=f"🎰 {emoji} {emoji} {emoji}",
        description=f"{ctx.author.mention} — **{text}**",
        color=color
    )
    await msg.edit(content="", embed=embed)


# ════════════════════════════════════════════════
#  🔮 ГОРОСКОП
# ════════════════════════════════════════════════

SIGNS = {
    "овен": "♈", "телец": "♉", "близнецы": "♊", "рак": "♋",
    "лев": "♌", "дева": "♍", "весы": "♎", "скорпион": "♏",
    "стрелец": "♐", "козерог": "♑", "водолей": "♒", "рыбы": "♓",
}

HOROSCOPE_TEMPLATES = [
    "Сегодня звёзды говорят: {advice}. Особенно это касается {sphere}.",
    "Меркурий в ретрограде, поэтому {advice}. Будь осторожен с {sphere}.",
    "День благоприятен для {activity}. {advice}.",
    "Луна в твоём знаке — это значит {advice}. Избегай {sphere}.",
]

ADVICES = [
    "не верь тому что прочтёшь в интернете",
    "возможно стоит выспаться наконец",
    "кофе — это не замена сну (но попробуй)",
    "сегодня лучший день чтобы ничего не делать",
    "скоро что-то изменится. Или нет",
    "твои планы разрушит что-нибудь мелкое",
    "сегодня кто-то думает о тебе. Скорее всего мама",
    "удача улыбается тем кто не проверяет гороскоп",
]

SPHERES  = ["денег", "любви", "еды", "WiFi соединения", "сна", "мемов", "Discord"]
ACTIVITIES = ["просмотра мемов", "ничегонеделания", "игр", "сна", "новых знакомств"]


async def cmd_horoscope(ctx, *, sign: str = ""):
    """!гороскоп [знак зодиака]"""
    if not sign:
        signs_list = " · ".join([f"{v}{k.capitalize()}" for k,v in SIGNS.items()])
        await ctx.send(f"🔮 Использование: `!гороскоп [знак]`\n{signs_list}")
        return

    sign_low = sign.lower().strip()
    if sign_low not in SIGNS:
        await ctx.send(f"❌ Знак **{sign}** не найден.\nДоступные: {', '.join(SIGNS.keys())}")
        return

    sign_emoji = SIGNS[sign_low]

    # Псевдо-случайный но разный каждый день
    seed = int(datetime.now().strftime("%Y%m%d")) + hash(sign_low)
    random.seed(seed)
    template = random.choice(HOROSCOPE_TEMPLATES)
    advice   = random.choice(ADVICES)
    sphere   = random.choice(SPHERES)
    activity = random.choice(ACTIVITIES)
    lucky_num = random.randint(1, 99)
    lucky_color = random.choice(["красный", "синий", "зелёный", "жёлтый", "фиолетовый", "чёрный"])
    random.seed()

    text = template.format(advice=advice, sphere=sphere, activity=activity)

    embed = discord.Embed(
        title=f"{sign_emoji} Гороскоп — {sign.capitalize()}",
        description=text,
        color=discord.Color.purple()
    )
    embed.add_field(name="🍀 Счастливое число", value=str(lucky_num), inline=True)
    embed.add_field(name="🎨 Счастливый цвет",  value=lucky_color,   inline=True)
    embed.set_footer(text="🔮 Звёзды предсказывают. Верить необязательно.")
    await ctx.send(embed=embed)


# ════════════════════════════════════════════════
#  📊 ОПРОСЫ
# ════════════════════════════════════════════════

active_polls: dict[int, dict] = {}
POLL_EMOJIS = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]


async def cmd_poll(ctx, *, args: str = ""):
    if not args or "|" not in args:
        await ctx.send(
            "📊 **Создание опроса:**\n"
            "`!опрос Вопрос? | Вариант 1 | Вариант 2 | Вариант 3`\n\n"
            "Пример: `!опрос Какую музыку включить? | Рэп | Рок | Электронная`"
        )
        return
    parts    = [p.strip() for p in args.split("|")]
    question = parts[0]
    options  = parts[1:]
    if len(options) < 2:
        await ctx.send("❌ Нужно хотя бы 2 варианта!")
        return
    if len(options) > 10:
        await ctx.send("❌ Максимум 10 вариантов.")
        return

    lines = [f"{POLL_EMOJIS[i]} {opt}" for i, opt in enumerate(options)]
    embed = discord.Embed(title=f"📊 {question}", description="\n\n".join(lines), color=discord.Color.gold())
    embed.set_footer(text=f"Голосование от {ctx.author.display_name} · Реагируй на цифру")
    msg = await ctx.send(embed=embed)
    for i in range(len(options)):
        await msg.add_reaction(POLL_EMOJIS[i])
    active_polls[msg.id] = {"question": question, "options": options}


async def cmd_endpoll(ctx, message_id: int = 0):
    if not message_id:
        await ctx.send("Использование: `!итог_опроса [ID сообщения]`")
        return
    if message_id not in active_polls:
        await ctx.send("❌ Опрос не найден.")
        return
    poll = active_polls[message_id]
    try:
        msg = await ctx.channel.fetch_message(message_id)
    except Exception:
        await ctx.send("❌ Сообщение не найдено.")
        return

    results = []
    total = 0
    for i, reaction in enumerate(msg.reactions):
        if i >= len(poll["options"]):
            break
        count = max(0, reaction.count - 1)
        results.append((poll["options"][i], count))
        total += count
    results.sort(key=lambda x: x[1], reverse=True)

    lines = []
    for opt, count in results:
        pct = round(count / total * 100) if total else 0
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        lines.append(f"**{opt}**\n{bar} {count} гол. ({pct}%)")

    embed = discord.Embed(title=f"📊 Итоги: {poll['question']}",
                          description="\n\n".join(lines), color=discord.Color.green())
    embed.set_footer(text=f"Всего голосов: {total}")
    await ctx.send(embed=embed)
    del active_polls[message_id]


# ════════════════════════════════════════════════
#  🏆 СИСТЕМА XP
# ════════════════════════════════════════════════

XP_FILE     = Path("xp_data.json")
XP_RANGE    = (5, 15)
XP_COOLDOWN = 60
_xp_data: dict = {}
_cooldowns: dict = {}


def _load_xp():
    global _xp_data
    if XP_FILE.exists():
        try:
            _xp_data = json.loads(XP_FILE.read_text(encoding="utf-8"))
        except Exception:
            _xp_data = {}


def _save_xp():
    try:
        XP_FILE.write_text(json.dumps(_xp_data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        log.error(f"XP save: {e}")


def _xp_needed(level: int) -> int:
    return 100 * level * level + 50 * level


def get_user(gid, uid) -> dict:
    gid, uid = str(gid), str(uid)
    _xp_data.setdefault(gid, {})
    _xp_data[gid].setdefault(uid, {"xp": 0, "level": 1, "total_xp": 0})
    return _xp_data[gid][uid]


async def add_xp(message: discord.Message, bot_name: str) -> bool:
    if message.author.bot:
        return False
    key = (str(message.guild.id), str(message.author.id))
    now = datetime.now().timestamp()
    if key in _cooldowns and now - _cooldowns[key] < XP_COOLDOWN:
        return False
    _cooldowns[key] = now

    data = get_user(message.guild.id, message.author.id)
    gain = random.randint(*XP_RANGE)
    data["xp"]       += gain
    data["total_xp"]  = data.get("total_xp", 0) + gain

    leveled = False
    while data["xp"] >= _xp_needed(data["level"]):
        data["xp"]   -= _xp_needed(data["level"])
        data["level"] += 1
        leveled = True
    _save_xp()

    if leveled:
        embed = discord.Embed(
            title="🎉 Новый уровень!",
            description=f"{message.author.mention} достиг **{data['level']} уровня**!",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=message.author.display_avatar.url)
        await message.channel.send(embed=embed)
    return leveled


async def cmd_rank(ctx):
    data  = get_user(ctx.guild.id, ctx.author.id)
    level = data["level"]
    xp    = data["xp"]
    need  = _xp_needed(level)
    pct   = min(xp / need, 1.0)
    bar   = "█" * int(pct * 20) + "░" * (20 - int(pct * 20))
    embed = discord.Embed(title=f"⭐ {ctx.author.display_name}", color=discord.Color.gold())
    embed.add_field(name="🏆 Уровень",  value=f"**{level}**",              inline=True)
    embed.add_field(name="✨ XP",       value=f"{xp} / {need}",            inline=True)
    embed.add_field(name="📊 Всего XP", value=str(data.get("total_xp",0)), inline=True)
    embed.add_field(name="📈 Прогресс", value=f"`{bar}` {int(pct*100)}%",  inline=False)
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)


async def cmd_leaderboard(ctx):
    gid = str(ctx.guild.id)
    if gid not in _xp_data or not _xp_data[gid]:
        await ctx.send("📭 Пока нет данных.")
        return
    users = []
    for uid, d in _xp_data[gid].items():
        m = ctx.guild.get_member(int(uid))
        name = m.display_name if m else "Участник"
        users.append((name, d["level"], d.get("total_xp", d["xp"])))
    users.sort(key=lambda x: (x[1], x[2]), reverse=True)
    medals = ["🥇","🥈","🥉"] + ["🏅"]*7
    lines  = [f"{medals[i]} **{n}** — {l} ур. ({x} XP)" for i,(n,l,x) in enumerate(users[:10])]
    embed  = discord.Embed(title=f"🏆 Топ — {ctx.guild.name}", description="\n".join(lines), color=discord.Color.gold())
    await ctx.send(embed=embed)


# ════════════════════════════════════════════════
#  👋 ПРИВЕТСТВИЯ
# ════════════════════════════════════════════════

WELCOME_CHANNEL = os.getenv("WELCOME_CHANNEL", "общее")
WELCOMES = [
    "Добро пожаловать, {name}! Рады тебя видеть! 🎉",
    "О, {name} присоединился! Привет! 👋",
    "{name} теперь с нами! Надеюсь понравится! 😊",
    "Встречаем {name}! Ты {count}-й участник! 🥳",
]


async def welcome_member(member: discord.Member, say_func=None):
    guild = member.guild
    ch = discord.utils.get(guild.text_channels, name=WELCOME_CHANNEL)
    if not ch:
        for c in guild.text_channels:
            if c.permissions_for(guild.me).send_messages:
                ch = c
                break
    if not ch:
        return
    text = random.choice(WELCOMES).format(name=member.display_name, count=guild.member_count)
    embed = discord.Embed(title="👋 Новый участник!", description=f"{member.mention}\n{text}", color=discord.Color.green())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"Участников: {guild.member_count}")
    await ch.send(embed=embed)
    if say_func and guild.voice_client and guild.voice_client.is_connected():
        await say_func(guild.id, f"Добро пожаловать, {member.display_name}!")


# ════════════════════════════════════════════════
#  ⚔️ ТЕКСТОВАЯ RPG
# ════════════════════════════════════════════════

rpg_sessions: dict[int, dict] = {}

RPG_SYSTEM_PROMPT = """Ты — Мастер текстовой RPG игры в Discord. Ведёшь интерактивное фэнтези-приключение.

Правила:
- Описывай сцены ярко и увлекательно, но КОРОТКО (3-5 предложений)
- Всегда предлагай 3 варианта действий в конце (пронумерованных)
- Следи за состоянием персонажа: HP, золото, инвентарь
- Делай события интересными: сражения, загадки, торговцы, ловушки
- Реагируй на выбор игрока логично
- Если HP упало до 0 — красиво заверши игру
- Пиши на русском языке
- Формат ответа строго:
  [описание сцены]
  
  ❤️ HP: X/20 | 💰 Золото: X
  
  Что делаешь?
  1️⃣ [вариант]
  2️⃣ [вариант]
  3️⃣ [вариант]"""


async def cmd_rpg(ctx, *, action: str = "", bot_name: str = "Алиса"):
    from ai_handler import get_response
    user_id = ctx.author.id

    if not action or action.lower() in ["старт", "start", "новая", "new", "начать"]:
        rpg_sessions[user_id] = {"history": [], "hp": 20, "gold": 10}
        prompt = (f"Начни RPG для {ctx.author.display_name}. "
                  f"Интересное вступление, герой на распутье, представь мир.")
        async with ctx.typing():
            reply = await get_response(prompt, [], bot_name, system_override=RPG_SYSTEM_PROMPT)
        rpg_sessions[user_id]["history"].append({"role": "assistant", "content": reply})
        embed = discord.Embed(title="⚔️ Новое приключение!", description=reply, color=discord.Color.dark_gold())
        embed.set_footer(text="!rpg [действие] — играть | !rpg стоп — выйти")
        await ctx.send(embed=embed)
        return

    if action.lower() in ["стоп", "stop", "конец", "выход"]:
        rpg_sessions.pop(user_id, None)
        await ctx.send("📖 Приключение завершено! `!rpg` — начать новое.")
        return

    if user_id not in rpg_sessions:
        await ctx.send("❌ Нет активного приключения. Напиши `!rpg` чтобы начать!")
        return

    session = rpg_sessions[user_id]
    session["history"].append({"role": "user", "content": action})
    async with ctx.typing():
        reply = await get_response(action, session["history"], bot_name, system_override=RPG_SYSTEM_PROMPT)
    session["history"].append({"role": "assistant", "content": reply})
    if len(session["history"]) > 20:
        session["history"] = session["history"][-20:]

    ended = any(w in reply.lower() for w in ["герой пал", "game over", "приключение окончено", "ты погиб"])
    embed = discord.Embed(
        title="⚔️ Приключение" if not ended else "💀 Игра окончена",
        description=reply,
        color=discord.Color.dark_gold() if not ended else discord.Color.dark_red()
    )
    embed.set_footer(text=f"{ctx.author.display_name} · !rpg [действие] · !rpg стоп")
    await ctx.send(embed=embed)
    if ended:
        rpg_sessions.pop(user_id, None)


_load_xp()
