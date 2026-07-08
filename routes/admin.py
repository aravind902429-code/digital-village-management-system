from flask import Blueprint, render_template, request, flash, redirect, url_for, send_from_directory, current_app
from flask_login import login_required, current_user
from database import db
from models.user import Villager, User
from models.certificate import Certificate
from models.complaint import Complaint
from models.scheme import Scheme, favourite_schemes
from models.announcement import Announcement
from models.tax import Tax
from datetime import datetime, date, timedelta
import random
import os
import csv
import io
from flask import Response
from werkzeug.utils import secure_filename

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@login_required
def check_role():
    if current_user.role != 'admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('main.index'))

@admin_bp.route('/dashboard')
def dashboard():
    villager_count = Villager.query.count()
    pending_certs = Certificate.query.filter_by(status='Pending').count()
    pending_complaints = Complaint.query.filter_by(status='Pending').count()
    active_schemes = Scheme.query.filter_by(is_active=True).count()
    total_taxes = Tax.query.count()
    total_revenue = db.session.query(db.func.sum(Tax.amount)).filter_by(payment_status='Paid').scalar() or 0.0
    return render_template('admin/dashboard.html', villager_count=villager_count, pending_certs=pending_certs, pending_complaints=pending_complaints, active_schemes=active_schemes, total_taxes=total_taxes, total_revenue=total_revenue)

@admin_bp.route('/certificates')
def certificates():
    status_filter = request.args.get('status')
    if status_filter:
        certs = Certificate.query.filter_by(status=status_filter).order_by(Certificate.submission_date.desc()).all()
    else:
        certs = Certificate.query.order_by(Certificate.submission_date.desc()).all()
    return render_template('admin/certificates.html', certificates=certs)

@admin_bp.route('/certificates/update/<int:id>', methods=['POST'])
def update_certificate(id):
    cert = db.session.get(Certificate, id)
    if not cert:
        return "Certificate not found", 404
    cert.status = request.form.get('status')
    cert.remarks = request.form.get('remarks')
    db.session.commit()
    flash(f'Certificate {id} updated successfully.', 'success')
    return redirect(url_for('admin.certificates'))

@admin_bp.route('/complaints')
def complaints():
    status_filter = request.args.get('status')
    if status_filter:
        cmplts = Complaint.query.filter_by(status=status_filter).order_by(Complaint.date.desc()).all()
    else:
        cmplts = Complaint.query.order_by(Complaint.date.desc()).all()
    return render_template('admin/complaints.html', complaints=cmplts)

@admin_bp.route('/complaints/update/<int:id>', methods=['POST'])
def update_complaint(id):
    complaint = db.session.get(Complaint, id)
    if not complaint:
        return "Complaint not found", 404
    complaint.status = request.form.get('status')
    complaint.remarks = request.form.get('remarks')
    db.session.commit()
    flash(f'Complaint {id} updated successfully.', 'success')
    return redirect(url_for('admin.complaints'))
    
@admin_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@admin_bp.route('/schemes')
def schemes():
    all_schemes = Scheme.query.order_by(Scheme.created_at.desc()).all()
    return render_template('admin/schemes.html', schemes=all_schemes)

@admin_bp.route('/schemes/add', methods=['GET', 'POST'])
def add_scheme():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        eligibility = request.form.get('eligibility')
        benefits = request.form.get('benefits')
        image = request.files.get('image')
        
        filename = None
        if image and image.filename != '':
            filename = secure_filename(image.filename)
            image.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            
        scheme = Scheme(
            title=title,
            description=description,
            eligibility=eligibility,
            benefits=benefits,
            image_filename=filename
        )
        db.session.add(scheme)
        db.session.commit()
        flash('Government Scheme added successfully.', 'success')
        return redirect(url_for('admin.schemes'))
    return render_template('admin/add_scheme.html')

