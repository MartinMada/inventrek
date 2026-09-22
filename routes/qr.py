from flask import (Blueprint, render_template, send_file,
                   abort, request, jsonify, flash, redirect, url_for)
from flask_login import login_required, current_user
from models import Item
import qrcode
import qrcode.image.svg
import io
import base64

qr_bp = Blueprint('qr', __name__)

def generate_qr_base64(data: str, box_size: int = 8) -> str:
    """Generate QR code dan return sebagai base64 PNG string."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=3,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img    = qr.make_image(fill_color='black', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


@qr_bp.route('/qr/<int:item_id>/image')
@login_required
def qr_image(item_id):
    """Return QR code sebagai PNG file download."""
    item = Item.query.get_or_404(item_id)
    if not item.qr_token:
        flash(f'"{item.name}" does not have a QR code yet '
              f'(QR generation was disabled when it was added).', 'error')
        return redirect(url_for('qr.item_detail', item_id=item.id))

    qr   = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=8,
        border=3,
    )
    qr.add_data(item.qr_token)
    qr.make(fit=True)
    img    = qr.make_image(fill_color='black', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype='image/png',
        as_attachment=True,
        download_name=f'QR-{item.item_code}.png'
    )


@qr_bp.route('/qr/<int:item_id>/detail')
@login_required
def item_detail(item_id):
    """Halaman detail item + QR Code."""
    item   = Item.query.get_or_404(item_id)
    qr_b64 = generate_qr_base64(item.qr_token, box_size=10) if item.qr_token else None
    return render_template('qr/item_detail.html',
        item=item, qr_b64=qr_b64)


@qr_bp.route('/qr/print')
@login_required
def print_qr():
    """
    Halaman print QR.
    ?ids=1,2,3  → print multiple items
    ?id=1       → print single item
    """
    id_param  = request.args.get('ids', '') or request.args.get('id', '')
    if not id_param:
        abort(400)

    ids   = [int(i) for i in id_param.split(',') if i.strip().isdigit()]
    items = Item.query.filter(Item.id.in_(ids)).all()

    if not items:
        abort(404)

    # Only items that actually have a QR token can be printed
    printable   = [i for i in items if i.qr_token]
    skipped_ct  = len(items) - len(printable)

    if not printable:
        flash('None of the selected items have a QR code generated. '
              'Enable "QR Code Generation" in Settings, then re-add or edit the item(s).', 'error')
        return redirect(request.referrer or url_for('inventory.all_items'))

    if skipped_ct:
        flash(f'{skipped_ct} selected item(s) skipped — they don\u2019t have a QR code generated.', 'error')

    # Generate QR untuk setiap item
    items_with_qr = []
    for item in printable:
        qr_b64 = generate_qr_base64(item.qr_token, box_size=8)
        items_with_qr.append({
            'item'   : item,
            'qr_b64' : qr_b64,
        })

    return render_template('qr/print.html',
        items_with_qr=items_with_qr,
        total=len(items_with_qr))


@qr_bp.route('/qr/batch-print', methods=['POST'])
@login_required
def batch_print():
    """Terima list ID dari form → redirect ke print page."""
    ids = request.form.getlist('selected_ids')
    if not ids:
        flash('No items selected for printing.', 'error')
        return redirect(request.referrer or url_for('inventory.all_items'))
    return redirect(url_for('qr.print_qr', ids=','.join(ids)))