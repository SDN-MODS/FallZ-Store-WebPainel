import discord
from discord.ui import View, Select, button
from services.coin_service import get_active_coin_packages, process_coin_purchase
from services.user_service import get_user_balance
from bot.utils import build_embed_from_db

class CoinPackageSelect(Select):
    def __init__(self, packages):
        options = []
        for pkg in packages:
            bonus_str = f" (+{pkg.bonus_coins} Bônus)" if pkg.bonus_coins > 0 else ""
            options.append(discord.SelectOption(
                label=f"{pkg.title} — R$ {pkg.price_brl:.2f}",
                value=pkg.id,
                description=f"Receba {pkg.coins + pkg.bonus_coins} Coins{bonus_str}",
                emoji="🪙"
            ))
        super().__init__(placeholder="Escolha um pacote de Coins...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        pkg_id = self.values[0]
        user_id = str(interaction.user.id)

        ok, msg = process_coin_purchase(user_id, pkg_id)
        balance = get_user_balance(user_id)

        embed = discord.Embed(
            title="✅ COMPRA DE COINS CONFIRMADA!" if ok else "❌ ERRO NA COMPRA",
            description=msg,
            color=discord.Color.green() if ok else discord.Color.red()
        )
        embed.add_field(name="🪙 Saldo Atualizado", value=f"**{balance} Coins**")
        await interaction.response.edit_message(embed=embed, view=None)

class CoinStoreView(View):
    def __init__(self):
        super().__init__(timeout=180)
        packages = get_active_coin_packages()
        if packages:
            self.add_item(CoinPackageSelect(packages))

    def get_embed(self):
        return build_embed_from_db('coin_store')

    @button(label="◀️ Voltar ao Menu Principal", style=discord.ButtonStyle.secondary, row=1)
    async def btn_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        from bot.views.main_menu import MainMenuView, build_main_embed
        view = MainMenuView()
        embed = build_main_embed(interaction.user.name, str(interaction.user.display_avatar.url))
        await interaction.response.edit_message(embed=embed, view=view)