@admin_bp.route('/schemes/edit/<int:id>', methods=['GET', 'POST'])
def edit_scheme(id):
    scheme = db.session.get(Scheme, id)
    if not scheme:
        flash('Scheme not found.', 'danger')
        return redirect(url_for('admin.schemes'))
        
    if request.method == 'POST':
        scheme.title = request.form.get('title')
        scheme.description = request.form.get('description')
        scheme.eligibility = request.form.get('eligibility')
        scheme.benefits = request.form.get('benefits')
        scheme.is_active = True if request.form.get('is_active') else False
        
        image = request.files.get('image')
        if image and image.filename != '':
            filename = secure_filename(image.filename)
            image.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            scheme.image_filename = filename
            
        db.session.commit()
        flash('Government Scheme updated successfully.', 'success')
        return redirect(url_for('admin.schemes'))
    return render_template('admin/edit_scheme.html', scheme=scheme)

@admin_bp.route('/schemes/delete/<int:id>', methods=['POST'])
def delete_scheme(id):
    scheme = db.session.get(Scheme, id)
    if scheme:
        db.session.delete(scheme)
        db.session.commit()
        flash('Government Scheme deleted successfully.', 'success')
    else:
        flash('Scheme not found.', 'danger')
    return redirect(url_for('admin.schemes'))

@admin_bp.route('/announcements')
def announcements():
    all_announcements = Announcement.query.order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc()).all()
    return render_template('admin/announcements.html', announcements=all_announcements)

@admin_bp.route('/announcements/add', methods=['GET', 'POST'])
def add_announcement():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category') or 'General'
        is_published = True if request.form.get('is_published') else False
        is_pinned = True if request.form.get('is_pinned') else False
        
        scheduled_date = None
        sched_str = request.form.get('scheduled_date')
        if sched_str:
            try:
                if 'T' in sched_str:
                    scheduled_date = datetime.strptime(sched_str, '%Y-%m-%dT%H:%M')
                else:
                    scheduled_date = datetime.strptime(sched_str, '%Y-%m-%d')
            except ValueError:
                pass
                
        attachment_filename = None
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                # Append timestamp to avoid overwrite
                filename = f"{int(datetime.now().timestamp())}_{filename}"
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                attachment_filename = filename
        
        announcement = Announcement(
            title=title,
            content=content,
            category=category,
            is_published=is_published,
            is_pinned=is_pinned,
            scheduled_date=scheduled_date,
            attachment_filename=attachment_filename
        )
        db.session.add(announcement)
        db.session.commit()
        flash('Announcement created successfully.', 'success')
        return redirect(url_for('admin.announcements'))
    return render_template('admin/add_announcement.html')

@admin_bp.route('/announcements/edit/<int:id>', methods=['GET', 'POST'])
def edit_announcement(id):
    announcement = db.session.get(Announcement, id)
    if not announcement:
        flash('Announcement not found.', 'danger')
        return redirect(url_for('admin.announcements'))
        
    if request.method == 'POST':
        announcement.title = request.form.get('title')
        announcement.content = request.form.get('content')
        announcement.category = request.form.get('category') or 'General'
        announcement.is_published = True if request.form.get('is_published') else False
        announcement.is_pinned = True if request.form.get('is_pinned') else False
        
        sched_str = request.form.get('scheduled_date')
        if sched_str:
            try:
                if 'T' in sched_str:
                    announcement.scheduled_date = datetime.strptime(sched_str, '%Y-%m-%dT%H:%M')
                else:
                    announcement.scheduled_date = datetime.strptime(sched_str, '%Y-%m-%d')
            except ValueError:
                pass
        else:
            announcement.scheduled_date = None
            
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                filename = f"{int(datetime.now().timestamp())}_{filename}"
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                announcement.attachment_filename = filename
                
        db.session.commit()
        flash('Announcement updated successfully.', 'success')
        return redirect(url_for('admin.announcements'))
    return render_template('admin/edit_announcement.html', announcement=announcement)

@admin_bp.route('/announcements/delete/<int:id>', methods=['POST'])
def delete_announcement(id):
    announcement = db.session.get(Announcement, id)
    if announcement:
        db.session.delete(announcement)
        db.session.commit()
        flash('Announcement deleted successfully.', 'success')
    return redirect(url_for('admin.announcements'))

