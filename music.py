"""
🎵 Музыкальный модуль — SoundCloud, YouTube, плейлисты

Поддерживает:
  - Одиночные треки
  - Плейлисты (SoundCloud/YouTube) — все треки добавляются в очередь
  - Поиск по названию: !play название песни
"""

import asyncio
import logging
from dataclasses import dataclass
from collections import deque

import discord

log = logging.getLogger(__name__)

YTDL_OPTIONS = {
    "format":         "bestaudio/best",
    "quiet":          True,
    "no_warnings":    True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
    "noplaylist":     True,
}

YTDL_PLAYLIST_OPTIONS = {
    "format":         "bestaudio/best",
    "quiet":          True,
    "no_warnings":    True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
    "noplaylist":     False,
    "playlistend":    50,
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options":        "-vn",
}


@dataclass
class Track:
    url:      str
    stream:   str
    title:    str
    duration: int
    uploader: str


queues:  dict[int, deque] = {}
current: dict[int, object] = {}


def get_queue(guild_id: int) -> deque:
    if guild_id not in queues:
        queues[guild_id] = deque()
    return queues[guild_id]


def fmt_duration(seconds: int) -> str:
    if not seconds:
        return "--:--"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


async def fetch_tracks(url: str) -> list:
    import yt_dlp
    is_playlist = any(x in url for x in ["playlist", "/sets/", "list="])
    opts = dict(YTDL_PLAYLIST_OPTIONS if is_playlist else YTDL_OPTIONS)
    loop = asyncio.get_event_loop()

    def _extract():
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    info = await loop.run_in_executor(None, _extract)
    tracks = []

    if "entries" in info:
        for entry in info["entries"]:
            if entry and entry.get("url"):
                tracks.append(Track(
                    url=entry.get("webpage_url", url),
                    stream=entry["url"],
                    title=entry.get("title", "Неизвестно"),
                    duration=entry.get("duration", 0),
                    uploader=entry.get("uploader", ""),
                ))
    else:
        tracks.append(Track(
            url=info.get("webpage_url", url),
            stream=info["url"],
            title=info.get("title", "Неизвестно"),
            duration=info.get("duration", 0),
            uploader=info.get("uploader", ""),
        ))

    return tracks


async def play_next(guild: discord.Guild, text_channel=None):
    queue = get_queue(guild.id)
    if not queue:
        current[guild.id] = None
        if text_channel:
            await text_channel.send("✅ Очередь закончилась!")
        return
    if not guild.voice_client or not guild.voice_client.is_connected():
        return

    track = queue.popleft()
    current[guild.id] = track
    source = discord.PCMVolumeTransformer(
        discord.FFmpegPCMAudio(track.stream, **FFMPEG_OPTIONS), volume=0.7
    )

    def after(error):
        if error:
            log.error(f"Воспроизведение: {error}")
        asyncio.run_coroutine_threadsafe(
            play_next(guild, text_channel), guild._state.loop
        )

    guild.voice_client.play(source, after=after)

    if text_channel:
        embed = discord.Embed(
            title="▶️ Сейчас играет",
            description=f"**{track.title}**",
            color=discord.Color.green()
        )
        embed.add_field(name="👤", value=track.uploader or "—", inline=True)
        embed.add_field(name="⏱️", value=fmt_duration(track.duration), inline=True)
        if queue:
            embed.add_field(name="📋 В очереди", value=f"{len(queue)} треков", inline=True)
        await text_channel.send(embed=embed)


