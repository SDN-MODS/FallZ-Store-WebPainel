import pytest
from database.db import init_db, get_db
from database.seed import seed
from services.cart_service import add_to_cart, get_cart_items, remove_from_cart, clear_cart, checkout_cart
from services.user_service import get_or_create_user, get_user_balance
from services.coin_service import adjust_user_coins_manually
from services.store_service import get_active_categories, get_products_by_category

@pytest.fixture(autouse=True)
def setup_database():
    init_db()
    seed()

def test_cart_operations():
    user_id = "test_cart_user_999"
    get_or_create_user(user_id, username="CartTester")

    # Pegar produto
    categories = get_active_categories()
    assert len(categories) > 0
    products = get_products_by_category(categories[0].id)
    assert len(products) > 0
    product = products[0]

    # 1. Adicionar ao carrinho
    ok, msg = add_to_cart(user_id, product.id, quantity=2)
    assert ok is True

    cart = get_cart_items(user_id)
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 2
    assert cart["total_coins"] == product.price_coins * 2

    # 2. Remover do carrinho
    ok, msg = remove_from_cart(user_id, product.id)
    assert ok is True

    cart = get_cart_items(user_id)
    assert len(cart["items"]) == 0

    # 3. Adicionar novamente e esvaziar
    add_to_cart(user_id, product.id, quantity=1)
    clear_cart(user_id)
    cart = get_cart_items(user_id)
    assert len(cart["items"]) == 0

def test_cart_checkout_with_coins():
    user_id = "checkout_user_888"
    get_or_create_user(user_id, username="CheckoutUser")

    categories = get_active_categories()
    products = get_products_by_category(categories[0].id)
    product = products[0]

    # Adicionar 2 unidades ao carrinho
    add_to_cart(user_id, product.id, quantity=2)

    total_coins_needed = product.price_coins * 2

    # Tentar checkout com saldo 0
    ok, msg = checkout_cart(user_id)
    assert ok is False
    assert "Saldo insuficiente" in msg

    # Adicionar saldo suficiente ao usuário
    adjust_user_coins_manually("admin", user_id, total_coins_needed + 100, reason="Teste de compra")
    assert get_user_balance(user_id) == total_coins_needed + 100

    # Tentar checkout novamente
    ok, msg = checkout_cart(user_id)
    assert ok is True
    assert "Compra do carrinho realizada com sucesso" in msg

    # Saldo deve ter sido descontado
    assert get_user_balance(user_id) == 100

    # Carrinho deve estar vazio
    cart = get_cart_items(user_id)
    assert len(cart["items"]) == 0
