import os
import pytest

# Use in-memory or dedicated test database for tests
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from database.models import Base
from database.db import engine, SessionLocal, init_db
from database.seed import seed
from services.user_service import get_or_create_user, get_user_balance
from services.coin_service import get_active_coin_packages, process_coin_purchase
from services.store_service import get_active_categories, get_products_by_category
from services.order_service import create_order, update_order_status, get_user_orders
from services.coupon_service import apply_coupon
from services.ticket_service import create_ticket, add_ticket_message

@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed()

def test_full_economy_flow():
    # 1. Create player
    discord_id = "999888777"
    user = get_or_create_user(discord_id, "SurvivorDayZ")
    assert user is not None
    assert get_user_balance(discord_id) == 0

    # 2. Buy Coins with BRL
    packages = get_active_coin_packages()
    assert len(packages) > 0
    pkg_1000 = [p for p in packages if "1.000" in p.title or p.coins == 1000][0]

    ok, msg = process_coin_purchase(discord_id, pkg_1000.id)
    assert ok is True
    # 1000 + 100 bonus = 1100 coins
    balance = get_user_balance(discord_id)
    assert balance == 1100

    # 3. Browse Store
    categories = get_active_categories()
    assert len(categories) > 0
    weapons_cat = [c for c in categories if c.name == "Armas"][0]

    products = get_products_by_category(weapons_cat.id)
    assert len(products) > 0
    m4a1 = [p for p in products if "M4A1" in p.name][0]
    assert m4a1.price_coins == 500

    # 4. Attempt Purchase of M4A1
    ok_order, msg_order, order_id = create_order(discord_id, [{'product_id': m4a1.id, 'quantity': 1}])
    assert ok_order is True, f"Failed order: {msg_order}"
    assert order_id is not None

    # Balance should now be 1100 - 500 = 600 Coins
    new_balance = get_user_balance(discord_id)
    assert new_balance == 600

    # 5. Check Order Status
    orders = get_user_orders(discord_id)
    assert len(orders) == 1
    assert orders[0].status == "Aguardando processamento"
    assert orders[0].total_coins == 500

    # 6. Admin updates order status to "Entregue"
    ok_status, msg_status = update_order_status(order_id, "Entregue", admin_notes="Entregue na base do jogador")
    assert ok_status is True

    orders_updated = get_user_orders(discord_id)
    assert orders_updated[0].status == "Entregue"

def test_insufficient_coins_prevention():
    discord_id = "111222333"
    get_or_create_user(discord_id, "Newbie")
    categories = get_active_categories()
    veic_cat = [c for c in categories if c.name == "Veículos"][0]
    car = get_products_by_category(veic_cat.id)[0] # Costs 1500 coins

    # User has 0 coins, trying to buy 1500 coins car
    ok, msg, order_id = create_order(discord_id, [{'product_id': car.id, 'quantity': 1}])
    assert ok is False
    assert "Saldo insuficiente" in msg

def test_coupon_redemption():
    discord_id = "555666777"
    get_or_create_user(discord_id, "CouponHunter")

    # Apply valid test coupon
    ok, msg = apply_coupon(discord_id, "BENVINDO")
    assert ok is True, f"Failed coupon: {msg}"
    assert get_user_balance(discord_id) == 50

    # Apply same coupon again (should fail)
    ok_dup, msg_dup = apply_coupon(discord_id, "BENVINDO")
    assert ok_dup is False
    assert "já utilizou" in msg_dup

def test_ticket_support_system():
    discord_id = "888999000"
    get_or_create_user(discord_id, "TicketUser")

    ok, msg, ticket_id = create_ticket(discord_id, "Problema com Coins", "Coins não creditadas", "Comprei pelo site e não entrou.")
    assert ok is True, f"Failed ticket: {msg}"

    ok_reply, msg_reply = add_ticket_message(ticket_id, "AdminWeb", "Admin", is_admin=True, content="Olá! Verifiquei e já recreditei seu saldo.")
    assert ok_reply is True
