from flask import (Blueprint, render_template, request, abort)
from flask_login import login_required, current_user
from models import Item, Category, Location
from database import db

reports_bp = Blueprint('reports', __name__)

def staff_or_admin():
    if current_user.role not in ['admin', 'staff']:
        abort(403)

@reports_bp.route('/reports/inventory')
@login_required
def inventory():
    staff_or_admin()
    cat_id = request.args.get('category')
    loc_id = request.args.get('location')
    query  = Item.query
    if cat_id:
        query = query.filter_by(category_id=cat_id)
    if loc_id:
        query = query.filter_by(location_id=loc_id)
    items       = query.order_by(Item.item_code).all()
    total_items = sum(i.quantity for i in items)
    total_sku   = len(items)
    total_value = sum(i.total_value for i in items)
    categories  = Category.query.filter_by(status='active').all()
    locations   = Location.query.filter_by(status='active').all()
    return render_template('reports/inventory.html',
        items=items,
        total_items=total_items,
        total_sku=total_sku,
        total_value=total_value,
        categories=categories,
        locations=locations,
        cat_count=len(categories),
    )

@reports_bp.route('/reports/borrowing')
@login_required
def borrowing():
    staff_or_admin()
    items          = Item.query.filter_by(status='in_use').order_by(Item.item_code).all()
    total_borrowed = sum(i.quantity for i in items)
    total_value    = sum(i.total_value for i in items)
    borrowers      = len(set(i.holder_id for i in items if i.holder_id))
    return render_template('reports/borrowing.html',
        items=items,
        total_borrowed=total_borrowed,
        total_value=total_value,
        borrowers=borrowers,
    )

@reports_bp.route('/reports/damage')
@login_required
def damage():
    staff_or_admin()
    filter_type   = request.args.get('type', '')
    damaged       = Item.query.filter_by(status='damaged').all()
    lost          = Item.query.filter_by(status='lost').all()
    if filter_type == 'damaged':
        items = damaged
    elif filter_type == 'lost':
        items = lost
    else:
        items = damaged + lost
    total_damaged = len(damaged)
    total_lost    = len(lost)
    total_loss    = sum(i.total_value for i in damaged + lost)
    return render_template('reports/damage.html',
        items=items,
        total_damaged=total_damaged,
        total_lost=total_lost,
        total_loss=total_loss,
        filter_type=filter_type,
    )