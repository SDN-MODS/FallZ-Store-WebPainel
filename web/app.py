import os
from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy.orm import joinedload
from database.db import init_db, SessionLocal
from database.models import (
    User, CoinPackage, CoinTransaction, Order, Product, Category, Coupon, AuditLog, StoreSettings
)
from services.coin_service import (
    get_active_coin_packages, create_coin_package, adjust_user_coins_manually
)
from services.store_service import (
    get_all_categories, create_category, create_product, delete_product
)
from services.order_service import update_order_status
from services.coupon_service import get_all_coupons, create_coupon
from services.audit_service import log_action

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dayz_secret_key_12345")

@app.before_request
def ensure_db():
    init_db()

# 📊 Dashboard
@app.route('/')
def dashboard():
    session = SessionLocal()
    try:
        transactions = session.query(CoinTransaction).filter_by(type="PURCHASE").all()
        revenue_brl = sum(t.amount_brl for t in transactions if t.amount_brl)
        coins_sold = sum(t.coins for t in transactions if t.coins > 0)

        pending_orders = session.query(Order).filter(Order.status.in_(["Aguardando processamento", "Processando"])).all()
        total_users = session.query(User).count()

        recent_orders = session.query(Order).options(joinedload(Order.user)).order_by(Order.created_at.desc()).limit(5).all()
        low_stock_products = session.query(Product).options(joinedload(Product.category)).filter(Product.stock >= 0, Product.stock <= 5).all()

        return render_template(
            'dashboard.html',
            active_page='dashboard',
            revenue_brl=revenue_brl,
            coins_sold=coins_sold,
            pending_orders_count=len(pending_orders),
            total_users=total_users,
            recent_orders=recent_orders,
            low_stock_products=low_stock_products
        )
    finally:
        session.close()

# 🪙 Gerenciamento de Coins
@app.route('/coins')
def coins():
    session = SessionLocal()
    try:
        packages = get_active_coin_packages()
        users = session.query(User).all()
        return render_template('coins.html', active_page='coins', packages=packages, users=users)
    finally:
        session.close()

@app.route('/coins/create-package', methods=['POST'])
def handle_create_package():
    title = request.form.get('title')
    coins = int(request.form.get('coins', 0))
    bonus_coins = int(request.form.get('bonus_coins', 0))
    price_brl = float(request.form.get('price_brl', 0.0))
    description = request.form.get('description', '')

    create_coin_package(title, coins, bonus_coins, price_brl, description)
    flash(f"Pacote '{title}' criado com sucesso!", "success")
    return redirect(url_for('coins'))

@app.route('/coins/adjust-balance', methods=['POST'])
def handle_adjust_balance():
    user_id = request.form.get('user_id')
    amount = int(request.form.get('amount', 0))
    reason = request.form.get('reason', '')

    ok, msg = adjust_user_coins_manually("AdminWeb", user_id, amount, reason)
    if ok:
        flash(msg, "success")
    else:
        flash(msg, "error")
    return redirect(url_for('coins'))

# 📦 Gerenciamento de Produtos & Categorias
@app.route('/products')
def products():
    session = SessionLocal()
    try:
        categories = get_all_categories()
        prods = session.query(Product).options(joinedload(Product.category)).all()
        return render_template('products.html', active_page='products', categories=categories, products=prods)
    finally:
        session.close()

@app.route('/products/create-category', methods=['POST'])
def handle_create_category():
    name = request.form.get('name')
    description = request.form.get('description', '')
    display_order = int(request.form.get('display_order', 0))

    create_category(name, description, display_order)
    flash(f"Categoria '{name}' criada!", "success")
    return redirect(url_for('products'))

@app.route('/products/create-product', methods=['POST'])
def handle_create_product():
    category_id = request.form.get('category_id')
    name = request.form.get('name')
    description = request.form.get('description', '')
    price_coins = int(request.form.get('price_coins', 0))
    stock = int(request.form.get('stock', -1))
    image_url = request.form.get('image_url', '')

    create_product(category_id, name, description, price_coins, stock, image_url)
    flash(f"Produto '{name}' cadastrado!", "success")
    return redirect(url_for('products'))

