from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, jsonify, abort)
from flask_login import login_required, current_user
from database import db
from models import Category, Brand, Location, Holder, ItemCondition, Unit

master_bp = Blueprint('master', __name__)

# ── Helper ────────────────────────────────────────────────────
def admin_only():
    if current_user.role != 'admin':
        abort(403)

# ══════════════════════════════════════════════════════════════
# CATEGORIES
# ══════════════════════════════════════════════════════════════
@master_bp.route('/master/categories')
@login_required
def categories():
    admin_only()
    items = Category.query.order_by(Category.id).all()
    return render_template('master/categories.html', items=items)

@master_bp.route('/master/categories/add', methods=['POST'])
@login_required
def add_category():
    admin_only()
    name        = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    if not name:
        flash('Category name is required.', 'error')
        return redirect(url_for('master.categories'))
    if Category.query.filter_by(name=name).first():
        flash('Category already exists.', 'error')
        return redirect(url_for('master.categories'))
    db.session.add(Category(name=name, description=description))
    db.session.commit()
    flash(f'Category "{name}" added successfully.', 'success')
    return redirect(url_for('master.categories'))

@master_bp.route('/master/categories/<int:id>/edit', methods=['POST'])
@login_required
def edit_category(id):
    admin_only()
    cat  = Category.query.get_or_404(id)
    name = request.form.get('name', '').strip()
    desc = request.form.get('description', '').strip()
    if not name:
        flash('Category name is required.', 'error')
        return redirect(url_for('master.categories'))
    cat.name        = name
    cat.description = desc
    db.session.commit()
    flash('Category updated.', 'success')
    return redirect(url_for('master.categories'))

@master_bp.route('/master/categories/<int:id>/delete', methods=['POST'])
@login_required
def delete_category(id):
    admin_only()
    cat = Category.query.get_or_404(id)
    if cat.items:
        flash('Cannot delete — category has items.', 'error')
        return redirect(url_for('master.categories'))
    db.session.delete(cat)
    db.session.commit()
    flash('Category deleted.', 'success')
    return redirect(url_for('master.categories'))

