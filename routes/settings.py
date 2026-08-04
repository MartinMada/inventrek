from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, abort)
from flask_login import login_required, current_user
from database import db
from models import Setting, User, Item

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings')
@login_required
def index():
    if current_user.role != 'admin':
        abort(403)
    settings    = {s.key: s.value for s in Setting.query.all()}
    total_items = Item.query.count()
    total_users = User.query.count()
    return render_template('settings/index.html',
        settings=settings,
        total_items=total_items,
        total_users=total_users,
    )

@settings_bp.route('/settings/save', methods=['POST'])
@login_required
def save():
    if current_user.role != 'admin':
        abort(403)
    keys = ['company_name', 'item_id_format', 'enable_qr',
            'require_serial', 'email_notif', 'opname_reminder']
    for key in keys:
        setting = Setting.query.filter_by(key=key).first()
        if not setting:
            setting = Setting(key=key)
            db.session.add(setting)
        if key in ['enable_qr', 'require_serial',
                   'email_notif', 'opname_reminder']:
            setting.value = 'true' if request.form.get(key) else 'false'
        else:
            setting.value = request.form.get(key, '').strip()
    db.session.commit()
    flash('Settings saved successfully.', 'success')
    return redirect(url_for('settings.index'))