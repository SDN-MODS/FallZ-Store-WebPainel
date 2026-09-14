import discord
from discord.ui import View, Select, Modal, TextInput
from services.ticket_service import create_ticket, get_user_tickets
from bot.utils import build_embed_from_db

class TicketModal(Modal, title="🎫 ABRIR TICKET DE SUPORTE"):
    subject_input = TextInput(
        label="Assunto",
        placeholder="Descreva brevemente o problema",
        required=True,
        max_length=100
    )
    message_input = TextInput(
        label="Detalhamento",
        placeholder="Descreva em detalhes o seu problema ou dúvida...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    def __init__(self, category: str):
        super().__init__()
        self.category = category

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        subject = self.subject_input.value
        message = self.message_input.value

        ok, msg, ticket_id = create_ticket(user_id, self.category, subject, message)

        embed = discord.Embed(
            title="🎫 SUPORTE — TICKET CRIADO" if ok else "❌ ERRO AO ABRIR TICKET",
            description=msg,
            color=discord.Color.green() if ok else discord.Color.red()
        )
        if ok:
            embed.add_field(name="Categoria", value=self.category, inline=True)
            embed.add_field(name="Assunto", value=subject, inline=True)
            embed.set_footer(text="Nossa equipe de suporte responderá em breve!")

        await interaction.response.send_message(embed=embed, ephemeral=True)


class TicketCategorySelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Problema com Coins", value="Problema com Coins", emoji="🪙"),
            discord.SelectOption(label="Problema com Pagamento", value="Problema com Pagamento", emoji="💳"),
            discord.SelectOption(label="Problema com Pedido", value="Problema com Pedido", emoji="📦"),
            discord.SelectOption(label="Problema com Entrega", value="Problema com Entrega", emoji="🚚"),
            discord.SelectOption(label="Outros Assuntos", value="Outros Assuntos", emoji="❓"),
        ]
        super().__init__(placeholder="Selecione o tipo de problema...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        await interaction.response.send_modal(TicketModal(category))


class TicketCategoryView(View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(TicketCategorySelect())

    def get_embed(self):
        return build_embed_from_db('ticket_support')

    @button(label="◀️ Voltar ao Menu Principal", style=discord.ButtonStyle.secondary, row=1)
    async def btn_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        from bot.views.main_menu import MainMenuView, build_main_embed
        view = MainMenuView()
        embed = build_main_embed(interaction.user.name, str(interaction.user.display_avatar.url))
        await interaction.response.edit_message(embed=embed, view=view)
