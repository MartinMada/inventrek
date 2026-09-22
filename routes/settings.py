import os
from datetime import datetime
from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, abort, current_app, send_file)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from database import db
from models import Setting, User, Item

settings_bp = Blueprint('settings', __name__)

ALLOWED_LOGO_EXT = {'png', 'jpg', 'jpeg', 'svg', 'webp'}


def get_setting(key, default=None):
    row = Setting.query.filter_by(key=key).first()
    return row.value if row and row.value not in (None, '') else default


def set_setting(key, value):
    row = Setting.query.filter_by(key=key).first()
    if not row:
        row = Setting(key=key)
        db.session.add(row)
    row.value = value
    return row


@settings_bp.route('/settings')
@login_required
def index():
    if current_user.role != 'admin':
        abort(403)
    settings    = {s.key: s.value for s in Setting.query.all()}
    total_items = Item.query.count()
    total_users = User.query.count()

    last_backup_display = None
    last_backup_raw = settings.get('last_backup_at')
    if last_backup_raw:
        try:
            dt = datetime.fromisoformat(last_backup_raw)
            last_backup_display = dt.strftime('%d %b %Y, %H:%M') + ' UTC'
        except ValueError:
            last_backup_display = last_backup_raw

    return render_template('settings/index.html',
        settings=settings,
        total_items=total_items,
        total_users=total_users,
        last_backup_display=last_backup_display,
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

    # ── Company logo upload (optional — only replaces existing if a new file is picked) ──
    file = request.files.get('company_logo')
    if file and file.filename:
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext not in ALLOWED_LOGO_EXT:
            flash('Logo file must be PNG, JPG, JPEG, WEBP, or SVG.', 'error')
            return redirect(url_for('settings.index'))

        filename  = secure_filename(f'company_logo.{ext}')
        upload_dir = os.path.join(current_app.static_folder, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        # remove any previous logo file (different extension) so old ones don't pile up
        for old_ext in ALLOWED_LOGO_EXT:
            old_path = os.path.join(upload_dir, f'company_logo.{old_ext}')
            if os.path.exists(old_path):
                os.remove(old_path)

        file.save(os.path.join(upload_dir, filename))
        set_setting('company_logo', f'uploads/{filename}')

    db.session.commit()
    flash('Settings saved successfully.', 'success')
    return redirect(url_for('settings.index'))


@settings_bp.route('/settings/backup', methods=['POST'])
@login_required
def backup():
    """Manual backup — streams a snapshot of the SQLite database file
    to the browser as a download. Only supports SQLite; other database
    engines (e.g. Postgres in production) should be backed up through
    the database provider's own backup tooling."""
    if current_user.role != 'admin':
        abort(403)

    uri = current_app.config['SQLALCHEMY_DATABASE_URI']
    if not uri.startswith('sqlite:///'):
        flash('Manual backup download only supports SQLite. '
              'For other databases, please use your provider\u2019s backup tool.', 'error')
        return redirect(url_for('settings.index'))

    db_file = uri.replace('sqlite:///', '', 1)
    db_path = db_file if os.path.isabs(db_file) else os.path.join(current_app.instance_path, db_file)

    if not os.path.exists(db_path):
        flash('Database file could not be found on the server.', 'error')
        return redirect(url_for('settings.index'))

    set_setting('last_backup_at', datetime.utcnow().isoformat())
    db.session.commit()

    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    return send_file(db_path, as_attachment=True,
                      download_name=f'inventrek_backup_{ts}.db')