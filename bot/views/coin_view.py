import discord
from discord.ui import View, Select, button
from services.coin_service import get_active_coin_packages, process_coin_purchase, get_coin_package_by_id
from services.user_service import get_user_balance
from bot.utils import build_embed_from_db

ESPACO_INVISIVEL = "\u3164"

class PromotionalUploadView(View):
    def __init__(self, transaction_id: str, package_name: str):
        super().__init__(timeout=180)
        self.transaction_id = transaction_id
        self.package_name = package_name

    @button(label=f"{ESPACO_INVISIVEL * 2}📤 Enviar Arquivo Promocional{ESPACO_INVISIVEL * 2}", style=discord.ButtonStyle.primary)
    async def btn_upload_file(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        try:
            thread_name = f"Entrega - {self.transaction_id[:8].upper()}"
            thread = await interaction.channel.create_thread(
                name=thread_name,
                type=discord.ChannelType.private_thread,
                invitable=False
            )

            from database.db import SessionLocal
            from database.models import StoreSettings
            session = SessionLocal()
            settings = session.query(StoreSettings).filter_by(id="default").first()
            session.close()

            admin_mention = ""
            if settings and settings.admin_role_id:
                admin_mention = f"<@&{settings.admin_role_id}> "

            await thread.add_user(interaction.user)

            msg = f"{interaction.user.mention} {admin_mention}\n" \
                  f"📦 **Resgate do Pacote:** {self.package_name}\n" \
                  f"🆔 **ID da Transação:** `{self.transaction_id}`\n\n" \
                  f"Por favor, envie o arquivo de imagem/comprovante ou os detalhes necessários nesta conversa para que a equipe possa personalizar a sua entrega."

            await thread.send(content=msg)
            await interaction.followup.send(f"✅ Conversa privada criada! Acesse aqui: {thread.mention}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send("❌ Não foi possível criar uma conversa privada neste canal. Por favor, abra um ticket manualmente em nosso canal de suporte.", ephemeral=True)

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

        ok, msg, transaction_id = process_coin_purchase(user_id, pkg_id)
        balance = get_user_balance(user_id)
        pkg = get_coin_package_by_id(pkg_id)

        embed = discord.Embed(
            title="✅ COMPRA DE COINS CONFIRMADA!" if ok else "❌ ERRO NA COMPRA",
            description=msg,
            color=discord.Color.green() if ok else discord.Color.red()
        )
        embed.add_field(name="🪙 Saldo Atualizado", value=f"**{balance} Coins**")

        view = None
        if ok and pkg and pkg.is_promotional and transaction_id:
            embed.description += f"\n\n🎁 **PACOTE PROMOCIONAL ATIVADO**\n{pkg.promotional_instructions}"
            embed.color = discord.Color.gold()
            view = PromotionalUploadView(transaction_id, pkg.title)

        await interaction.response.edit_message(embed=embed, view=view)

class CoinStoreView(View):
    def __init__(self):
        super().__init__(timeout=180)
        packages = get_active_coin_packages()
        if packages:
            self.add_item(CoinPackageSelect(packages))

    def get_embed(self):
        return build_embed_from_db('coin_store')

    # 2 botões na mesma linha (row=1) com tamanho e alinhamento ajustados
    @button(label=f"{ESPACO_INVISIVEL * 1}🎟️ Resgatar Cupom de Bônus de Coins{ESPACO_INVISIVEL * 1}", style=discord.ButtonStyle.success, row=1)
    async def btn_apply_coin_coupon(self, interaction: discord.Interaction, button: discord.ui.Button):
        from bot.views.coupon_view import CouponModal
        await interaction.response.send_modal(CouponModal())

    @button(label=f"{ESPACO_INVISIVEL * 4}◀️ Voltar ao Menu Principal.{ESPACO_INVISIVEL * 4}", style=discord.ButtonStyle.secondary, row=1)
    async def btn_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        from bot.views.main_menu import MainMenuView, build_main_embed
        view = MainMenuView()
        embed = build_main_embed(interaction.user.name, str(interaction.user.display_avatar.url))
        await interaction.response.edit_message(embed=embed, view=view)
