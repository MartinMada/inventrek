from database import db
from flask_login import UserMixin
from datetime import datetime
import secrets

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(200), nullable=False)
    role       = db.Column(db.String(20), default='staff')
    # role: admin, staff, pic
    status     = db.Column(db.String(10), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.name}>'

class Category(db.Model):
    __tablename__ = 'categories'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    status      = db.Column(db.String(10), default='active')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('Item', backref='category', lazy=True)


class Brand(db.Model):
    __tablename__ = 'brands'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    status     = db.Column(db.String(10), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('Item', backref='brand', lazy=True)


class Location(db.Model):
    __tablename__ = 'locations'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    building   = db.Column(db.String(100), nullable=True)
    status     = db.Column(db.String(10), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('Item', backref='location', lazy=True)


class Holder(db.Model):
    __tablename__ = 'holders'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    division   = db.Column(db.String(100), nullable=True)
    email      = db.Column(db.String(120), nullable=True)
    status     = db.Column(db.String(10), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('Item', backref='holder', lazy=True)


class ItemCondition(db.Model):
    __tablename__ = 'item_conditions'

    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    items   = db.relationship('Item', backref='condition', lazy=True)
    opnames = db.relationship('StockOpname', backref='condition', lazy=True)


class Unit(db.Model):
    __tablename__ = 'units'

    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    items = db.relationship('Item', backref='unit', lazy=True)

class Item(db.Model):
    __tablename__ = 'items'

    id            = db.Column(db.Integer, primary_key=True)
    item_code     = db.Column(db.String(50), unique=True, nullable=False)
    name          = db.Column(db.String(200), nullable=False)
    item_type     = db.Column(db.String(20), default='general')
    # item_type: general, electronic, sample

    category_id   = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    brand_id      = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=True)
    unit_id       = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    condition_id  = db.Column(db.Integer, db.ForeignKey('item_conditions.id'), nullable=True)
    location_id   = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)
    holder_id     = db.Column(db.Integer, db.ForeignKey('holders.id'), nullable=True)

    quantity      = db.Column(db.Integer, default=1)
    unit_price    = db.Column(db.Float, default=0)
    purchase_date = db.Column(db.Date, nullable=True)
    status        = db.Column(db.String(20), default='available')
    # status: available, in_use, damaged, lost

    # Electronic specific
    model         = db.Column(db.String(100), nullable=True)
    serial_number = db.Column(db.String(100), nullable=True)

    # QR Code
    qr_token      = db.Column(db.String(32), unique=True,
                               default=lambda: secrets.token_hex(16))

    notes         = db.Column(db.Text, nullable=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # opnames = db.relationship('StockOpname', backref='item', lazy=True)

    # ── Relationships ─────────────────────────────────────────
    opname_records = db.relationship('StockOpname', backref='item',
                                     lazy=True, cascade='all, delete-orphan')

    @property
    def total_value(self):
        return self.unit_price * self.quantity

    def to_dict(self):
        return {
            'id'         : self.id,
            'item_code'  : self.item_code,
            'name'       : self.name,
            'category'   : self.category.name if self.category else '-',
            'brand'      : self.brand.name if self.brand else '-',
            'quantity'   : self.quantity,
            'unit'       : self.unit.name if self.unit else 'pcs',
            'condition'  : self.condition.name if self.condition else '-',
            'location'   : self.location.name if self.location else '-',
            'holder'     : self.holder.name if self.holder else '-',
            'status'     : self.status,
            'unit_price' : self.unit_price,
            'total_value': self.total_value,
        }


class StockOpname(db.Model):
    __tablename__ = 'stock_opname'

    id           = db.Column(db.Integer, primary_key=True)
    opname_code  = db.Column(db.String(50), unique=True, nullable=False)
    item_id      = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    checker_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    condition_id = db.Column(db.Integer, db.ForeignKey('item_conditions.id'), nullable=True)
    location_id  = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)
    notes        = db.Column(db.Text, nullable=True)
    checked_at   = db.Column(db.DateTime, default=datetime.utcnow)

    checker  = db.relationship('User', backref='opnames')
    location = db.relationship('Location', foreign_keys=[location_id])

    def to_dict(self):
        return {
            'id'          : self.id,
            'opname_code' : self.opname_code,
            'item_id'     : self.item_id,
            'item_name'   : self.item.name,
            'item_code'   : self.item.item_code,
            'condition'   : self.condition.name if self.condition else '-',
            'location'    : self.location.name if self.location else '-',
            'checker'     : self.checker.name if self.checker else '-',
            'notes'       : self.notes,
            'checked_at'  : self.checked_at.strftime('%Y-%m-%d'),
        }


class Setting(db.Model):
    __tablename__ = 'settings'

    id    = db.Column(db.Integer, primary_key=True)
    key   = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)