import discord
from discord.ui import View, Select, button
from services.coin_service import get_active_coin_packages, process_coin_purchase
from services.user_service import get_user_balance

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

        # Confirm purchase simulation
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
        embed = discord.Embed(
            title="🪙 ADQUIRIR COINS — MOEDA VIRTUAL",
            description="Escolha um dos pacotes abaixo para recarregar seu saldo de Coins instantaneamente!\n\n"
                        "**Exemplos de Pacotes:**\n"
                        "• 100 Coins = R$ 10,00\n"
                        "• 250 Coins (+10) = R$ 25,00\n"
                        "• 500 Coins (+30) = R$ 50,00\n"
                        "• 1.000 Coins (+100) = R$ 95,00\n"
                        "• 2.500 Coins (+300) = R$ 220,00",
            color=discord.Color.gold()
        )
        embed.set_footer(text="Ao selecionar um pacote, o pagamento é processado e as coins entram no seu saldo.")
        return embed
