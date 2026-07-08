from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from database import db
from models.user import User, Villager

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
            
        login_user(user)
        if user.role == 'villager' and hasattr(user, 'villager_profile') and user.villager_profile:
            from models.announcement import Announcement, AnnouncementRead
            from datetime import datetime
            active_announcements = Announcement.query.filter(
                Announcement.is_published == True,
                db.or_(Announcement.scheduled_date == None, Announcement.scheduled_date <= datetime.now())
            ).all()
            read_ids = [r.announcement_id for r in AnnouncementRead.query.filter_by(villager_id=user.villager_profile.id).all()]
            unread_count = len([a for a in active_announcements if a.id not in read_ids])
            if unread_count > 0:
                flash(f'Welcome back! You have {unread_count} new unread announcement(s)/notification(s). Check the notification bell!', 'info')
        return redirect(url_for('main.index'))
        
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        mobile = request.form.get('mobile')
        address = request.form.get('address')
        aadhaar = request.form.get('aadhaar')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('auth.register'))
            
        user = User(username=username, role='villager')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        villager = Villager(user_id=user.id, full_name=full_name, mobile=mobile, address=address, aadhaar=aadhaar)
        db.session.add(villager)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
