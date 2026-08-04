from flask import Blueprint, render_template
from flask_login import login_required
from models import Item, StockOpname, Category
from database import db
from datetime import date

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    # ── Stats ──────────────────────────────────────────────
    total_items      = Item.query.count()
    electronic_count = Item.query.filter_by(item_type='electronic').count()
    sample_count     = Item.query.filter_by(item_type='sample').count()
    borrowed_count   = Item.query.filter_by(status='in_use').count()
    damaged_count    = Item.query.filter_by(status='damaged').count()
    lost_count       = Item.query.filter_by(status='lost').count()
    total_value      = db.session.query(
        db.func.sum(Item.unit_price * Item.quantity)
    ).scalar() or 0

    # ── Stock opname progress ──────────────────────────────
    checked_ids = db.session.query(
        StockOpname.item_id
    ).distinct().all()
    checked_ids   = [r[0] for r in checked_ids]
    opname_pct    = round(len(checked_ids) / total_items * 100) if total_items else 0

    # ── Pie chart: inventory by category ──────────────────
    categories  = Category.query.filter_by(status='active').all()
    cat_labels  = [c.name for c in categories]
    cat_values  = [Item.query.filter_by(category_id=c.id).count()
                   for c in categories]

    # ── Bar chart: monthly opname ──────────────────────────
    months      = ['Jan','Feb','Mar','Apr','May','Jun',
                   'Jul','Aug','Sep','Oct','Nov','Dec']
    year        = date.today().year
    monthly     = []
    for m in range(1, 13):
        count = StockOpname.query.filter(
            db.func.extract('year',  StockOpname.checked_at) == year,
            db.func.extract('month', StockOpname.checked_at) == m,
        ).count()
        monthly.append(count)

    # ── Recent items ───────────────────────────────────────
    recent_items = Item.query.order_by(
        Item.created_at.desc()
    ).limit(5).all()

    return render_template('dashboard/index.html',
        total_items      = total_items,
        electronic_count = electronic_count,
        sample_count     = sample_count,
        borrowed_count   = borrowed_count,
        damaged_count    = damaged_count,
        lost_count       = lost_count,
        total_value      = total_value,
        opname_pct       = opname_pct,
        cat_labels       = cat_labels,
        cat_values       = cat_values,
        months           = months,
        monthly          = monthly,
        recent_items     = recent_items,
    )