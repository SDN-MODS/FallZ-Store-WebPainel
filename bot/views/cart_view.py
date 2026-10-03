import discord
from discord.ui import View, button
from services.cart_service import get_cart_items, remove_from_cart, clear_cart, checkout_cart
from bot.utils import build_embed_from_db

ESPACO_INVISIVEL = "\u3164"

class CartView(View):
    def __init__(self, user_id: str):
        super().__init__(timeout=180)
        self.user_id = user_id

    def get_embed(self):
        cart = get_cart_items(self.user_id)
        embed = build_embed_from_db('shopping_cart')

        items = cart["items"]
        total_coins = cart["total_coins"]
        user_coins = cart["user_coins"]

        if not items:
            embed.description = f"{embed.description}\n\n⚠️ **Seu carrinho está vazio!**\nNavegue pelas categorias para adicionar produtos."
            embed.add_field(name="🪙 Seu Saldo Atual", value=f"**{user_coins} Coins**", inline=False)
            return embed

        cart_text = ""
        for idx, item in enumerate(items, 1):
            cart_text += f"**{idx}. {item['name']}**\n"
            cart_text += f"└ {item['quantity']}x @ {item['price_coins']} Coins = **{item['subtotal_coins']} Coins**\n"

        embed.description = f"{embed.description}\n\n📋 **Itens Selecionados:**\n{cart_text}"
        embed.add_field(name="💰 Valor Total do Carrinho", value=f"**{total_coins} Coins**", inline=True)
        embed.add_field(name="🪙 Seu Saldo Atual", value=f"**{user_coins} Coins**", inline=True)

        coins_after = user_coins - total_coins
        if coins_after >= 0:
            embed.add_field(name="➡️ Saldo Após a Compra", value=f"**{coins_after} Coins**", inline=False)
        else:
            embed.add_field(name="⚠️ Saldo Insuficiente", value=f"Faltam **{abs(coins_after)} Coins** para concluir a compra.", inline=False)

        return embed

    # 5 Botões: 3 em cima (row=0) e 2 embaixo (row=1)
    @button(label=f"{ESPACO_INVISIVEL * 4}✅ Finalizar Compra{ESPACO_INVISIVEL * 4}", style=discord.ButtonStyle.success, row=0)
    async def btn_checkout(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        ok, msg = checkout_cart(user_id)
        if ok:
            embed_success = build_embed_from_db('purchase_success')
            embed_success.description = f"{embed_success.description}\n\n{msg}"
            await interaction.response.edit_message(embed=embed_success, view=None)
        else:
            await interaction.response.send_message(f"❌ {msg}", ephemeral=True)

    @button(label=f"{ESPACO_INVISIVEL * 2}🛍️ Continuar Comprando{ESPACO_INVISIVEL * 2}", style=discord.ButtonStyle.primary, row=0)
    async def btn_continue_shopping(self, interaction: discord.Interaction, button: discord.ui.Button):
        from bot.views.store_view import CategorySelectView
        view = CategorySelectView()
        embed = view.get_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    @button(label=f"{ESPACO_INVISIVEL * 1}🎟️ Aplicar Cupom{ESPACO_INVISIVEL * 1}", style=discord.ButtonStyle.primary, row=0)
    async def btn_apply_coupon(self, interaction: discord.Interaction, button: discord.ui.Button):
        from bot.views.coupon_view import CouponModal
        await interaction.response.send_modal(CouponModal())

    @button(label=f"{ESPACO_INVISIVEL * 4}🧹 Limpar Carrinho.{ESPACO_INVISIVEL * 4}", style=discord.ButtonStyle.secondary, row=1)
    async def btn_clear(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        clear_cart(user_id)
        embed = self.get_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @button(label=f"{ESPACO_INVISIVEL * 2}◀️ Voltar ao Menu Principal{ESPACO_INVISIVEL * 2}", style=discord.ButtonStyle.secondary, row=1)
    async def btn_back_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        from bot.views.main_menu import MainMenuView, build_main_embed
        view = MainMenuView()
        embed = build_main_embed(interaction.user.name, str(interaction.user.display_avatar.url))
        await interaction.response.edit_message(embed=embed, view=view)