@app.route('/products/delete/<product_id>')
def handle_delete_product(product_id):
    delete_product(product_id)
    flash("Produto excluído.", "success")
    return redirect(url_for('products'))

# 🛒 Gerenciamento de Pedidos
@app.route('/orders')
def orders():
    session = SessionLocal()
    try:
        all_orders = session.query(Order).options(
            joinedload(Order.user),
            joinedload(Order.items).joinedload(Order.items.property.mapper.class_.product)
        ).order_by(Order.created_at.desc()).all()
        return render_template('orders.html', active_page='orders', orders=all_orders)
    finally:
        session.close()

@app.route('/orders/update-status', methods=['POST'])
def handle_update_order_status():
    order_id = request.form.get('order_id')
    status = request.form.get('status')
    refund = request.form.get('refund') == 'true'

    ok, msg = update_order_status(order_id, status, refund=refund)
    if ok:
        flash(msg, "success")
    else:
        flash(msg, "error")
    return redirect(url_for('orders'))

# 👤 Jogadores / Clientes
@app.route('/users')
def users():
    session = SessionLocal()
    try:
        users_list = session.query(User).options(joinedload(User.orders)).all()
        return render_template('users.html', active_page='users', users=users_list)
    finally:
        session.close()

# 🎁 Cupons
@app.route('/coupons')
def coupons():
    coupons_list = get_all_coupons()
    return render_template('coupons.html', active_page='coupons', coupons=coupons_list)

@app.route('/coupons/create', methods=['POST'])
def handle_create_coupon():
    code = request.form.get('code')
    type_str = request.form.get('type')
    value = int(request.form.get('value', 0))
    max_uses = int(request.form.get('max_uses', -1))

    create_coupon(code, type_str, value, max_uses)
    flash(f"Cupom '{code}' criado com sucesso!", "success")
    return redirect(url_for('coupons'))

# 📈 Relatórios
@app.route('/reports')
def reports():
    session = SessionLocal()
    try:
        transactions = session.query(CoinTransaction).options(joinedload(CoinTransaction.user)).order_by(CoinTransaction.created_at.desc()).all()
        purchases = [t for t in transactions if t.type == "PURCHASE"]

        revenue_brl = sum(t.amount_brl for t in purchases if t.amount_brl)
        total_coins_issued = sum(t.coins for t in transactions if t.coins > 0)
        total_coins_spent = abs(sum(t.coins for t in transactions if t.coins < 0))

        return render_template(
            'reports.html',
            active_page='reports',
            transactions=transactions,
            revenue_brl=revenue_brl,
            total_coins_issued=total_coins_issued,
            total_coins_spent=total_coins_spent
        )
    finally:
        session.close()

# ⚙️ Configurações
@app.route('/settings')
def settings():
    session = SessionLocal()
    try:
        s = session.query(StoreSettings).filter_by(id='default').first()
        return render_template('settings.html', active_page='settings', settings=s)
    finally:
        session.close()

@app.route('/settings/save', methods=['POST'])
def handle_save_settings():
    session = SessionLocal()
    try:
        s = session.query(StoreSettings).filter_by(id='default').first()
        if s:
            s.store_name = request.form.get('store_name')
            s.logo_url = request.form.get('logo_url')
            s.support_channel_id = request.form.get('support_channel_id')
            s.admin_role_id = request.form.get('admin_role_id')
            s.bot_welcome_message = request.form.get('bot_welcome_message')
            session.commit()
            log_action("SETTINGS_UPDATED", "Configurações gerais da loja atualizadas")
            flash("Configurações atualizadas!", "success")
        return redirect(url_for('settings'))
    finally:
        session.close()

# 📝 Logs
@app.route('/logs')
def logs():
    session = SessionLocal()
    try:
        audit_logs = session.query(AuditLog).options(joinedload(AuditLog.user)).order_by(AuditLog.created_at.desc()).limit(100).all()
        return render_template('logs.html', active_page='logs', logs=audit_logs)
    finally:
        session.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
