import json
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

    if tpl.fields_json:
        try:
            fields = json.loads(tpl.fields_json)
            for f in fields:
                if isinstance(f, dict) and f.get("name") and f.get("value"):
                    embed.add_field(
                        name=f.get("name"),
                        value=f.get("value"),
                        inline=f.get("inline", True)
                    )
        except Exception as e:
            print(f"Erro ao carregar fields_json de {key}: {e}")

    if tpl.footer_text:
        embed.set_footer(text=tpl.footer_text)

    if tpl.thumbnail_url and tpl.thumbnail_url.startswith("http"):
        embed.set_thumbnail(url=tpl.thumbnail_url)

    if tpl.image_url and tpl.image_url.startswith("http"):
        embed.set_image(url=tpl.image_url)

    return embed
