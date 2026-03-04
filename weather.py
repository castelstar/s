"""
🌤️ Погода — Open-Meteo + Nominatim (100% БЕСПЛАТНО, без ключей, без блокировок)

Почему поменяли wttr.in:
  wttr.in иногда возвращает HTML вместо JSON и блокирует запросы.
  Open-Meteo — специализированный погодный API, никогда не блокирует.
  Nominatim — геокодер OpenStreetMap, находит любой город по-русски.
"""

import aiohttp
import logging
import discord

log = logging.getLogger(__name__)

WMO_CODES = {
    0:  ("☀️",  "Ясно"),
    1:  ("🌤️", "Преимущественно ясно"),
    2:  ("⛅",  "Переменная облачность"),
    3:  ("☁️",  "Пасмурно"),
    45: ("🌫️", "Туман"),
    48: ("🌫️", "Ледяной туман"),
    51: ("🌦️", "Слабая морось"),
    53: ("🌦️", "Морось"),
    55: ("🌧️", "Сильная морось"),
    61: ("🌧️", "Слабый дождь"),
    63: ("🌧️", "Дождь"),
    65: ("🌧️", "Сильный дождь"),
    71: ("🌨️", "Слабый снег"),
    73: ("❄️",  "Снег"),
    75: ("❄️",  "Сильный снег"),
    77: ("🌨️", "Снежная крупа"),
    80: ("🌦️", "Ливневый дождь"),
    81: ("🌧️", "Ливень"),
    82: ("⛈️",  "Сильный ливень"),
    85: ("🌨️", "Снегопад"),
    86: ("❄️",  "Сильный снегопад"),
    95: ("⛈️",  "Гроза"),
    96: ("⛈️",  "Гроза с градом"),
    99: ("⛈️",  "Сильная гроза с градом"),
}

WIND_DIRS = ["С", "ССВ", "СВ", "ВСВ", "В", "ВЮВ", "ЮВ", "ЮЮВ",
             "Ю", "ЮЮЗ", "ЮЗ", "ЗЮЗ", "З", "ЗСЗ", "СЗ", "ССЗ"]


def wind_dir(deg: float) -> str:
    return WIND_DIRS[round(deg / 22.5) % 16]


def temp_color(t: float) -> discord.Color:
    if t <= 0:  return discord.Color.blue()
    if t <= 10: return discord.Color.teal()
    if t <= 20: return discord.Color.green()
    if t <= 30: return discord.Color.orange()
    return discord.Color.red()


async def geocode(city: str) -> tuple[float, float, str] | None:
    """Найти координаты города через OpenStreetMap Nominatim"""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city, "format": "json", "limit": 1, "accept-language": "ru"}
    headers = {"User-Agent": "DiscordBot/2.0 (weather feature)"}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, params=params, headers=headers,
                             timeout=aiohttp.ClientTimeout(total=10)) as r:
                data = await r.json()
                if data:
                    return float(data[0]["lat"]), float(data[0]["lon"]), data[0]["display_name"].split(",")[0]
    except Exception as e:
        log.error(f"Geocode error: {e}")
    return None


async def fetch_weather(lat: float, lon: float) -> dict | None:
    """Получить погоду через Open-Meteo"""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,wind_direction_10m,weather_code,precipitation",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto", "forecast_days": 3,
    }
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status == 200:
                    return await r.json()
    except Exception as e:
        log.error(f"Weather fetch error: {e}")
    return None


async def cmd_weather(ctx, *, city: str = "", say_func=None):
    if not city:
        await ctx.send("Использование: `!погода [город]`\nПример: `!погода Москва`")
        return

    msg = await ctx.send(f"🔍 Ищу погоду в **{city}**...")

    geo = await geocode(city)
    if not geo:
        await msg.edit(content=f"❌ Город **{city}** не найден. Попробуй написать по-английски.")
        return

    lat, lon, place = geo
    data = await fetch_weather(lat, lon)
    if not data:
        await msg.edit(content="❌ Не удалось получить погоду, попробуй позже.")
        return

    cur  = data["current"]
    days = data["daily"]

    temp    = cur["temperature_2m"]
    feels   = cur["apparent_temperature"]
    humid   = cur["relative_humidity_2m"]
    wind_s  = cur["wind_speed_10m"]
    wind_d  = wind_dir(cur["wind_direction_10m"])
    precip  = cur["precipitation"]
    code    = cur["weather_code"]
    emoji, desc = WMO_CODES.get(code, ("🌡️", "Неизвестно"))

    # Прогноз на 3 дня
    day_names = ["Сегодня", "Завтра", "Послезавтра"]
    forecast  = []
    for i in range(3):
        d_code   = days["weather_code"][i]
        d_emoji, _ = WMO_CODES.get(d_code, ("🌡️", ""))
        d_max    = days["temperature_2m_max"][i]
        d_min    = days["temperature_2m_min"][i]
        d_rain   = days["precipitation_sum"][i]
        forecast.append(f"{day_names[i]}: {d_emoji} {d_min:.0f}°…{d_max:.0f}° 💧{d_rain:.1f}мм")

    embed = discord.Embed(
        title=f"{emoji} Погода — {place}",
        color=temp_color(temp)
    )
    embed.add_field(name="🌡️ Температура",  value=f"**{temp:.0f}°C** (ощущается {feels:.0f}°C)", inline=True)
    embed.add_field(name="💧 Влажность",    value=f"{humid}%",                                    inline=True)
    embed.add_field(name="💨 Ветер",        value=f"{wind_d} {wind_s:.0f} км/ч",                 inline=True)
    embed.add_field(name="🌧️ Осадки",      value=f"{precip} мм",                                inline=True)
    embed.add_field(name="☁️ Описание",     value=desc,                                           inline=True)
    embed.add_field(name="📅 Прогноз 3 дня", value="\n".join(forecast),                          inline=False)
    embed.set_footer(text="Open-Meteo · OpenStreetMap · Бесплатно")

    await msg.delete()
    await ctx.send(embed=embed)

    if say_func and ctx.voice_client and ctx.voice_client.is_connected():
        voice = (f"Погода в {place}. {desc}. "
                 f"Температура {temp:.0f} градусов, ощущается как {feels:.0f}. "
                 f"Ветер {wind_s:.0f} километров в час.")
        await say_func(ctx.guild.id, voice)
