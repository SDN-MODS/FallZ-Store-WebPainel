import discord
from discord.ui import Modal, TextInput
from services.coupon_service import apply_coupon

class CouponModal(Modal, title="🎁 RESGATAR CUPOM PROMOCIONAL"):
    code_input = TextInput(
        label="Código do Cupom",
        placeholder="Digite seu código promocional (ex: BENVINDO)",
        required=True,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        code = self.code_input.value.strip()

        ok, msg = apply_coupon(user_id, code)

        embed = discord.Embed(
            title="🎁 RESGATE DE CUPOM",
            description=msg,
            color=discord.Color.green() if ok else discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