async def cmd_play(ctx, url: str):
    if not ctx.author.voice:
        await ctx.send("❌ Зайди в голосовой канал!")
        return
    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()
    elif ctx.voice_client.channel != ctx.author.voice.channel:
        await ctx.voice_client.move_to(ctx.author.voice.channel)

    msg = await ctx.send("🔍 Ищу...")
    try:
        tracks = await fetch_tracks(url)
    except Exception as e:
        log.error(f"fetch_tracks: {e}")
        await msg.edit(content="❌ Не удалось загрузить. Проверь ссылку!")
        return

    if not tracks:
        await msg.edit(content="❌ Треки не найдены.")
        return

    queue = get_queue(ctx.guild.id)
    playing = ctx.voice_client.is_playing() or ctx.voice_client.is_paused()

    if len(tracks) == 1:
        t = tracks[0]
        if playing:
            queue.append(t)
            await msg.edit(content=f"➕ В очередь: **{t.title}** ({fmt_duration(t.duration)}) | Позиция: {len(queue)}")
        else:
            await msg.delete()
            queue.appendleft(t)
            await play_next(ctx.guild, ctx.channel)
    else:
        for t in tracks:
            queue.append(t)
        total = sum(t.duration for t in tracks)
        embed = discord.Embed(title="📋 Плейлист добавлен в очередь", color=discord.Color.blue())
        embed.add_field(name="🎵 Треков",       value=str(len(tracks)),        inline=True)
        embed.add_field(name="⏱️ Длительность", value=fmt_duration(total),     inline=True)
        embed.add_field(name="📌 Первый трек",  value=tracks[0].title[:60],    inline=False)
        await msg.delete()
        await ctx.send(embed=embed)
        if not playing:
            await play_next(ctx.guild, ctx.channel)


async def cmd_skip(ctx):
    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await ctx.send("❌ Сейчас ничего не играет.")
        return
    ctx.voice_client.stop()
    await ctx.send("⏭️ Пропущено!")


async def cmd_stop_music(ctx):
    if ctx.voice_client:
        get_queue(ctx.guild.id).clear()
        current[ctx.guild.id] = None
        ctx.voice_client.stop()
    await ctx.send("⏹️ Стоп. Очередь очищена.")


async def cmd_pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Пауза.")
    else:
        await ctx.send("❌ Сейчас ничего не играет.")


async def cmd_resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Продолжаю!")
    else:
        await ctx.send("❌ Нечего продолжать.")


async def cmd_queue(ctx):
    queue = get_queue(ctx.guild.id)
    cur   = current.get(ctx.guild.id)
    if not cur and not queue:
        await ctx.send("📭 Очередь пуста.")
        return
    lines = []
    if cur:
        lines.append(f"▶️ **{cur.title}** ({fmt_duration(cur.duration)})")
    for i, t in enumerate(list(queue)[:10], 1):
        lines.append(f"`{i}.` {t.title} ({fmt_duration(t.duration)})")
    if len(queue) > 10:
        lines.append(f"*...и ещё {len(queue)-10} треков*")
    total = sum(t.duration for t in queue) + (cur.duration if cur else 0)
    embed = discord.Embed(title="🎵 Очередь", description="\n".join(lines), color=discord.Color.purple())
    embed.set_footer(text=f"Треков: {len(queue)+(1 if cur else 0)} • {fmt_duration(total)}")
    await ctx.send(embed=embed)


async def cmd_volume(ctx, vol: int):
    if not ctx.voice_client or not ctx.voice_client.source:
        await ctx.send("❌ Сейчас ничего не играет.")
        return
    if not 0 <= vol <= 100:
        await ctx.send("❌ Громкость: 0-100.")
        return
    ctx.voice_client.source.volume = vol / 100
    await ctx.send(f"🔊 Громкость: **{vol}%**")


async def cmd_nowplaying(ctx):
    cur = current.get(ctx.guild.id)
    if not cur:
        await ctx.send("❌ Сейчас ничего не играет.")
        return
    embed = discord.Embed(title="🎵 Сейчас играет", description=f"**{cur.title}**", color=discord.Color.green())
    embed.add_field(name="👤", value=cur.uploader or "—", inline=True)
    embed.add_field(name="⏱️", value=fmt_duration(cur.duration), inline=True)
    embed.add_field(name="🔗 Ссылка", value=cur.url, inline=False)
    await ctx.send(embed=embed)
