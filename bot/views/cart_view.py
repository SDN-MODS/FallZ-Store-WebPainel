import discord
from discord.ui import View, button
from services.cart_service import get_cart_items, remove_from_cart, clear_cart, checkout_cart
from bot.utils import build_embed_from_db

class CartView(View):
    def __init__(self, user_id: str):
        super().__init__(timeout=180)
        self.user_id = user_id

    def get_embed(self):
        cart = get_cart_items(self.user_id)
        embed = build_embed_from_db('product_detail') # usa template de produto ou padrão
        embed.title = "🛒 SEU CARRINHO DE COMPRAS"
        embed.color = discord.Color.gold()

        items = cart["items"]
        total_coins = cart["total_coins"]
        user_coins = cart["user_coins"]

        if not items:
            embed.description = "Seu carrinho está **vazio**!\n\nNavegue pelas categorias e adicione os produtos desejados."
            embed.add_field(name="🪙 Seu Saldo Atual", value=f"**{user_coins} Coins**", inline=False)
            return embed

        cart_text = ""
        for idx, item in enumerate(items, 1):
            cart_text += f"**{idx}. {item['name']}**\n"
            cart_text += f"└ {item['quantity']}x @ {item['price_coins']} Coins = **{item['subtotal_coins']} Coins**\n"

        embed.description = f"Confira os itens selecionados:\n\n{cart_text}"
        embed.add_field(name="💰 Valor Total do Carrinho", value=f"**{total_coins} Coins**", inline=True)
        embed.add_field(name="🪙 Seu Saldo Atual", value=f"**{user_coins} Coins**", inline=True)

        coins_after = user_coins - total_coins
        if coins_after >= 0:
            embed.add_field(name="➡️ Saldo Após a Compra", value=f"**{coins_after} Coins**", inline=False)
        else:
            embed.add_field(name="⚠️ Saldo Insuficiente", value=f"Faltam **{abs(coins_after)} Coins** para concluir a compra.", inline=False)

        return embed

    @button(label="✅ Finalizar Compra", style=discord.ButtonStyle.success, row=0)
    async def btn_checkout(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        ok, msg = checkout_cart(user_id)
        if ok:
            embed_success = discord.Embed(
                title="🎉 COMPRA REALIZADA COM SUCESSO!",
                description=msg,
                color=discord.Color.green()
            )
            embed_success.set_footer(text="Acompanhe o status em 'Meus Pedidos'")
            await interaction.response.edit_message(embed=embed_success, view=None)
        else:
            await interaction.response.send_message(f"❌ {msg}", ephemeral=True)

    @button(label="🛍️ Continuar Comprando", style=discord.ButtonStyle.primary, row=0)
    async def btn_continue_shopping(self, interaction: discord.Interaction, button: discord.ui.Button):
        from bot.views.store_view import CategorySelectView
        view = CategorySelectView()
        embed = view.get_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    @button(label="🎟️ Aplicar Cupom de Desconto", style=discord.ButtonStyle.primary, row=1)
    async def btn_apply_coupon(self, interaction: discord.Interaction, button: discord.ui.Button):
        from bot.views.coupon_view import CouponModal
        await interaction.response.send_modal(CouponModal())

    @button(label="🧹 Limpar Carrinho", style=discord.ButtonStyle.secondary, row=1)
    async def btn_clear(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        clear_cart(user_id)
        embed = self.get_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @button(label="◀️ Voltar ao Menu Principal", style=discord.ButtonStyle.secondary, row=1)
    async def btn_back_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        from bot.views.main_menu import MainMenuView, build_main_embed
        view = MainMenuView()
        embed = build_main_embed(interaction.user.name, str(interaction.user.display_avatar.url))
        await interaction.response.edit_message(embed=embed, view=view)
