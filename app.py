import os
import secrets
from flask import Flask, render_template
from database import db
from extensions import login_manager, csrf, limiter
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

def create_app():
    app = Flask(__name__)

    # ── Secret Key ────────────────────────────────────────────
    secret = os.environ.get('SECRET_KEY', '')
    if not secret or len(secret) < 32:
        secret = secrets.token_hex(32)
        print('⚠️  WARNING: Using auto-generated SECRET_KEY.')
        print('   Set SECRET_KEY in .env for persistent sessions.')
    app.config['SECRET_KEY'] = secret

    # ── Config ────────────────────────────────────────────────
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['PERMANENT_SESSION_LIFETIME']     = timedelta(hours=8)
    app.config['SESSION_COOKIE_HTTPONLY']        = True
    app.config['SESSION_COOKIE_SAMESITE']        = 'Lax'
    app.config['SESSION_COOKIE_SECURE']          = False  # True jika pakai HTTPS
    app.config['REMEMBER_COOKIE_HTTPONLY']       = True
    app.config['REMEMBER_COOKIE_DURATION']       = timedelta(hours=8)
    app.config['SESSION_REFRESH_EACH_REQUEST']   = True
    app.config['WTF_CSRF_TIME_LIMIT']            = 3600
    app.config['MAX_CONTENT_LENGTH']             = 5 * 1024 * 1024  # 5 MB upload limit (company logo)

    # ── Database ──────────────────────────────────────────────
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///inventrek.db')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+psycopg2://', 1)
    elif database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url

    # ── Extensions ────────────────────────────────────────────
    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view            = 'auth.login'
    login_manager.login_message         = 'Please login to continue.'
    login_manager.login_message_category = 'warning'
    login_manager.refresh_view          = 'auth.login'
    login_manager.needs_refresh_message = 'Session expired, please login again.'

    from models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ── Security Headers ──────────────────────────────────────
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options']        = 'SAMEORIGIN'
        response.headers['X-XSS-Protection']       = '1; mode=block'
        response.headers['Referrer-Policy']        = 'strict-origin-when-cross-origin'
        return response

    # ── Jinja2 filter: display a UTC datetime as WIB (UTC+7) ────────
    from datetime import timedelta as _td
    def _fmt_wib(dt, fmt='%Y-%m-%d %H:%M WIB'):
        """Convert a naive UTC datetime to WIB (UTC+7) and format it."""
        if dt is None:
            return '-'
        return (dt + _td(hours=7)).strftime(fmt)
    app.jinja_env.filters['wib'] = _fmt_wib

    # ── Company logo — available in every template via {{ company_logo_url }} ──
    @app.context_processor
    def inject_company_logo():
        from models import Setting
        logo_path = None
        try:
            row = Setting.query.filter_by(key='company_logo').first()
            logo_path = row.value if row and row.value else None
        except Exception:
            logo_path = None  # e.g. during first-run before tables exist
        if logo_path:
            from flask import url_for
            return {'company_logo_url': url_for('static', filename=logo_path)}
        return {'company_logo_url': None}

    # ── Rate limit error handler ──────────────────────────────
    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return render_template('errors/429.html'), 429

    # ── Blueprints ────────────────────────────────────────────
    from routes.auth      import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.master    import master_bp
    from routes.inventory import inventory_bp
    from routes.opname    import opname_bp
    from routes.reports   import reports_bp
    from routes.users     import users_bp
    from routes.settings  import settings_bp
    from routes.qr        import qr_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(master_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(opname_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(qr_bp)

    # ── Error Handlers ────────────────────────────────────────
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    # ── Database & Seed ───────────────────────────────────────
    os.makedirs(os.path.join(app.static_folder, 'uploads'), exist_ok=True)
    with app.app_context():
        db.create_all()
        seed_initial_data()
        print('✅ InvenTrek ready!')

    return app


def seed_initial_data():
    from models import (User, Category, Brand, Location,
                        Holder, ItemCondition, Unit, Setting)
    from werkzeug.security import generate_password_hash

    if not User.query.first():
        db.session.add(User(
            name     = 'Admin User',
            email    = 'admin@company.com',
            password = generate_password_hash('admin123'),
            role     = 'admin',
            status   = 'active',
        ))

    if not Category.query.first():
        for name in ['Electronics', 'Furniture', 'Stationery',
                     'IT Equipment', 'Sample Products']:
            db.session.add(Category(name=name))

    if not Brand.query.first():
        for name in ['Dell', 'HP', 'Lenovo', 'Apple', 'Samsung',
                     'Canon', 'Logitech', 'Epson']:
            db.session.add(Brand(name=name))

    if not Location.query.first():
        for name, building in [
            ('Main Office',    'Tower A - Floor 3'),
            ('Meeting Room 1', 'Tower A - Floor 3'),
            ('IT Department',  'Tower A - Floor 5'),
            ('Marketing',      'Tower B - Floor 2'),
            ('Warehouse',      'Storage Building'),
        ]:
            db.session.add(Location(name=name, building=building))

    if not ItemCondition.query.first():
        for name in ['Good', 'Minor Damage', 'Repair', 'Lost']:
            db.session.add(ItemCondition(name=name))

    if not Unit.query.first():
        for name in ['pcs', 'box', 'set', 'unit']:
            db.session.add(Unit(name=name))

    if not Setting.query.first():
        for key, value in [
            ('company_name',    'PT. Contoh Perusahaan'),
            ('item_id_format',  'INV-YYYY-###'),
            ('enable_qr',       'true'),
            ('require_serial',  'true'),
            ('email_notif',     'false'),
            ('opname_reminder', 'true'),
        ]:
            db.session.add(Setting(key=key, value=value))

    db.session.commit()


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)