@admin_bp.route('/announcements/toggle/<int:id>', methods=['POST'])
def toggle_announcement(id):
    announcement = db.session.get(Announcement, id)
    if announcement:
        announcement.is_published = not announcement.is_published
        db.session.commit()
        status_text = 'published' if announcement.is_published else 'unpublished'
        flash(f'Announcement {status_text} successfully.', 'info')
    return redirect(url_for('admin.announcements'))

@admin_bp.route('/announcements/pin/<int:id>', methods=['POST'])
def pin_announcement(id):
    announcement = db.session.get(Announcement, id)
    if announcement:
        announcement.is_pinned = not announcement.is_pinned
        db.session.commit()
        status_text = 'pinned' if announcement.is_pinned else 'unpinned'
        flash(f'Announcement {status_text} successfully.', 'success')
    return redirect(url_for('admin.announcements'))

@admin_bp.route('/reports')
def reports():
    period = request.args.get('period', 'all')
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    
    # Filter builder helper for date ranges
    def get_date_filter(model_attr):
        now = datetime.now()
        if period == '7d':
            return model_attr >= (now - timedelta(days=7))
        elif period == '30d':
            return model_attr >= (now - timedelta(days=30))
        elif period == 'this_month':
            return db.and_(db.extract('year', model_attr) == now.year, db.extract('month', model_attr) == now.month)
        elif period == 'this_year':
            return db.extract('year', model_attr) == now.year
        elif period == 'custom' and start_date_str and end_date_str:
            try:
                s = datetime.strptime(start_date_str, '%Y-%m-%d')
                e = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1, microseconds=-1)
                return db.and_(model_attr >= s, model_attr <= e)
            except ValueError:
                pass
        return db.text("1=1")

    # Filtered queries
    v_query = Villager.query.join(User).filter(get_date_filter(User.created_at))
    c_query = Certificate.query.filter(get_date_filter(Certificate.submission_date))
    comp_query = Complaint.query.filter(get_date_filter(Complaint.date))
    t_query = Tax.query.filter(get_date_filter(Tax.created_at))
    a_query = Announcement.query.filter(get_date_filter(Announcement.created_at))
    s_query = Scheme.query.filter(get_date_filter(Scheme.created_at))
    
    # KPI Metrics
    villager_count = v_query.count()
    cert_count = c_query.count()
    comp_count = comp_query.count()
    scheme_count = s_query.count()
    active_schemes = s_query.filter_by(is_active=True).count()
    ann_count = a_query.count()
    pinned_ann = a_query.filter_by(is_pinned=True).count()
    
    # Certificate status & type breakdown
    cert_pending = c_query.filter_by(status='Pending').count()
    cert_approved = c_query.filter_by(status='Approved').count()
    cert_rejected = c_query.filter_by(status='Rejected').count()
    
    cert_types = ['Income Certificate', 'Residence Certificate', 'Community Certificate', 'Birth Certificate', 'Death Certificate']
    cert_type_counts = [c_query.filter_by(type=ct).count() for ct in cert_types]
    
    # Complaint status & category breakdown
    comp_pending = comp_query.filter_by(status='Pending').count()
    comp_in_progress = comp_query.filter_by(status='In Progress').count()
    comp_resolved = comp_query.filter_by(status='Resolved').count()
    
    comp_categories = ['Water Supply', 'Street Light', 'Road Damage', 'Drainage', 'Electricity', 'Sanitation']
    comp_cat_counts = [comp_query.filter_by(category=cat).count() for cat in comp_categories]
    
    # Tax metrics & type breakdown
    tax_count = t_query.count()
    tax_paid = t_query.filter_by(payment_status='Paid').count()
    tax_pending = t_query.filter(Tax.payment_status.in_(['Unpaid', 'Overdue'])).count()
    tax_revenue = db.session.query(db.func.sum(Tax.amount)).filter(get_date_filter(Tax.created_at), Tax.payment_status == 'Paid').scalar() or 0.0
    tax_due_amount = db.session.query(db.func.sum(Tax.amount)).filter(get_date_filter(Tax.created_at), Tax.payment_status.in_(['Unpaid', 'Overdue'])).scalar() or 0.0
    
    tax_types = ['Property Tax', 'House Tax', 'Water Tax']
    tax_type_paid = [db.session.query(db.func.sum(Tax.amount)).filter(get_date_filter(Tax.created_at), Tax.tax_type == tt, Tax.payment_status == 'Paid').scalar() or 0.0 for tt in tax_types]
    tax_type_unpaid = [db.session.query(db.func.sum(Tax.amount)).filter(get_date_filter(Tax.created_at), Tax.tax_type == tt, Tax.payment_status.in_(['Unpaid', 'Overdue'])).scalar() or 0.0 for tt in tax_types]
    
    # Total saved favourite schemes
    fav_count = db.session.query(favourite_schemes).count()
    
    stats = {
        'period': period,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'villagers': villager_count,
        'certificates': cert_count,
        'complaints': comp_count,
        'schemes': scheme_count,
        'active_schemes': active_schemes,
        'announcements': ann_count,
        'pinned_announcements': pinned_ann,
        'fav_count': fav_count,
        'cert_pending': cert_pending,
        'cert_approved': cert_approved,
        'cert_rejected': cert_rejected,
        'cert_types': cert_types,
        'cert_type_counts': cert_type_counts,
        'comp_pending': comp_pending,
        'comp_in_progress': comp_in_progress,
        'comp_resolved': comp_resolved,
        'comp_categories': comp_categories,
        'comp_cat_counts': comp_cat_counts,
        'tax_count': tax_count,
        'tax_paid': tax_paid,
        'tax_pending': tax_pending,
        'tax_revenue': tax_revenue,
        'tax_due_amount': tax_due_amount,
        'tax_types': tax_types,
        'tax_type_paid': tax_type_paid,
        'tax_type_unpaid': tax_type_unpaid
    }
    return render_template('admin/reports.html', stats=stats)

