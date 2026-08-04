from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, jsonify)
from flask_login import login_required, current_user
from database import db
from models import (Item, Category, Brand, Location,
                    Holder, ItemCondition, Unit, Setting)
from datetime import datetime, date
import re

inventory_bp = Blueprint('inventory', __name__)

# ── Helper: generate item code ────────────────────────────────
def generate_item_code():
    setting = Setting.query.filter_by(key='item_id_format').first()
    fmt     = setting.value if setting else 'INV-YYYY-###'
    year    = str(date.today().year)
    fmt     = fmt.replace('YYYY', year)

    # Cari nomor urut terakhir tahun ini
    prefix  = fmt.split('###')[0]
    last    = Item.query.filter(
        Item.item_code.like(f'{prefix}%')
    ).order_by(Item.item_code.desc()).first()

    if last:
        try:
            num = int(last.item_code.split(prefix)[-1]) + 1
        except:
            num = 1
    else:
        num = 1

    return f"{prefix}{str(num).zfill(3)}"

# ── Context: master data untuk form ──────────────────────────
def get_master_data():
    return {
        'categories': Category.query.filter_by(status='active').all(),
        'brands'    : Brand.query.filter_by(status='active').all(),
        'locations' : Location.query.filter_by(status='active').all(),
        'holders'   : Holder.query.filter_by(status='active').all(),
        'conditions': ItemCondition.query.all(),
        'units'     : Unit.query.all(),
    }

# ══════════════════════════════════════════════════════════════
# ALL ITEMS
# ══════════════════════════════════════════════════════════════
@inventory_bp.route('/inventory/all')
@login_required
def all_items():
    cat_id = request.args.get('category')
    loc_id = request.args.get('location')

    query = Item.query
    if cat_id:
        query = query.filter_by(category_id=cat_id)
    if loc_id:
        query = query.filter_by(location_id=loc_id)

    items      = query.order_by(Item.item_code).all()

    # ── Hapus categories & locations dari get_master_data()
    #    karena sudah didefinisikan ulang di sini ──────────────
    master     = get_master_data()
    categories = Category.query.filter_by(status='active').all()
    locations  = Location.query.filter_by(status='active').all()

    return render_template('inventory/all_items.html',
        items      = items,
        categories = categories,
        locations  = locations,
        brands     = master['brands'],
        holders    = master['holders'],
        conditions = master['conditions'],
        units      = master['units'],
    )

@inventory_bp.route('/inventory/add', methods=['POST'])
@login_required
def add_item():
    data = request.form

    # Generate item code otomatis
    item_code = generate_item_code()

    # Parse purchase date
    purchase_date = None
    if data.get('purchase_date'):
        try:
            purchase_date = datetime.strptime(
                data['purchase_date'], '%Y-%m-%d'
            ).date()
        except:
            pass

    new_item = Item(
        item_code     = item_code,
        name          = data.get('name', '').strip(),
        item_type     = data.get('item_type', 'general'),
        category_id   = data.get('category_id') or None,
        brand_id      = data.get('brand_id') or None,
        unit_id       = data.get('unit_id') or None,
        condition_id  = data.get('condition_id') or None,
        location_id   = data.get('location_id') or None,
        holder_id     = data.get('holder_id') or None,
        quantity      = int(data.get('quantity', 1)),
        unit_price    = float(data.get('unit_price', 0) or 0),
        purchase_date = purchase_date,
        status        = data.get('status', 'available'),
        model         = data.get('model', '').strip() or None,
        serial_number = data.get('serial_number', '').strip() or None,
        notes         = data.get('notes', '').strip() or None,
    )

    db.session.add(new_item)
    db.session.commit()
    flash(f'Item "{new_item.name}" added with code {item_code}.', 'success')

    # Redirect ke halaman yang sesuai
    redirect_to = data.get('redirect_to', 'inventory.all_items')
    return redirect(url_for(redirect_to))

@inventory_bp.route('/inventory/<int:id>/edit', methods=['POST'])
@login_required
def edit_item(id):
    item = Item.query.get_or_404(id)
    data = request.form

    purchase_date = None
    if data.get('purchase_date'):
        try:
            purchase_date = datetime.strptime(
                data['purchase_date'], '%Y-%m-%d'
            ).date()
        except:
            pass

    item.name          = data.get('name', '').strip()
    item.item_type     = data.get('item_type', 'general')
    item.category_id   = data.get('category_id') or None
    item.brand_id      = data.get('brand_id') or None
    item.unit_id       = data.get('unit_id') or None
    item.condition_id  = data.get('condition_id') or None
    item.location_id   = data.get('location_id') or None
    item.holder_id     = data.get('holder_id') or None
    item.quantity      = int(data.get('quantity', 1))
    item.unit_price    = float(data.get('unit_price', 0) or 0)
    item.purchase_date = purchase_date
    item.status        = data.get('status', 'available')
    item.model         = data.get('model', '').strip() or None
    item.serial_number = data.get('serial_number', '').strip() or None
    item.notes         = data.get('notes', '').strip() or None

    db.session.commit()
    flash(f'Item "{item.name}" updated.', 'success')

    redirect_to = data.get('redirect_to', 'inventory.all_items')
    return redirect(url_for(redirect_to))

@inventory_bp.route('/inventory/<int:id>/delete', methods=['POST'])
@login_required
def delete_item(id):
    item = Item.query.get_or_404(id)
    name = item.name
    db.session.delete(item)
    db.session.commit()
    flash(f'Item "{name}" deleted.', 'success')
    return redirect(request.referrer or url_for('inventory.all_items'))

@inventory_bp.route('/inventory/<int:id>/json')
@login_required
def get_item_json(id):
    item = Item.query.get_or_404(id)
    return jsonify({
        'id'           : item.id,
        'name'         : item.name,
        'item_type'    : item.item_type,
        'category_id'  : item.category_id,
        'brand_id'     : item.brand_id,
        'unit_id'      : item.unit_id,
        'condition_id' : item.condition_id,
        'location_id'  : item.location_id,
        'holder_id'    : item.holder_id,
        'quantity'     : item.quantity,
        'unit_price'   : item.unit_price,
        'purchase_date': item.purchase_date.strftime('%Y-%m-%d') if item.purchase_date else '',
        'status'       : item.status,
        'model'        : item.model or '',
        'serial_number': item.serial_number or '',
        'notes'        : item.notes or '',
    })

# ══════════════════════════════════════════════════════════════
# ELECTRONIC ASSETS
# ══════════════════════════════════════════════════════════════
@inventory_bp.route('/inventory/electronic')
@login_required
def electronic():
    items = Item.query.filter_by(
        item_type='electronic'
    ).order_by(Item.item_code).all()

    return render_template('inventory/electronic.html',
        items=items, **get_master_data()
    )

# ══════════════════════════════════════════════════════════════
# SAMPLE ITEMS
# ══════════════════════════════════════════════════════════════
@inventory_bp.route('/inventory/samples')
@login_required
def samples():
    items = Item.query.filter_by(
        item_type='sample'
    ).order_by(Item.item_code).all()

    return render_template('inventory/samples.html',
        items=items, **get_master_data()
    )