import discord
from discord.ui import View, Select, button
from services.store_service import get_active_categories, get_products_by_category, get_product_by_id
from services.user_service import get_user_balance
from services.order_service import create_order

class CategorySelect(Select):
    def __init__(self, categories):
        options = [
            discord.SelectOption(
                label=cat.name,
                value=cat.id,
                description=cat.description or "Ver produtos desta categoria",
                emoji="📁"
            ) for cat in categories
        ]
        super().__init__(placeholder="Selecione uma Categoria...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        cat_id = self.values[0]
        view = ProductSelectView(cat_id)
        embed = view.get_embed()
        await interaction.response.edit_message(embed=embed, view=view)


class CategorySelectView(View):
    def __init__(self):
        super().__init__(timeout=180)
        categories = get_active_categories()
        if categories:
            self.add_item(CategorySelect(categories))

    def get_embed(self):
        embed = discord.Embed(
            title="🛒 LOJA — CATEGORIAS DISPONÍVEIS",
            description="Selecione a categoria desejada no menu suspenso abaixo para ver os itens.",
            color=discord.Color.blue()
        )
        return embed


class ProductSelect(Select):
    def __init__(self, products):
        options = []
        for prod in products:
            stock_str = "Infinito" if prod.stock == -1 else f"{prod.stock} un"
            options.append(discord.SelectOption(
                label=f"{prod.name} — {prod.price_coins} Coins",
                value=prod.id,
                description=f"Estoque: {stock_str} | {prod.description[:50] if prod.description else ''}",
                emoji="📦"
            ))
        super().__init__(placeholder="Selecione um Produto...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        product_id = self.values[0]
        view = ProductDetailView(product_id, str(interaction.user.id))
        embed = view.get_embed()
        await interaction.response.edit_message(embed=embed, view=view)


class ProductSelectView(View):
    def __init__(self, category_id: str):
        super().__init__(timeout=180)
        products = get_products_by_category(category_id)
        if products:
            self.add_item(ProductSelect(products))

    def get_embed(self):
        embed = discord.Embed(
            title="🛒 LOJA — SELEÇÃO DE PRODUTO",
            description="Escolha um produto da lista abaixo para conferir os detalhes e realizar a compra.",
            color=discord.Color.blue()
        )
        return embed


class ProductDetailView(View):
    def __init__(self, product_id: str, user_id: str):
        super().__init__(timeout=180)
        self.product_id = product_id
        self.user_id = user_id
        self.product = get_product_by_id(product_id)

    def get_embed(self):
        if not self.product:
            return discord.Embed(title="Erro", description="Produto não encontrado.", color=discord.Color.red())

        user_coins = get_user_balance(self.user_id)
        stock_str = "Infinito" if self.product.stock == -1 else f"{self.product.stock} unidades"

        embed = discord.Embed(
            title=f"📦 {self.product.name}",
            description=self.product.description or "Sem descrição.",
            color=discord.Color.purple()
        )
        embed.add_field(name="💰 Preço", value=f"**{self.product.price_coins} Coins**", inline=True)
        embed.add_field(name="📊 Estoque", value=stock_str, inline=True)
        embed.add_field(name="🪙 Seu Saldo Atual", value=f"**{user_coins} Coins**", inline=False)

        coins_after = user_coins - self.product.price_coins
        if coins_after >= 0:
            embed.add_field(name="➡️ Saldo Após a Compra", value=f"**{coins_after} Coins**", inline=False)
        else:
            embed.add_field(name="⚠️ Atenção", value=f"Saldo insuficiente! Faltam **{abs(coins_after)} Coins**.", inline=False)

        if self.product.image_url and self.product.image_url.startswith("http"):
            embed.set_thumbnail(url=self.product.image_url)

        return embed

    @button(label="✅ Confirmar Compra", style=discord.ButtonStyle.success)
    async def btn_confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        user_coins = get_user_balance(user_id)

        if not self.product:
            await interaction.response.send_message("Produto indisponível.", ephemeral=True)
            return

        if user_coins < self.product.price_coins:
            embed_err = discord.Embed(
                title="❌ SALDO INSUFICIENTE",
                description=f"Você precisa de **{self.product.price_coins} Coins** mas possui apenas **{user_coins} Coins**.\n\n"
                            "Não é possível pagar diretamente em dinheiro. Adquira mais Coins primeiro!",
                color=discord.Color.red()
            )
            # Render Buy Coins view directly
            from bot.views.coin_view import CoinStoreView
            coin_view = CoinStoreView()
            await interaction.response.edit_message(embed=embed_err, view=coin_view)
            return

        # Execute purchase
        ok, msg, order_id = create_order(user_id, [{'product_id': self.product.id, 'quantity': 1}])

        if ok:
            new_balance = get_user_balance(user_id)
            embed_success = discord.Embed(
                title="🎉 COMPRA REALIZADA COM SUCESSO!",
                description=f"Seu pedido para **{self.product.name}** foi registrado com status **🟡 Aguardando processamento**.",
                color=discord.Color.green()
            )
            embed_success.add_field(name="🪙 Coins Descontadas", value=f"-{self.product.price_coins} Coins")
            embed_success.add_field(name="💰 Novo Saldo", value=f"{new_balance} Coins")
            embed_success.set_footer(text="Nossa equipe entregará seu item no servidor em breve!")
            await interaction.response.edit_message(embed=embed_success, view=None)
        else:
            await interaction.response.send_message(f"❌ Falha no pedido: {msg}", ephemeral=True)

    @button(label="🪙 Comprar Coins", style=discord.ButtonStyle.secondary)
    async def btn_get_coins(self, interaction: discord.Interaction, button: discord.ui.Button):
        from bot.views.coin_view import CoinStoreView
        view = CoinStoreView()
        embed = view.get_embed()
        await interaction.response.edit_message(embed=embed, view=view)