@admin_bp.route('/reports/export/csv')
@admin_bp.route('/reports/export/<module>/csv')
def export_csv(module='summary'):
    output = io.StringIO()
    writer = csv.writer(output)
    filename = f"digital_village_{module}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    if module == 'villagers':
        writer.writerow(['ID', 'Full Name', 'Mobile Number', 'Address', 'Aadhaar Number', 'Registered Date'])
        for v in Villager.query.join(User).order_by(User.created_at.desc()).all():
            writer.writerow([v.id, v.full_name, v.mobile, v.address, v.aadhaar, v.user.created_at.strftime('%Y-%m-%d %H:%M') if v.user and v.user.created_at else ''])
            
    elif module == 'certificates':
        writer.writerow(['ID', 'Applicant Name', 'Certificate Type', 'Mobile Number', 'Status', 'Applied Date', 'Admin Remarks'])
        for c in Certificate.query.order_by(Certificate.submission_date.desc()).all():
            writer.writerow([c.id, c.villager.full_name if c.villager else '', c.type, c.mobile, c.status, c.submission_date.strftime('%Y-%m-%d %H:%M') if c.submission_date else '', c.remarks or ''])
            
    elif module == 'complaints':
        writer.writerow(['ID', 'Complainant Name', 'Category', 'Description', 'Status', 'Registered Date', 'Admin Remarks'])
        for comp in Complaint.query.order_by(Complaint.date.desc()).all():
            writer.writerow([comp.id, comp.villager.full_name if comp.villager else '', comp.category, comp.description, comp.status, comp.date.strftime('%Y-%m-%d %H:%M') if comp.date else '', comp.remarks or ''])
            
    elif module == 'taxes':
        writer.writerow(['Bill ID', 'Villager Name', 'Tax Type', 'Assessment Amount (Rs)', 'Due Date', 'Payment Status', 'Receipt Number', 'Payment Date'])
        for t in Tax.query.order_by(Tax.due_date.desc()).all():
            writer.writerow([t.id, t.villager.full_name if t.villager else '', t.tax_type, t.amount, t.due_date.strftime('%Y-%m-%d') if t.due_date else '', t.payment_status, t.receipt_number or '', t.payment_date.strftime('%Y-%m-%d') if t.payment_date else ''])
            
    elif module == 'schemes':
        writer.writerow(['ID', 'Scheme Title', 'Eligibility Criteria', 'Benefits Description', 'Active Status', 'Saved by Residents Count', 'Created Date'])
        for s in Scheme.query.order_by(Scheme.created_at.desc()).all():
            writer.writerow([s.id, s.title, s.eligibility, s.benefits, 'Active' if s.is_active else 'Inactive', len(s.saved_by), s.created_at.strftime('%Y-%m-%d') if s.created_at else ''])
            
    else: # summary
        writer.writerow(['DIGITAL VILLAGE MANAGEMENT SYSTEM - EXECUTIVE AUDIT & ANALYTICS SUMMARY'])
        writer.writerow(['Generated On', datetime.now().strftime('%B %d, %Y - %I:%M %p')])
        writer.writerow([])
        writer.writerow(['1. DEMOGRAPHICS & WELFARE'])
        writer.writerow(['Total Registered Residents / Villagers', Villager.query.count()])
        writer.writerow(['Total Welfare Schemes Published', Scheme.query.count()])
        writer.writerow(['Active Welfare Schemes', Scheme.query.filter_by(is_active=True).count()])
        writer.writerow(['Total Favourited Schemes by Residents', db.session.query(favourite_schemes).count()])
        writer.writerow(['Total Official Announcements Broadcasted', Announcement.query.count()])
        writer.writerow([])
        writer.writerow(['2. CERTIFICATE SERVICES AUDIT'])
        writer.writerow(['Total Applications Received', Certificate.query.count()])
        writer.writerow(['Approved Certificates', Certificate.query.filter_by(status='Approved').count()])
        writer.writerow(['Pending Verification', Certificate.query.filter_by(status='Pending').count()])
        writer.writerow(['Rejected Applications', Certificate.query.filter_by(status='Rejected').count()])
        writer.writerow([])
        writer.writerow(['3. GRIEVANCE REDRESSAL AUDIT'])
        writer.writerow(['Total Complaints Registered', Complaint.query.count()])
        writer.writerow(['Resolved Complaints', Complaint.query.filter_by(status='Resolved').count()])
        writer.writerow(['In Progress Complaints', Complaint.query.filter_by(status='In Progress').count()])
        writer.writerow(['Pending Complaints', Complaint.query.filter_by(status='Pending').count()])
        writer.writerow([])
        writer.writerow(['4. MUNICIPAL & TAX FINANCIAL AUDIT'])
        writer.writerow(['Total Tax Assessments Issued', Tax.query.count()])
        writer.writerow(['Paid Assessments Count', Tax.query.filter_by(payment_status='Paid').count()])
        writer.writerow(['Unpaid / Overdue Assessments Count', Tax.query.filter(Tax.payment_status.in_(['Unpaid', 'Overdue'])).count()])
        writer.writerow(['Total Tax Revenue Collected (Rs)', db.session.query(db.func.sum(Tax.amount)).filter_by(payment_status='Paid').scalar() or 0.0])
        writer.writerow(['Total Pending Tax Dues (Rs)', db.session.query(db.func.sum(Tax.amount)).filter(Tax.payment_status.in_(['Unpaid', 'Overdue'])).scalar() or 0.0])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@admin_bp.route('/reports/export/pdf')
