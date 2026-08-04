from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, session, make_response)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from database import db
from models import User
from extensions import limiter

auth_bp = Blueprint('auth', __name__)


# Home redirect
@auth_bp.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))


# Login
@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('10 per minute', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not email or not password:
            flash('Email and password are required.', 'error')
            return render_template('auth/login.html')

        user = User.query.filter_by(email=email, status='active').first()

        if not user or not check_password_hash(user.password, password):
            flash('Invalid email or password.', 'error')
            return render_template('auth/login.html')

        login_user(user, remember=remember)
        session.permanent = True

        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect(url_for('dashboard.index'))

    return render_template('auth/login.html')


# Change Password
@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current  = request.form.get('current_password', '')
        new_pass = request.form.get('new_password', '')
        confirm  = request.form.get('confirm_password', '')

        if not check_password_hash(current_user.password, current):
            flash('Current password is incorrect.', 'error')
            return render_template('auth/change_password.html')

        if len(new_pass) < 8:
            flash('New password must be at least 8 characters.', 'error')
            return render_template('auth/change_password.html')

        if new_pass != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('auth/change_password.html')

        current_user.password = generate_password_hash(new_pass)
        db.session.commit()
        flash('Password changed successfully.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/change_password.html')


# Logout
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    resp = make_response(redirect(url_for('auth.login')))
    resp.delete_cookie('session')
    resp.delete_cookie('remember_token')
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma']        = 'no-cache'
    resp.headers['Expires']       = '0'
    flash('You have been logged out successfully.', 'success')
    return resp