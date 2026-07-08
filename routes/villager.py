from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, send_from_directory
from flask_login import login_required, current_user
from database import db
from models.user import Villager
from models.certificate import Certificate
from models.complaint import Complaint
from models.scheme import Scheme
from models.announcement import Announcement, AnnouncementRead
from models.tax import Tax
from datetime import datetime
import random
import os
from werkzeug.utils import secure_filename

villager_bp = Blueprint('villager', __name__, url_prefix='/villager')

@villager_bp.before_request
@login_required
def check_role():
    if current_user.role != 'villager':
        flash('Access denied. This section is for villagers only.', 'danger')
        return redirect(url_for('main.index'))

@villager_bp.route('/dashboard')
def dashboard():
    cert_count = Certificate.query.filter_by(villager_id=current_user.villager_profile.id).count()
    complaint_count = Complaint.query.filter(
        Complaint.villager_id == current_user.villager_profile.id,
        Complaint.status != 'Resolved'
    ).count()
    scheme_count = Scheme.query.filter_by(is_active=True).count()
    
    active_ann_query = Announcement.query.filter(
        Announcement.is_published == True,
        db.or_(Announcement.scheduled_date == None, Announcement.scheduled_date <= datetime.now())
    )
    announcement_count = active_ann_query.count()
    latest_announcements = active_ann_query.order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc()).limit(3).all()
    
    read_ids = [r.announcement_id for r in AnnouncementRead.query.filter_by(villager_id=current_user.villager_profile.id).all()]
    
    unpaid_taxes = Tax.query.filter(Tax.villager_id == current_user.villager_profile.id, Tax.payment_status.in_(['Unpaid', 'Overdue'])).count()
    total_due_amount = db.session.query(db.func.sum(Tax.amount)).filter(Tax.villager_id == current_user.villager_profile.id, Tax.payment_status.in_(['Unpaid', 'Overdue'])).scalar() or 0.0
    return render_template('villager/dashboard.html', cert_count=cert_count, complaint_count=complaint_count, scheme_count=scheme_count, announcement_count=announcement_count, latest_announcements=latest_announcements, read_ids=read_ids, unpaid_taxes=unpaid_taxes, total_due_amount=total_due_amount)

@villager_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    villager = current_user.villager_profile
    if request.method == 'POST':
        villager.full_name = request.form.get('full_name')
        villager.mobile = request.form.get('mobile')
        villager.address = request.form.get('address')
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('villager.profile'))
    return render_template('villager/profile.html', villager=villager)

@villager_bp.route('/certificates')
def certificates():
    certs = Certificate.query.filter_by(villager_id=current_user.villager_profile.id).order_by(Certificate.submission_date.desc()).all()
    return render_template('villager/certificates.html', certificates=certs)

@villager_bp.route('/certificates/apply', methods=['GET', 'POST'])
def apply_certificate():
    if request.method == 'POST':
        cert_type = request.form.get('type')
        applicant_name = request.form.get('applicant_name')
        address = request.form.get('address')
        mobile = request.form.get('mobile')
        aadhaar = request.form.get('aadhaar')
        document = request.files.get('document')
        
        filename = None
        if document and document.filename != '':
            filename = secure_filename(document.filename)
            document.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            
        cert = Certificate(
            villager_id=current_user.villager_profile.id,
            type=cert_type,
            applicant_name=applicant_name,
            address=address,
            mobile=mobile,
            aadhaar=aadhaar,
            document_filename=filename
        )
        db.session.add(cert)
        db.session.commit()
        flash('Certificate application submitted successfully.', 'success')
        return redirect(url_for('villager.certificates'))
        
    return render_template('villager/apply_certificate.html', villager=current_user.villager_profile)

@villager_bp.route('/certificates/<int:id>/acknowledgement')
def acknowledgement(id):
    cert = db.session.get(Certificate, id)
    if not cert or cert.villager_id != current_user.villager_profile.id:
        flash('Certificate not found or unauthorized', 'danger')
        return redirect(url_for('villager.certificates'))
    return render_template('villager/acknowledgement.html', cert=cert)

