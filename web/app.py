import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy.orm import joinedload
from database.db import init_db, SessionLocal
from database.models import (
    User, CoinPackage, CoinTransaction, Order, Product, Category, Coupon, AuditLog, StoreSettings
)
from services.coin_service import (
    get_active_coin_packages, get_all_coin_packages, get_coin_package_by_id,
    create_coin_package, update_coin_package, delete_coin_package, adjust_user_coins_manually
)
from services.store_service import (
    get_all_categories, create_category, create_product, delete_product
)
from services.order_service import update_order_status
from services.coupon_service import get_all_coupons, create_coupon, delete_coupon, toggle_coupon
from services.audit_service import log_action
from services.types_xml_service import process_types_xml_content, get_all_type_item_names
from services.discord_publisher import publish_store_panel_to_discord
from services.embed_service import get_all_embed_templates, get_embed_template, update_embed_template

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
@app.route('/coins/edit-package/<package_id>')
def coins(package_id=None):
    session = SessionLocal()
    try:
        packages = get_all_coin_packages()
        users = session.query(User).all()
        edit_pkg = None
        if package_id:
            edit_pkg = session.query(CoinPackage).filter_by(id=package_id).first()
        return render_template('coins.html', active_page='coins', packages=packages, users=users, edit_pkg=edit_pkg)
    finally:
        session.close()

@app.route('/coins/create-package', methods=['POST'])
def handle_create_package():
    title = request.form.get('title')
    coins = int(request.form.get('coins', 0))
    bonus_coins = int(request.form.get('bonus_coins', 0))
    price_brl = float(request.form.get('price_brl', 0.0))
    description = request.form.get('description', '')
    image_url = request.form.get('image_url', '')

    create_coin_package(title, coins, bonus_coins, price_brl, description, image_url)
    flash(f"Pacote '{title}' criado com sucesso!", "success")
    return redirect(url_for('coins'))

@app.route('/coins/edit-package/<package_id>', methods=['POST'])
def handle_edit_package(package_id):
    title = request.form.get('title')
    coins = int(request.form.get('coins', 0))
    bonus_coins = int(request.form.get('bonus_coins', 0))
    price_brl = float(request.form.get('price_brl', 0.0))
    description = request.form.get('description', '')
    image_url = request.form.get('image_url', '')
    active = request.form.get('active') == 'true'

    res = update_coin_package(package_id, title, coins, bonus_coins, price_brl, active, description, image_url)
    if res:
        flash(f"Pacote '{title}' atualizado com sucesso!", "success")
    else:
        flash("Erro ao atualizar pacote.", "error")
    return redirect(url_for('coins'))

@app.route('/coins/toggle-package/<package_id>')
def handle_toggle_package(package_id):
    session = SessionLocal()
    try:
        pkg = session.query(CoinPackage).filter_by(id=package_id).first()
        if pkg:
            pkg.active = not pkg.active
            session.commit()
            flash(f"Status do pacote '{pkg.title}' alterado para {'Ativo' if pkg.active else 'Inativo'}.", "success")
        return redirect(url_for('coins'))
    finally:
        session.close()

@app.route('/coins/delete-package/<package_id>')
def handle_delete_package(package_id):
    ok, msg = delete_coin_package(package_id)
    if ok:
        flash(msg, "success")
    else:
        flash(msg, "error")
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

# 📦 Gerenciamento de Produtos, Kits & Types.xml
@app.route('/products')
def products():
    session = SessionLocal()
    try:
        categories = get_all_categories()
        prods = session.query(Product).options(
            joinedload(Product.category),
            joinedload(Product.content_items)
        ).all()
        dayz_type_names = get_all_type_item_names()

        return render_template('products.html', active_page='products', categories=categories, products=prods, dayz_type_names=dayz_type_names)
    finally:
        session.close()

@app.route('/products/upload-types-xml', methods=['POST'])
def handle_upload_types_xml():
    if 'types_file' not in request.files:
        flash("Nenhum arquivo enviado.", "error")
        return redirect(url_for('products'))

    file = request.files['types_file']
    if file.filename == '':
        flash("Nenhum arquivo selecionado.", "error")
        return redirect(url_for('products'))

    try:
        content = file.read().decode('utf-8', errors='ignore')
        ok, msg = process_types_xml_content(content)
        if ok:
            flash(msg, "success")
        else:
            flash(msg, "error")
    except Exception as e:
        flash(f"Erro ao ler arquivo XML: {str(e)}", "error")

    return redirect(url_for('products'))

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

    item_names = request.form.getlist('item_names[]')
    item_quantities = request.form.getlist('item_quantities[]')
    item_expirations = request.form.getlist('item_expirations[]')
    item_single_uses = request.form.getlist('item_single_use[]')

    content_items = []
    for idx, item_name in enumerate(item_names):
        if item_name.strip():
            qty = int(item_quantities[idx]) if idx < len(item_quantities) and item_quantities[idx] else 1
            exp = int(item_expirations[idx]) if idx < len(item_expirations) and item_expirations[idx] else 0
            is_single = str(idx) in item_single_uses or '0' in item_single_uses

            content_items.append({
                'item_name': item_name.strip(),
                'quantity': qty,
                'is_single_use': is_single,
                'expiration_days': exp
            })

    create_product(category_id, name, description, price_coins, stock, image_url, content_items=content_items)
    flash(f"Produto/Kit '{name}' cadastrado com sucesso!", "success")
    return redirect(url_for('products'))

