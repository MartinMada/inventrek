from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, jsonify, abort)
from flask_login import login_required, current_user
from database import db
from models import Item, StockOpname, ItemCondition, Location
from datetime import date

opname_bp = Blueprint('opname', __name__)

def staff_or_admin():
    if current_user.role not in ['admin', 'staff']:
        abort(403)

def generate_opname_code():
    year = date.today().year
    last = StockOpname.query.filter(
        StockOpname.opname_code.like(f'SO-{year}-%%')
    ).order_by(StockOpname.id.desc()).first()
    num  = int(last.opname_code.split('-')[-1]) + 1 if last else 1
    return f'SO-{year}-{str(num).zfill(3)}'

@opname_bp.route('/opname/scan')
@login_required
def scan():
    conditions = ItemCondition.query.all()
    locations  = Location.query.filter_by(status='active').all()
    return render_template('opname/scan.html',
        conditions=conditions, locations=locations)

@opname_bp.route('/opname/lookup', methods=['POST'])
@login_required
def lookup():
    code = request.form.get('code', '').strip()
    if not code:
        return jsonify({'error': 'Code is required'}), 400
    item = Item.query.filter_by(item_code=code).first()
    if not item:
        item = Item.query.filter_by(qr_token=code).first()
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    return jsonify({
        'id'       : item.id,
        'item_code': item.item_code,
        'name'     : item.name,
        'category' : item.category.name if item.category else '-',
        'brand'    : item.brand.name if item.brand else '-',
        'condition': item.condition.name if item.condition else '-',
        'location' : item.location.name if item.location else '-',
        'holder'   : item.holder.name if item.holder else '-',
        'status'   : item.status,
        'quantity' : item.quantity,
    })

@opname_bp.route('/opname/submit', methods=['POST'])
@login_required
def submit_opname():
    item_id      = request.form.get('item_id')
    condition_id = request.form.get('condition_id')
    location_id  = request.form.get('location_id')
    notes        = request.form.get('notes', '').strip()
    if not item_id:
        flash('Item not found.', 'error')
        return redirect(url_for('opname.scan'))
    item   = Item.query.get_or_404(int(item_id))
    opname = StockOpname(
        opname_code  = generate_opname_code(),
        item_id      = item.id,
        checker_id   = current_user.id,
        condition_id = int(condition_id) if condition_id else item.condition_id,
        location_id  = int(location_id) if location_id else item.location_id,
        notes        = notes,
    )
    if condition_id:
        item.condition_id = int(condition_id)
        cond = ItemCondition.query.get(int(condition_id))
        if cond:
            if cond.name == 'Lost':
                item.status = 'lost'
            elif 'Damage' in cond.name or cond.name == 'Repair':
                item.status = 'damaged'
            else:
                item.status = 'available'
    db.session.add(opname)
    db.session.commit()
    flash(f'Stock opname for "{item.name}" recorded successfully.', 'success')
    return redirect(url_for('opname.scan'))

@opname_bp.route('/opname/results')
@login_required
def results():
    staff_or_admin()
    records        = StockOpname.query.order_by(StockOpname.checked_at.desc()).all()
    total_checked  = len(records)
    good_condition = sum(1 for r in records if r.condition and r.condition.name == 'Good')
    issues_found   = total_checked - good_condition
    return render_template('opname/results.html',
        records=records,
        total_checked=total_checked,
        good_condition=good_condition,
        issues_found=issues_found,
    )

@opname_bp.route('/opname/history')
@login_required
def history():
    staff_or_admin()
    all_records = StockOpname.query.order_by(StockOpname.checked_at.desc()).all()
    grouped     = {}
    for r in all_records:
        key = r.checked_at.strftime('%B %Y')
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(r)
    return render_template('opname/history.html', grouped=grouped)