@admin_bp.route('/reports/executive_summary')
def export_pdf():
    stats = {
        'villagers': Villager.query.count(),
        'certificates': Certificate.query.count(),
        'complaints': Complaint.query.count(),
        'schemes': Scheme.query.count(),
        'active_schemes': Scheme.query.filter_by(is_active=True).count(),
        'announcements': Announcement.query.count(),
        'cert_pending': Certificate.query.filter_by(status='Pending').count(),
        'cert_approved': Certificate.query.filter_by(status='Approved').count(),
        'cert_rejected': Certificate.query.filter_by(status='Rejected').count(),
        'comp_pending': Complaint.query.filter_by(status='Pending').count(),
        'comp_in_progress': Complaint.query.filter_by(status='In Progress').count(),
        'comp_resolved': Complaint.query.filter_by(status='Resolved').count(),
        'tax_count': Tax.query.count(),
        'tax_paid': Tax.query.filter_by(payment_status='Paid').count(),
        'tax_pending': Tax.query.filter(Tax.payment_status.in_(['Unpaid', 'Overdue'])).count(),
        'tax_revenue': db.session.query(db.func.sum(Tax.amount)).filter_by(payment_status='Paid').scalar() or 0.0,
        'tax_due': db.session.query(db.func.sum(Tax.amount)).filter(Tax.payment_status.in_(['Unpaid', 'Overdue'])).scalar() or 0.0,
        'generated_on': datetime.now().strftime('%B %d, %Y - %I:%M %p')
    }
    return render_template('admin/report_print.html', stats=stats)

