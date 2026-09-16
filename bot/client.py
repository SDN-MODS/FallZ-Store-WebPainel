import os
import discord
from discord.ext import commands
from bot.views.main_menu import MainMenuView, build_main_embed

import datetime
from discord.ext import tasks
from database.db import SessionLocal
from database.models import Coupon

class CouponRedeemButton(discord.ui.Button):
    def __init__(self, coupon_code: str):
        super().__init__(label="🎁 Resgatar Cupom Agora!", style=discord.ButtonStyle.success, custom_id=f"btn_redeem_coupon_{coupon_code}")
        self.coupon_code = coupon_code

    async def callback(self, interaction: discord.Interaction):
        from services.coupon_service import apply_coupon
        user_id = str(interaction.user.id)
        ok, msg = apply_coupon(user_id, self.coupon_code)
        await interaction.response.send_message(msg, ephemeral=True)

class CouponBroadcastView(discord.ui.View):
    def __init__(self, coupon_code: str):
        super().__init__(timeout=None)
        self.add_item(CouponRedeemButton(coupon_code))

class DayZStoreBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(MainMenuView())
        self.coupon_broadcast_loop.start()
        print("✓ Visões persistentes e Tarefa de Envio Automático de Cupons registradas!")

    async def on_ready(self):
        print(f"✓ Bot conectado como {self.user} (ID: {self.user.id})")

    @tasks.loop(seconds=60)
    async def coupon_broadcast_loop(self):
        session = SessionLocal()
        try:
            now_brt = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
            coupons = session.query(Coupon).filter_by(active=True).all()

            for c in coupons:
                if not c.channel_id or not c.interval_minutes or c.interval_minutes <= 0:
                    continue

                if c.start_time and now_brt < c.start_time:
                    continue

                if c.expires_at and now_brt > c.expires_at:
                    continue

                if c.max_uses != -1 and c.used_count >= c.max_uses:
                    continue

                if c.last_sent_at:
                    elapsed = (now_brt - c.last_sent_at).total_seconds() / 60.0
                    if elapsed < c.interval_minutes:
                        continue

                channel = self.get_channel(int(c.channel_id))
                if channel:
                    uses_str = f"{c.max_uses - c.used_count} resgates restantes" if c.max_uses != -1 else "Resgates ilimitados"
                    embed = discord.Embed(
                        title=f"🎁 CUPOM DISPONÍVEL: {c.code}",
                        description=f"Um novo cupom promocional está ativo no servidor!\n\n"
                                    f"• **Código:** `{c.code}`\n"
                                    f"• **Benefício:** {c.value} ({c.type})\n"
                                    f"• **Disponibilidade:** **{uses_str}**\n\n"
                                    f"Clique no botão abaixo para resgatar instantaneamente no seu saldo!",
                        color=discord.Color.gold()
                    )
                    embed.set_footer(text="Aproveite antes que os resgates se esgotem!")
                    view = CouponBroadcastView(c.code)
                    await channel.send(embed=embed, view=view)

                    c.last_sent_at = now_brt
                    session.commit()
        except Exception as e:
            session.rollback()
        finally:
            session.close()

def setup_bot_channel_message():
    """Utility function to create or build the main store panel embed and view."""
    view = MainMenuView()
    embed = build_main_embed("DayZ Store")
    return embed, view
