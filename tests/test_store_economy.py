import os
import pytest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from database.models import Base, StoreSettings
from database.db import engine, SessionLocal, init_db
from database.seed import seed
from services.user_service import get_or_create_user, get_user_balance
from services.coin_service import get_active_coin_packages, process_coin_purchase, update_coin_package, create_coin_package
from services.store_service import get_active_categories, get_products_by_category, create_product, get_product_by_id
from services.order_service import create_order, update_order_status, get_user_orders
from services.coupon_service import apply_coupon
from services.ticket_service import create_ticket
from services.types_xml_service import process_types_xml_content, get_all_type_item_names
from services.discord_publisher import publish_store_panel_to_discord
from services.embed_service import update_embed_template, get_embed_template
from bot.utils import build_embed_from_db

@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed()

def test_full_economy_flow():
    discord_id = "999888777"
    user = get_or_create_user(discord_id, "SurvivorDayZ")
    assert user is not None
    assert get_user_balance(discord_id) == 0

    packages = get_active_coin_packages()
    assert len(packages) > 0
    pkg_1000 = [p for p in packages if "1.000" in p.title or p.coins == 1000][0]

    ok, msg = process_coin_purchase(discord_id, pkg_1000.id)
    assert ok is True
    balance = get_user_balance(discord_id)
    assert balance == 1100

    categories = get_active_categories()
    weapons_cat = [c for c in categories if c.name == "Armas"][0]

    products = get_products_by_category(weapons_cat.id)
    m4a1 = [p for p in products if "M4A1" in p.name][0]

    ok_order, msg_order, order_id = create_order(discord_id, [{'product_id': m4a1.id, 'quantity': 1}])
    assert ok_order is True, f"Failed order: {msg_order}"

    assert get_user_balance(discord_id) == 600

    orders = get_user_orders(discord_id)
    assert len(orders) == 1
    assert orders[0].status == "Aguardando processamento"

    ok_status, msg_status = update_order_status(order_id, "Entregue", admin_notes="Entregue na base do jogador")
    assert ok_status is True

def test_embed_template_customization():
    ok, msg = update_embed_template(
        key="main_menu",
        title="🏪 LOJA CUSTOMIZADA DAYZ",
        description="Nova descrição customizada pelo painel web",
        color="#34D399",
        footer_text="Rodapé Customizado",
        thumbnail_url="https://i.imgur.com/thumb.png",
        image_url="https://i.imgur.com/banner.png"
    )
    assert ok is True

    tpl = get_embed_template("main_menu")
    assert tpl.title == "🏪 LOJA CUSTOMIZADA DAYZ"
    assert tpl.color == "#34D399"

    discord_embed = build_embed_from_db("main_menu")
    assert discord_embed.title == "🏪 LOJA CUSTOMIZADA DAYZ"
    assert discord_embed.description == "Nova descrição customizada pelo painel web"
    assert discord_embed.footer.text == "Rodapé Customizado"

def test_dayz_types_xml_parser_and_kit_creation():
    xml_data = """<?xml version="1.0" encoding="UTF-8"?>
    <types>
        <type name="AK74">
            <nominal>10</nominal>
            <category name="weapons"/>
        </type>
        <type name="WoodenPlank">
            <nominal>50</nominal>
            <category name="tools"/>
        </type>
    </types>"""

    ok, msg = process_types_xml_content(xml_data)
    assert ok is True
    item_names = get_all_type_item_names()
    assert "AK74" in item_names
    assert "WoodenPlank" in item_names

    categories = get_active_categories()
    cat_id = categories[0].id

    kit_items = [
        {'item_name': 'WoodenPlank', 'quantity': 20, 'is_single_use': True, 'expiration_days': 30},
        {'item_name': 'NailsBox', 'quantity': 2, 'is_single_use': True, 'expiration_days': 0}
    ]

    prod = create_product(cat_id, "Kit Básico de Construção", "Contém tábuas e pregos", 800, stock=10, content_items=kit_items)
    assert prod is not None

    fetched = get_product_by_id(prod.id)
    assert len(fetched.content_items) == 2
    assert fetched.content_items[0].item_name == "WoodenPlank"
    assert fetched.content_items[0].expiration_days == 30

def test_discord_publisher_validation():
    session = SessionLocal()
    s = session.query(StoreSettings).filter_by(id="default").first()
    s.bot_token = ""
    s.store_channel_id = ""
    session.commit()
    session.close()

    ok, msg = publish_store_panel_to_discord()
    assert ok is False
    assert "Token do Bot não configurado" in msg
