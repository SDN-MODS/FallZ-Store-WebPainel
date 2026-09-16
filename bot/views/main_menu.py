import discord
from discord.ui import View, Modal, TextInput, button
from services.user_service import get_or_create_user, is_user_registered, register_user, get_user_balance
from services.coin_service import get_user_coin_transactions
from bot.utils import build_embed_from_db
from bot.views.coin_view import CoinStoreView
from bot.views.store_view import CategorySelectView
from bot.views.order_view import MyOrdersView
from bot.views.ticket_view import TicketCategoryView

class RegistrationModal(Modal, title="📝 CADASTRO DE JOGADOR DAYZ"):
    full_name_input = TextInput(
        label="Nome Completo",
        placeholder="Digite seu nome completo",
        required=True,
        max_length=100
    )
    nick_input = TextInput(
        label="Nick de Jogo no DayZ",
        placeholder="Digite seu nick idêntico ao jogo",
        required=True,
        max_length=50
    )
    steam_id_input = TextInput(
        label="Steam ID 64",
        placeholder="Ex: 76561198000000000",
        required=True,
        max_length=20
    )

    def __init__(self, action_type: str = "store"):
        super().__init__()
        self.action_type = action_type

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        username = interaction.user.name
        avatar = str(interaction.user.display_avatar.url)

        ok, msg = register_user(
            user_id, username,
            self.full_name_input.value,
            self.nick_input.value,
            self.steam_id_input.value,
            interaction.user.discriminator or "0",
            avatar
        )

        if ok:
            embed = build_embed_from_db('registration_prompt')
            embed.description = f"{embed.description}\n\n{msg}"
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ {msg}", ephemeral=True)


async def check_registration_or_prompt(interaction: discord.Interaction) -> bool:
    user_id = str(interaction.user.id)
    get_or_create_user(user_id, interaction.user.name, interaction.user.discriminator or "0", str(interaction.user.display_avatar.url))

    if not is_user_registered(user_id):
        await interaction.response.send_modal(RegistrationModal())
        return False
    return True


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
        if not await check_registration_or_prompt(interaction):
            return
        view = CategorySelectView()
        embed = view.get_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @button(label="🛍️ Ver Carrinho", style=discord.ButtonStyle.primary, custom_id="btn_main_cart")
    async def btn_cart(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_registration_or_prompt(interaction):
            return
        user_id = str(interaction.user.id)
        from bot.views.cart_view import CartView
        view = CartView(user_id)
        embed = view.get_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @button(label="🪙 Comprar Coins", style=discord.ButtonStyle.success, custom_id="btn_main_buy_coins")
    async def btn_buy_coins(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_registration_or_prompt(interaction):
            return
        view = CoinStoreView()
        embed = view.get_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @button(label="💰 Meu Saldo", style=discord.ButtonStyle.secondary, custom_id="btn_main_balance")
    async def btn_balance(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_registration_or_prompt(interaction):
            return
        user_id = str(interaction.user.id)
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
        if not await check_registration_or_prompt(interaction):
            return
        user_id = str(interaction.user.id)
        view = MyOrdersView(user_id)
        embed = view.get_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @button(label="🎫 Suporte", style=discord.ButtonStyle.danger, custom_id="btn_main_support")
    async def btn_support(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_registration_or_prompt(interaction):
            return
        view = TicketCategoryView()
        embed = view.get_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