@app.route('/products/delete/<product_id>')
def handle_delete_product(product_id):
    delete_product(product_id)
    flash("Produto excluído.", "success")
    return redirect(url_for('products'))

# 🎨 Personalização de Embeds & Conversas do Bot
@app.route('/embeds')
def embeds():
    session = SessionLocal()
    try:
        templates = get_all_embed_templates()
        selected_key = request.args.get('key', 'main_menu')
        selected_tpl = get_embed_template(selected_key)
        return render_template('embeds.html', active_page='embeds', templates=templates, selected_key=selected_key, selected_tpl=selected_tpl)
    finally:
        session.close()

import json

@app.route('/embeds/save/<key>', methods=['POST'])
def handle_save_embed(key):
    title = request.form.get('title')
    description = request.form.get('description')
    color = request.form.get('color')
    footer_text = request.form.get('footer_text', '')
    thumbnail_url = request.form.get('thumbnail_url', '')
    image_url = request.form.get('image_url', '')

    field_names = request.form.getlist('field_names[]')
    field_values = request.form.getlist('field_values[]')
    field_inlines = request.form.getlist('field_inlines[]')

    fields_list = []
    for idx, f_name in enumerate(field_names):
        if f_name.strip():
            f_val = field_values[idx] if idx < len(field_values) else ''
            inline_val = field_inlines[idx] if idx < len(field_inlines) else 'true'
            is_inline = (inline_val == 'true')
            fields_list.append({
                "name": f_name.strip(),
                "value": f_val.strip(),
                "inline": is_inline
            })

    fields_json = json.dumps(fields_list, ensure_ascii=False) if fields_list else ""

    ok, msg = update_embed_template(key, title, description, color, footer_text, thumbnail_url, image_url, fields_json=fields_json)
    if ok:
        flash(msg, "success")
    else:
        flash(msg, "error")
    return redirect(url_for('embeds', key=key))

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
    session = SessionLocal()
    try:
        coupons_list = get_all_coupons()
        categories = get_all_categories()
        products = session.query(Product).all()
        return render_template('coupons.html', active_page='coupons', coupons=coupons_list, categories=categories, products=products)
    finally:
        session.close()

import datetime

@app.route('/coupons/create', methods=['POST'])
def handle_create_coupon():
    code = request.form.get('code')
    type_str = request.form.get('type')
    value = int(request.form.get('value', 0))
    applies_to = request.form.get('applies_to', 'ALL')
    target_id = request.form.get('target_id', '')
    max_uses = int(request.form.get('max_uses', -1))

    channel_id = request.form.get('channel_id', '').strip()
    interval_minutes = int(request.form.get('interval_minutes', 0))

    start_time_str = request.form.get('start_time', '').strip()
    expires_at_str = request.form.get('expires_at', '').strip()

    start_time = datetime.datetime.fromisoformat(start_time_str) if start_time_str else None
    expires_at = datetime.datetime.fromisoformat(expires_at_str) if expires_at_str else None

    create_coupon(
        code, type_str, value,
        applies_to=applies_to, target_id=target_id,
        max_uses=max_uses, channel_id=channel_id,
        interval_minutes=interval_minutes,
        start_time=start_time, expires_at=expires_at
    )
    flash(f"Cupom '{code}' criado com sucesso!", "success")
    return redirect(url_for('coupons'))

@app.route('/coupons/toggle/<coupon_id>')
def handle_toggle_coupon(coupon_id):
    ok, msg = toggle_coupon(coupon_id)
    if ok:
        flash(msg, "success")
    else:
        flash(msg, "error")
    return redirect(url_for('coupons'))

@app.route('/coupons/delete/<coupon_id>')
def handle_delete_coupon(coupon_id):
    ok, msg = delete_coupon(coupon_id)
    if ok:
        flash(msg, "success")
    else:
        flash(msg, "error")
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

# ⚙️ Configurações & Publicação no Discord
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

            bot_client_id = request.form.get('bot_client_id', '').strip()
            bot_token = request.form.get('bot_token', '').strip()
            store_channel_id = request.form.get('store_channel_id', '').strip()

            bot_invite_url = request.form.get('bot_invite_url', '').strip()
            if not bot_invite_url and bot_client_id:
                bot_invite_url = f"https://discord.com/oauth2/authorize?client_id={bot_client_id}&permissions=8&scope=bot"

            s.bot_client_id = bot_client_id
            s.bot_token = bot_token
            s.bot_invite_url = bot_invite_url
            s.store_channel_id = store_channel_id
            s.support_channel_id = request.form.get('support_channel_id')
            s.bot_welcome_message = request.form.get('bot_welcome_message')
            session.commit()
            log_action("SETTINGS_UPDATED", "Configurações do Discord e da loja salvas.")
            flash("Configurações salvas com sucesso!", "success")
        return redirect(url_for('settings'))
    finally:
        session.close()

@app.route('/settings/publish-store-panel', methods=['POST'])
def handle_publish_store_panel():
    ok, msg = publish_store_panel_to_discord()
    if ok:
        flash(msg, "success")
    else:
        flash(msg, "error")
    return redirect(url_for('settings'))

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
