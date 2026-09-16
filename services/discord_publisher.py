import json
import urllib.request
import urllib.error
from database.db import SessionLocal
from database.models import StoreSettings, BotEmbedTemplate
from services.audit_service import log_action

def publish_store_panel_to_discord():
    session = SessionLocal()
    try:
        settings = session.query(StoreSettings).filter_by(id="default").first()
        if not settings:
            return False, "Configurações da loja não encontradas."

        bot_token = settings.bot_token.strip() if settings.bot_token else ""
        channel_id = settings.store_channel_id.strip() if settings.store_channel_id else ""

        if not bot_token:
            return False, "Token do Bot não configurado. Por favor, insira o Bot Token nas configurações."

        if not channel_id:
            return False, "ID do Canal da Loja não configurado. Por favor, insira o ID do Canal do Discord nas configurações."

        # Fetch custom 'main_menu' template
        tpl = session.query(BotEmbedTemplate).filter_by(key="main_menu").first()
        title = tpl.title if tpl else f"🏪 {settings.store_name.upper()} — MENU PRINCIPAL"
        description = tpl.description if tpl else settings.bot_welcome_message
        footer_text = tpl.footer_text if tpl else "Regra Central da Economia: Dinheiro ➔ Coins ➔ Produtos"
        color_hex = tpl.color if tpl else "#FFD700"

        try:
            color_int = int(color_hex.lstrip('#'), 16)
        except Exception:
            color_int = 16766720

        embed = {
            "title": title,
            "description": description,
            "color": color_int,
            "fields": [
                {"name": "🛒 Loja", "value": "Explore armas, equipamentos e veículos.", "inline": True},
                {"name": "🪙 Comprar Coins", "value": "Adquira moedas virtuais.", "inline": True},
                {"name": "💰 Meu Saldo", "value": "Consulte seu saldo e movimentações.", "inline": True},
                {"name": "📦 Meus Pedidos", "value": "Acompanhe suas compras.", "inline": True},
                {"name": "🎫 Suporte", "value": "Abra um ticket de atendimento.", "inline": True}
            ],
            "footer": {"text": footer_text}
        }

        thumb_url = tpl.thumbnail_url if (tpl and tpl.thumbnail_url) else settings.logo_url
        if thumb_url and thumb_url.startswith("http"):
            embed["thumbnail"] = {"url": thumb_url}

        if tpl and tpl.image_url and tpl.image_url.startswith("http"):
            embed["image"] = {"url": tpl.image_url}

        components = [
            {
                "type": 1,
                "components": [
                    {"type": 2, "style": 1, "label": "🛒 Loja", "custom_id": "btn_main_store"},
                    {"type": 2, "style": 1, "label": "🛍️ Ver Carrinho", "custom_id": "btn_main_cart"},
                    {"type": 2, "style": 3, "label": "🪙 Comprar Coins", "custom_id": "btn_main_buy_coins"},
                    {"type": 2, "style": 2, "label": "💰 Meu Saldo", "custom_id": "btn_main_balance"},
                    {"type": 2, "style": 2, "label": "📦 Meus Pedidos", "custom_id": "btn_main_orders"}
                ]
            },
            {
                "type": 1,
                "components": [
                    {"type": 2, "style": 4, "label": "🎫 Suporte Técnico", "custom_id": "btn_main_support"}
                ]
            }
        ]

        payload = {
            "embeds": [embed],
            "components": components
        }

        data = json.dumps(payload).encode('utf-8')
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"

        headers = {
            "Authorization": f"Bot {bot_token}",
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (https://github.com, 1.0)"
        }

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        with urllib.request.urlopen(req) as response:
            res_body = json.loads(response.read().decode('utf-8'))
            message_id = res_body.get('id')
            log_action("STORE_PANEL_PUBLISHED", f"Painel da loja publicado no canal {channel_id} (Msg ID: {message_id})")
            return True, f"🚀 Painel da loja enviado com sucesso para o canal do Discord! (ID da Mensagem: {message_id})"

    except urllib.error.HTTPError as e:
        error_content = e.read().decode('utf-8')
        return False, f"Erro na API do Discord ({e.code}): Verifique se o Bot Token tem acesso ao canal e se o ID do canal está correto. Detalhes: {error_content}"
    except Exception as e:
        return False, f"Erro ao comunicar com Discord: {str(e)}"
    finally:
        session.close()