@villager_bp.route('/complaints')
def complaints():
    user_complaints = Complaint.query.filter_by(villager_id=current_user.villager_profile.id).order_by(Complaint.date.desc()).all()
    return render_template('villager/complaints.html', complaints=user_complaints)

@villager_bp.route('/complaints/submit', methods=['GET', 'POST'])
def submit_complaint():
    if request.method == 'POST':
        category = request.form.get('category')
        description = request.form.get('description')
        image = request.files.get('image')
        
        filename = None
        if image and image.filename != '':
            filename = secure_filename(image.filename)
            image.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            
        complaint = Complaint(
            villager_id=current_user.villager_profile.id,
            category=category,
            description=description,
            image_filename=filename
        )
        db.session.add(complaint)
        db.session.commit()
        flash('Complaint submitted successfully.', 'success')
        return redirect(url_for('villager.complaints'))
        
    return render_template('villager/submit_complaint.html')

@villager_bp.route('/schemes')
def schemes():
    q = request.args.get('q')
    query = Scheme.query.filter_by(is_active=True)
    if q:
        query = query.filter(Scheme.title.ilike(f'%{q}%') | Scheme.description.ilike(f'%{q}%'))
    active_schemes = query.order_by(Scheme.created_at.desc()).all()
    villager = current_user.villager_profile
    return render_template('villager/schemes.html', schemes=active_schemes, villager=villager)

@villager_bp.route('/schemes/<int:id>')
def scheme_details(id):
    scheme = db.session.get(Scheme, id)
    if not scheme or not scheme.is_active:
        flash('Scheme not found or inactive.', 'danger')
        return redirect(url_for('villager.schemes'))
    villager = current_user.villager_profile
    return render_template('villager/scheme_details.html', scheme=scheme, villager=villager)

@villager_bp.route('/schemes/favourite/<int:id>', methods=['POST'])
def toggle_favourite(id):
    scheme = db.session.get(Scheme, id)
    if not scheme:
        flash('Scheme not found.', 'danger')
        return redirect(url_for('villager.schemes'))
    villager = current_user.villager_profile
    if scheme in villager.favourite_schemes.all():
        villager.favourite_schemes.remove(scheme)
        flash(f'Removed "{scheme.title}" from your favourites.', 'info')
    else:
        villager.favourite_schemes.append(scheme)
        flash(f'Added "{scheme.title}" to your favourites!', 'success')
    db.session.commit()
    redirect_url = request.form.get('next') or url_for('villager.schemes')
    return redirect(redirect_url)

@villager_bp.route('/schemes/favourites')
def favourites():
    villager = current_user.villager_profile
    fav_schemes = villager.favourite_schemes.all()
    return render_template('villager/favourites.html', schemes=fav_schemes, villager=villager)

@villager_bp.route('/announcements')
def announcements():
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    
    query = Announcement.query.filter(
        Announcement.is_published == True,
        db.or_(Announcement.scheduled_date == None, Announcement.scheduled_date <= datetime.now())
    )
    if q:
        query = query.filter(db.or_(Announcement.title.ilike(f'%{q}%'), Announcement.content.ilike(f'%{q}%')))
    if category and category != 'All':
        query = query.filter(Announcement.category == category)
        
    published_announcements = query.order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc()).all()
    read_ids = [r.announcement_id for r in AnnouncementRead.query.filter_by(villager_id=current_user.villager_profile.id).all()]
    return render_template('villager/announcements.html', announcements=published_announcements, read_ids=read_ids, selected_category=category, q=q)

@villager_bp.route('/announcements/read/<int:id>')
def read_announcement(id):
    announcement = db.session.get(Announcement, id)
    if announcement:
        villager_id = current_user.villager_profile.id
        existing = AnnouncementRead.query.filter_by(announcement_id=id, villager_id=villager_id).first()
        if not existing:
            read_record = AnnouncementRead(announcement_id=id, villager_id=villager_id)
            db.session.add(read_record)
            db.session.commit()
    return redirect(url_for('villager.announcements'))