@admin_bp.route('/search')
def search():
    q = request.args.get('q', '').strip()
    results = {
        'villagers': [],
        'certificates': [],
        'complaints': [],
        'schemes': []
    }
    if q:
        results['villagers'] = Villager.query.filter(
            Villager.full_name.ilike(f'%{q}%') | 
            Villager.mobile.ilike(f'%{q}%') | 
            Villager.aadhaar.ilike(f'%{q}%')
        ).all()
        
        results['certificates'] = Certificate.query.filter(
            Certificate.applicant_name.ilike(f'%{q}%') | 
            Certificate.type.ilike(f'%{q}%') | 
            Certificate.aadhaar.ilike(f'%{q}%')
        ).all()
        
        results['complaints'] = Complaint.query.filter(
            Complaint.category.ilike(f'%{q}%') | 
            Complaint.description.ilike(f'%{q}%')
        ).all()
        
        results['schemes'] = Scheme.query.filter(
            Scheme.title.ilike(f'%{q}%') | 
            Scheme.description.ilike(f'%{q}%')
        ).all()
        
        results['taxes'] = Tax.query.join(Villager).filter(
            Tax.tax_type.ilike(f'%{q}%') | 
            Tax.receipt_number.ilike(f'%{q}%') | 
            Villager.full_name.ilike(f'%{q}%') | 
            Villager.mobile.ilike(f'%{q}%')
        ).all()
        
    return render_template('admin/search.html', q=q, results=results)

@admin_bp.route('/taxes')
def taxes():
    tax_type = request.args.get('tax_type')
    status = request.args.get('status')
    query = Tax.query
    if tax_type:
        query = query.filter_by(tax_type=tax_type)
    if status:
        query = query.filter_by(payment_status=status)
    all_taxes = query.order_by(Tax.created_at.desc()).all()
    villagers = Villager.query.order_by(Villager.full_name).all()
    return render_template('admin/taxes.html', taxes=all_taxes, villagers=villagers, tax_type=tax_type, status=status)

@admin_bp.route('/taxes/add', methods=['GET', 'POST'])
def add_tax():
    if request.method == 'POST':
        villager_id = request.form.get('villager_id')
        tax_type = request.form.get('tax_type')
        amount = request.form.get('amount')
        due_date_str = request.form.get('due_date')
        remarks = request.form.get('remarks')
        
        # Server-side validation
        if not (villager_id and tax_type and amount and due_date_str):
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('admin.add_tax'))
            
        # Check for duplicate unpaid tax record
        existing = Tax.query.filter_by(villager_id=villager_id, tax_type=tax_type, payment_status='Unpaid').first()
        if existing:
            flash(f'An unpaid {tax_type} already exists for this villager.', 'warning')
            return redirect(url_for('admin.taxes'))
            
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        tax = Tax(
            villager_id=int(villager_id),
            tax_type=tax_type,
            amount=float(amount),
            due_date=due_date,
            remarks=remarks,
            payment_status='Unpaid'
        )
        db.session.add(tax)
        db.session.commit()
        flash('Tax record created successfully.', 'success')
        return redirect(url_for('admin.taxes'))
        
    villagers = Villager.query.order_by(Villager.full_name).all()
    return render_template('admin/add_tax.html', villagers=villagers)

