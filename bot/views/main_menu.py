import discord
from discord.ui import View, button
from services.user_service import get_or_create_user, get_user_balance
from services.coin_service import get_user_coin_transactions
from bot.utils import build_embed_from_db
from bot.views.coin_view import CoinStoreView
from bot.views.store_view import CategorySelectView
from bot.views.order_view import MyOrdersView
from bot.views.coupon_view import CouponModal
from bot.views.ticket_view import TicketCategoryView

def build_main_embed(user_name: str = "DayZ Store", avatar_url: str = None):
    embed = build_embed_from_db('main_menu')
    if avatar_url and not embed.thumbnail:
        embed.set_thumbnail(url=avatar_url)
    return embed

class MainMenuView(View):
    def __init__(self):
        super().__init__(timeout=None) # Persistent view

    @button(label="🛒 Loja", style=discord.ButtonStyle.primary, custom_id="btn_main_store")
    async def btn_store(self, interaction: discord.Interaction, button: discord.ui.Button):
        get_or_create_user(str(interaction.user.id), interaction.user.name, interaction.user.discriminator or "0", str(interaction.user.display_avatar.url))
        view = CategorySelectView()
        embed = view.get_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @button(label="🛍️ Ver Carrinho", style=discord.ButtonStyle.primary, custom_id="btn_main_cart")
    async def btn_cart(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        get_or_create_user(user_id, interaction.user.name, interaction.user.discriminator or "0", str(interaction.user.display_avatar.url))
        from bot.views.cart_view import CartView
        view = CartView(user_id)
        embed = view.get_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @button(label="🪙 Comprar Coins", style=discord.ButtonStyle.success, custom_id="btn_main_buy_coins")
    async def btn_buy_coins(self, interaction: discord.Interaction, button: discord.ui.Button):
        get_or_create_user(str(interaction.user.id), interaction.user.name, interaction.user.discriminator or "0", str(interaction.user.display_avatar.url))
        view = CoinStoreView()
        embed = view.get_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @button(label="💰 Meu Saldo", style=discord.ButtonStyle.secondary, custom_id="btn_main_balance")
    async def btn_balance(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        get_or_create_user(user_id, interaction.user.name, interaction.user.discriminator or "0", str(interaction.user.display_avatar.url))
        balance = get_user_balance(user_id)
        transactions = get_user_coin_transactions(user_id)

        embed = build_embed_from_db('balance_info')
        embed.add_field(name="🪙 Saldo Atual", value=f"**{balance} Coins**", inline=False)

        if transactions:
            tx_history = ""
            for tx in transactions[:5]:
                tx_history += f"• `{tx.created_at.strftime('%d/%m %H:%M')}` — **{tx.coins:+} Coins** ({tx.description})\n"
            embed.add_field(name="📜 Últimas Movimentações", value=tx_history, inline=False)
        else:
            embed.add_field(name="📜 Últimas Movimentações", value="Nenhuma movimentação registrada ainda.", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @button(label="📦 Meus Pedidos", style=discord.ButtonStyle.secondary, custom_id="btn_main_orders")
    async def btn_orders(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        get_or_create_user(user_id, interaction.user.name, interaction.user.discriminator or "0", str(interaction.user.display_avatar.url))
        view = MyOrdersView(user_id)
        embed = view.get_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @button(label="🎁 Cupons", style=discord.ButtonStyle.secondary, custom_id="btn_main_coupons")
    async def btn_coupons(self, interaction: discord.Interaction, button: discord.ui.Button):
        get_or_create_user(str(interaction.user.id), interaction.user.name, interaction.user.discriminator or "0", str(interaction.user.display_avatar.url))
        await interaction.response.send_modal(CouponModal())

    @button(label="🎫 Suporte", style=discord.ButtonStyle.danger, custom_id="btn_main_support")
    async def btn_support(self, interaction: discord.Interaction, button: discord.ui.Button):
        get_or_create_user(str(interaction.user.id), interaction.user.name, interaction.user.discriminator or "0", str(interaction.user.display_avatar.url))
        view = TicketCategoryView()
        embed = view.get_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