@master_bp.route('/master/categories/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_category(id):
    admin_only()
    cat        = Category.query.get_or_404(id)
    cat.status = 'inactive' if cat.status == 'active' else 'active'
    db.session.commit()
    return jsonify({'status': cat.status})

# ══════════════════════════════════════════════════════════════
# BRANDS
# ══════════════════════════════════════════════════════════════
@master_bp.route('/master/brands')
@login_required
def brands():
    admin_only()
    items = Brand.query.order_by(Brand.id).all()
    return render_template('master/brands.html', items=items)

@master_bp.route('/master/brands/add', methods=['POST'])
@login_required
def add_brand():
    admin_only()
    name = request.form.get('name', '').strip()
    if not name:
        flash('Brand name is required.', 'error')
        return redirect(url_for('master.brands'))
    if Brand.query.filter_by(name=name).first():
        flash('Brand already exists.', 'error')
        return redirect(url_for('master.brands'))
    db.session.add(Brand(name=name))
    db.session.commit()
    flash(f'Brand "{name}" added.', 'success')
    return redirect(url_for('master.brands'))

@master_bp.route('/master/brands/<int:id>/edit', methods=['POST'])
@login_required
def edit_brand(id):
    admin_only()
    brand      = Brand.query.get_or_404(id)
    name       = request.form.get('name', '').strip()
    if not name:
        flash('Brand name is required.', 'error')
        return redirect(url_for('master.brands'))
    brand.name = name
    db.session.commit()
    flash('Brand updated.', 'success')
    return redirect(url_for('master.brands'))

@master_bp.route('/master/brands/<int:id>/delete', methods=['POST'])
@login_required
def delete_brand(id):
    admin_only()
    brand = Brand.query.get_or_404(id)
    if brand.items:
        flash('Cannot delete — brand has items.', 'error')
        return redirect(url_for('master.brands'))
    db.session.delete(brand)
    db.session.commit()
    flash('Brand deleted.', 'success')
    return redirect(url_for('master.brands'))

# ══════════════════════════════════════════════════════════════
# LOCATIONS
# ══════════════════════════════════════════════════════════════
@master_bp.route('/master/locations')
@login_required
def locations():
    admin_only()
    items = Location.query.order_by(Location.id).all()
    return render_template('master/locations.html', items=items)

@master_bp.route('/master/locations/add', methods=['POST'])
@login_required
def add_location():
    admin_only()
    name     = request.form.get('name', '').strip()
    building = request.form.get('building', '').strip()
    if not name:
        flash('Location name is required.', 'error')
        return redirect(url_for('master.locations'))
    db.session.add(Location(name=name, building=building))
    db.session.commit()
    flash(f'Location "{name}" added.', 'success')
    return redirect(url_for('master.locations'))

@master_bp.route('/master/locations/<int:id>/edit', methods=['POST'])
@login_required
def edit_location(id):
    admin_only()
    loc          = Location.query.get_or_404(id)
    loc.name     = request.form.get('name', '').strip()
    loc.building = request.form.get('building', '').strip()
    db.session.commit()
    flash('Location updated.', 'success')
    return redirect(url_for('master.locations'))

@master_bp.route('/master/locations/<int:id>/delete', methods=['POST'])
@login_required
def delete_location(id):
    admin_only()
    loc = Location.query.get_or_404(id)
    if loc.items:
        flash('Cannot delete — location has items.', 'error')
        return redirect(url_for('master.locations'))
    db.session.delete(loc)
    db.session.commit()
    flash('Location deleted.', 'success')
    return redirect(url_for('master.locations'))

# ══════════════════════════════════════════════════════════════
# HOLDERS / PIC
# ══════════════════════════════════════════════════════════════
@master_bp.route('/master/holders')
@login_required
def holders():
    admin_only()
    items = Holder.query.order_by(Holder.id).all()
    return render_template('master/holders.html', items=items)

@master_bp.route('/master/holders/add', methods=['POST'])
@login_required
def add_holder():
    admin_only()
    name     = request.form.get('name', '').strip()
    division = request.form.get('division', '').strip()
    email    = request.form.get('email', '').strip()
    if not name:
        flash('Holder name is required.', 'error')
        return redirect(url_for('master.holders'))
    db.session.add(Holder(name=name, division=division, email=email))
    db.session.commit()
    flash(f'Holder "{name}" added.', 'success')
    return redirect(url_for('master.holders'))

@master_bp.route('/master/holders/<int:id>/edit', methods=['POST'])
@login_required
def edit_holder(id):
    admin_only()
    h          = Holder.query.get_or_404(id)
    h.name     = request.form.get('name', '').strip()
    h.division = request.form.get('division', '').strip()
    h.email    = request.form.get('email', '').strip()
    db.session.commit()
    flash('Holder updated.', 'success')
    return redirect(url_for('master.holders'))

@master_bp.route('/master/holders/<int:id>/delete', methods=['POST'])
@login_required
def delete_holder(id):
    admin_only()
    h = Holder.query.get_or_404(id)
    if h.items:
        flash('Cannot delete — holder has items.', 'error')
        return redirect(url_for('master.holders'))
    db.session.delete(h)
    db.session.commit()
    flash('Holder deleted.', 'success')
    return redirect(url_for('master.holders'))

# ══════════════════════════════════════════════════════════════
# ITEM CONDITIONS
# ══════════════════════════════════════════════════════════════
@master_bp.route('/master/conditions')
@login_required
def conditions():
    admin_only()
    items = ItemCondition.query.order_by(ItemCondition.id).all()
    return render_template('master/conditions.html', items=items)

@master_bp.route('/master/conditions/add', methods=['POST'])
@login_required
def add_condition():
    admin_only()
    name = request.form.get('name', '').strip()
    if not name:
        flash('Condition name is required.', 'error')
        return redirect(url_for('master.conditions'))
    if ItemCondition.query.filter_by(name=name).first():
        flash('Condition already exists.', 'error')
        return redirect(url_for('master.conditions'))
    db.session.add(ItemCondition(name=name))
    db.session.commit()
    flash(f'Condition "{name}" added.', 'success')
    return redirect(url_for('master.conditions'))

@master_bp.route('/master/conditions/<int:id>/edit', methods=['POST'])
@login_required
def edit_condition(id):
    admin_only()
    cond      = ItemCondition.query.get_or_404(id)
    cond.name = request.form.get('name', '').strip()
    db.session.commit()
    flash('Condition updated.', 'success')
    return redirect(url_for('master.conditions'))

@master_bp.route('/master/conditions/<int:id>/delete', methods=['POST'])
@login_required
def delete_condition(id):
    admin_only()
    cond = ItemCondition.query.get_or_404(id)
    if cond.items:
        flash('Cannot delete — condition has items.', 'error')
        return redirect(url_for('master.conditions'))
    db.session.delete(cond)
    db.session.commit()
    flash('Condition deleted.', 'success')
    return redirect(url_for('master.conditions'))

# ══════════════════════════════════════════════════════════════
# UNITS
# ══════════════════════════════════════════════════════════════
@master_bp.route('/master/units')
@login_required
def units():
    admin_only()
    items = Unit.query.order_by(Unit.id).all()
    return render_template('master/units.html', items=items)

@master_bp.route('/master/units/add', methods=['POST'])
@login_required
def add_unit():
    admin_only()
    name = request.form.get('name', '').strip()
    if not name:
        flash('Unit name is required.', 'error')
        return redirect(url_for('master.units'))
    if Unit.query.filter_by(name=name).first():
        flash('Unit already exists.', 'error')
        return redirect(url_for('master.units'))
    db.session.add(Unit(name=name))
    db.session.commit()
    flash(f'Unit "{name}" added.', 'success')
    return redirect(url_for('master.units'))

@master_bp.route('/master/units/<int:id>/edit', methods=['POST'])
@login_required
def edit_unit(id):
    admin_only()
    unit      = Unit.query.get_or_404(id)
    unit.name = request.form.get('name', '').strip()
    db.session.commit()
    flash('Unit updated.', 'success')
    return redirect(url_for('master.units'))

@master_bp.route('/master/units/<int:id>/delete', methods=['POST'])
@login_required
def delete_unit(id):
    admin_only()
    unit = Unit.query.get_or_404(id)
    if unit.items:
        flash('Cannot delete — unit has items.', 'error')
        return redirect(url_for('master.units'))
    db.session.delete(unit)
    db.session.commit()
    flash('Unit deleted.', 'success')
    return redirect(url_for('master.units'))