@admin_bp.route('/taxes/edit/<int:id>', methods=['GET', 'POST'])
def edit_tax(id):
    tax = db.session.get(Tax, id)
    if not tax:
        flash('Tax record not found.', 'danger')
        return redirect(url_for('admin.taxes'))
        
    if request.method == 'POST':
        tax.tax_type = request.form.get('tax_type')
        tax.amount = float(request.form.get('amount'))
        due_date_str = request.form.get('due_date')
        if due_date_str:
            tax.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        tax.remarks = request.form.get('remarks')
        status = request.form.get('payment_status')
        if status:
            tax.payment_status = status
            if status == 'Paid' and not tax.payment_date:
                tax.payment_date = datetime.utcnow()
                if not tax.receipt_number:
                    tax.receipt_number = f"RCP-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        db.session.commit()
        flash('Tax record updated successfully.', 'success')
        return redirect(url_for('admin.taxes'))
        
    villagers = Villager.query.order_by(Villager.full_name).all()
    return render_template('admin/edit_tax.html', tax=tax, villagers=villagers)

@admin_bp.route('/taxes/delete/<int:id>', methods=['POST'])
def delete_tax(id):
    tax = db.session.get(Tax, id)
    if tax:
        db.session.delete(tax)
        db.session.commit()
        flash('Tax record deleted successfully.', 'success')
    return redirect(url_for('admin.taxes'))

@admin_bp.route('/taxes/mark_paid/<int:id>', methods=['POST'])
def mark_tax_paid(id):
    tax = db.session.get(Tax, id)
    if tax:
        if tax.payment_status != 'Paid':
            tax.payment_status = 'Paid'
            tax.payment_date = datetime.utcnow()
            if not tax.receipt_number:
                tax.receipt_number = f"RCP-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            db.session.commit()
            flash(f'Tax record marked as Paid. Receipt: {tax.receipt_number}', 'success')
        else:
            flash('Tax record is already marked as Paid.', 'info')
    return redirect(url_for('admin.taxes'))

@admin_bp.route('/taxes/report')
def tax_report():
    total_records = Tax.query.count()
    paid_count = Tax.query.filter_by(payment_status='Paid').count()
    unpaid_count = Tax.query.filter_by(payment_status='Unpaid').count()
    overdue_count = Tax.query.filter_by(payment_status='Overdue').count()
    
    total_revenue = db.session.query(db.func.sum(Tax.amount)).filter_by(payment_status='Paid').scalar() or 0.0
    pending_revenue = db.session.query(db.func.sum(Tax.amount)).filter(Tax.payment_status.in_(['Unpaid', 'Overdue'])).scalar() or 0.0
    
    # Breakdown by tax type
    prop_revenue = db.session.query(db.func.sum(Tax.amount)).filter_by(tax_type='Property Tax', payment_status='Paid').scalar() or 0.0
    house_revenue = db.session.query(db.func.sum(Tax.amount)).filter_by(tax_type='House Tax', payment_status='Paid').scalar() or 0.0
    water_revenue = db.session.query(db.func.sum(Tax.amount)).filter_by(tax_type='Water Tax', payment_status='Paid').scalar() or 0.0
    
    stats = {
        'total_records': total_records,
        'paid_count': paid_count,
        'unpaid_count': unpaid_count,
        'overdue_count': overdue_count,
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue,
        'prop_revenue': prop_revenue,
        'house_revenue': house_revenue,
        'water_revenue': water_revenue
    }
    
    recent_paid = Tax.query.filter_by(payment_status='Paid').order_by(Tax.payment_date.desc()).limit(10).all()
    return render_template('admin/tax_report.html', stats=stats, recent_paid=recent_paid)



