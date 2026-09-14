import discord
from discord.ui import View, button
from services.order_service import get_user_orders
from bot.utils import build_embed_from_db

class MyOrdersView(View):
    def __init__(self, user_id: str):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.orders = get_user_orders(user_id)

    def get_embed(self):
        embed = build_embed_from_db('order_list')

        if not self.orders:
            embed.description = f"{embed.description}\n\n*Você ainda não fez nenhum pedido na loja.*"
            return embed

        for order in self.orders[:10]:
            items_str = ", ".join([f"{item.quantity}x {item.product.name if item.product else 'Produto'}" for item in order.items])
            status_emoji = {
                "Aguardando processamento": "🟡",
                "Processando": "🔵",
                "Entregue": "🟢",
                "Cancelado": "🔴"
            }.get(order.status, "⚪")

            embed.add_field(
                name=f"{status_emoji} Pedido #{order.order_number} — {order.status}",
                value=f"**Itens:** {items_str}\n"
                      f"**Valor:** {order.total_coins} Coins\n"
                      f"**Data:** {order.created_at.strftime('%d/%m/%Y %H:%M')}",
                inline=False
            )

        return embed

    @button(label="◀️ Voltar ao Menu Principal", style=discord.ButtonStyle.secondary, row=1)
    async def btn_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        from bot.views.main_menu import MainMenuView, build_main_embed
        view = MainMenuView()
        embed = build_main_embed(interaction.user.name, str(interaction.user.display_avatar.url))
        await interaction.response.edit_message(embed=embed, view=view)
