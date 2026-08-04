from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, abort)
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from database import db
from models import User

users_bp = Blueprint('users', __name__)

@users_bp.route('/users')
@login_required
def index():
    if current_user.role != 'admin':
        abort(403)
    users       = User.query.order_by(User.id).all()
    admin_count = sum(1 for u in users if u.role == 'admin')
    staff_count = sum(1 for u in users if u.role == 'staff')
    pic_count   = sum(1 for u in users if u.role == 'pic')
    return render_template('users/index.html',
        users=users,
        admin_count=admin_count,
        staff_count=staff_count,
        pic_count=pic_count,
    )

@users_bp.route('/users/add', methods=['POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        abort(403)
    name     = request.form.get('name', '').strip()
    email    = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    role     = request.form.get('role', 'staff')
    if not name or not email or not password:
        flash('Name, email and password are required.', 'error')
        return redirect(url_for('users.index'))
    if User.query.filter_by(email=email).first():
        flash('Email already exists.', 'error')
        return redirect(url_for('users.index'))
    db.session.add(User(
        name     = name,
        email    = email,
        password = generate_password_hash(password),
        role     = role,
        status   = 'active'
    ))
    db.session.commit()
    flash(f'User "{name}" added successfully.', 'success')
    return redirect(url_for('users.index'))

@users_bp.route('/users/<int:id>/edit', methods=['POST'])
@login_required
def edit_user(id):
    if current_user.role != 'admin':
        abort(403)
    user        = User.query.get_or_404(id)
    user.name   = request.form.get('name', '').strip()
    user.role   = request.form.get('role', 'staff')
    user.status = request.form.get('status', 'active')
    new_pass    = request.form.get('password', '').strip()
    if new_pass:
        user.password = generate_password_hash(new_pass)
    db.session.commit()
    flash('User updated successfully.', 'success')
    return redirect(url_for('users.index'))

@users_bp.route('/users/<int:id>/delete', methods=['POST'])
@login_required
def delete_user(id):
    if current_user.role != 'admin':
        abort(403)
    if id == current_user.id:
        flash('Cannot delete your own account.', 'error')
        return redirect(url_for('users.index'))
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted.', 'success')
    return redirect(url_for('users.index'))