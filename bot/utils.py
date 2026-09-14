import discord
from services.embed_service import get_embed_template

def hex_to_discord_color(hex_str: str) -> discord.Color:
    try:
        hex_clean = hex_str.lstrip('#')
        return discord.Color(int(hex_clean, 16))
    except Exception:
        return discord.Color.gold()

def build_embed_from_db(key: str) -> discord.Embed:
    tpl = get_embed_template(key)
    color = hex_to_discord_color(tpl.color)

    embed = discord.Embed(
        title=tpl.title,
        description=tpl.description,
        color=color
    )

    if tpl.footer_text:
        embed.set_footer(text=tpl.footer_text)

    if tpl.thumbnail_url and tpl.thumbnail_url.startswith("http"):
        embed.set_thumbnail(url=tpl.thumbnail_url)

    if tpl.image_url and tpl.image_url.startswith("http"):
        embed.set_image(url=tpl.image_url)

    return embed