@villager_bp.route('/announcements/read_all')
def read_all_announcements():
    villager_id = current_user.villager_profile.id
    active_announcements = Announcement.query.filter(
        Announcement.is_published == True,
        db.or_(Announcement.scheduled_date == None, Announcement.scheduled_date <= datetime.now())
    ).all()
    read_ids = [r.announcement_id for r in AnnouncementRead.query.filter_by(villager_id=villager_id).all()]
    for a in active_announcements:
        if a.id not in read_ids:
            read_record = AnnouncementRead(announcement_id=a.id, villager_id=villager_id)
            db.session.add(read_record)
    db.session.commit()
    flash('All announcements marked as read.', 'success')
    return redirect(url_for('villager.announcements'))

@villager_bp.route('/announcements/download/<int:id>')
def download_announcement_attachment(id):
    announcement = db.session.get(Announcement, id)
    if announcement and announcement.attachment_filename:
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], announcement.attachment_filename, as_attachment=True)
    flash('Attachment not found.', 'danger')
    return redirect(url_for('villager.announcements'))

@villager_bp.route('/taxes')
def taxes():
    villager_id = current_user.villager_profile.id
    all_taxes = Tax.query.filter_by(villager_id=villager_id).order_by(Tax.due_date.desc()).all()
    
    # Calculate summary metrics
    total_due = db.session.query(db.func.sum(Tax.amount)).filter(Tax.villager_id==villager_id, Tax.payment_status.in_(['Unpaid', 'Overdue'])).scalar() or 0.0
    prop_tax = db.session.query(db.func.sum(Tax.amount)).filter(Tax.villager_id==villager_id, Tax.tax_type=='Property Tax', Tax.payment_status.in_(['Unpaid', 'Overdue'])).scalar() or 0.0
    house_tax = db.session.query(db.func.sum(Tax.amount)).filter(Tax.villager_id==villager_id, Tax.tax_type=='House Tax', Tax.payment_status.in_(['Unpaid', 'Overdue'])).scalar() or 0.0
    water_tax = db.session.query(db.func.sum(Tax.amount)).filter(Tax.villager_id==villager_id, Tax.tax_type=='Water Tax', Tax.payment_status.in_(['Unpaid', 'Overdue'])).scalar() or 0.0
    
    paid_taxes = [t for t in all_taxes if t.payment_status == 'Paid']
    unpaid_taxes = [t for t in all_taxes if t.payment_status in ['Unpaid', 'Overdue']]
    
    return render_template('villager/taxes.html', taxes=all_taxes, paid_taxes=paid_taxes, unpaid_taxes=unpaid_taxes, total_due=total_due, prop_tax=prop_tax, house_tax=house_tax, water_tax=water_tax)

@villager_bp.route('/taxes/pay/<int:id>', methods=['POST'])
def pay_tax(id):
    tax = db.session.get(Tax, id)
    if not tax or tax.villager_id != current_user.villager_profile.id:
        flash('Tax record not found or access denied.', 'danger')
        return redirect(url_for('villager.taxes'))
        
    if tax.payment_status == 'Paid':
        flash('This tax bill has already been paid.', 'info')
    else:
        tax.payment_status = 'Paid'
        tax.payment_date = datetime.utcnow()
        tax.receipt_number = f"RCP-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        db.session.commit()
        flash(f'Online Payment successful! Receipt generated: {tax.receipt_number}', 'success')
        
    return redirect(url_for('villager.taxes'))

@villager_bp.route('/taxes/receipt/<int:id>')
def tax_receipt(id):
    tax = db.session.get(Tax, id)
    if not tax or tax.villager_id != current_user.villager_profile.id or tax.payment_status != 'Paid':
        flash('Valid payment receipt not found.', 'danger')
        return redirect(url_for('villager.taxes'))
    return render_template('villager/tax_receipt.html', tax=tax)



