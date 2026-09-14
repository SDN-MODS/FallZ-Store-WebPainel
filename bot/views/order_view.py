import discord
from discord.ui import View
from services.order_service import get_user_orders

class MyOrdersView(View):
    def __init__(self, user_id: str):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.orders = get_user_orders(user_id)

    def get_embed(self):
        embed = discord.Embed(
            title="📦 MEUS PEDIDOS",
            color=discord.Color.gold()
        )

        if not self.orders:
            embed.description = "Você ainda não fez nenhum pedido na loja."
            return embed

        embed.description = "Confira abaixo o histórico de seus pedidos e o status de entrega:\n"

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
