from flask import Flask, render_template
from config import Config
from database import db
from flask_login import LoginManager
import os

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    from models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.villager import villager_bp
    from routes.admin import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(villager_bp)
    app.register_blueprint(admin_bp)
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
    
    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        
    @app.context_processor
    def inject_notifications():
        from flask_login import current_user
        from models.announcement import Announcement, AnnouncementRead
        from datetime import datetime
        if current_user.is_authenticated and current_user.role == 'villager' and hasattr(current_user, 'villager_profile') and current_user.villager_profile:
            active_announcements = Announcement.query.filter(
                Announcement.is_published == True,
                db.or_(Announcement.scheduled_date == None, Announcement.scheduled_date <= datetime.now())
            ).all()
            read_ids = [r.announcement_id for r in AnnouncementRead.query.filter_by(villager_id=current_user.villager_profile.id).all()]
            unread_list = [a for a in active_announcements if a.id not in read_ids]
            unread_list.sort(key=lambda x: (not x.is_pinned, x.created_at), reverse=True)
            return dict(unread_announcements_count=len(unread_list), unread_notifications=unread_list[:5])
        return dict(unread_announcements_count=0, unread_notifications=[])

    # Create database tables
    with app.app_context():
        db.create_all()
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE announcements ADD COLUMN category VARCHAR(50) DEFAULT 'General'"))
                conn.commit()
        except Exception:
            pass
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE announcements ADD COLUMN is_pinned BOOLEAN DEFAULT 0"))
                conn.commit()
        except Exception:
            pass
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE announcements ADD COLUMN scheduled_date DATETIME DEFAULT NULL"))
                conn.commit()
        except Exception:
            pass
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE announcements ADD COLUMN attachment_filename VARCHAR(255) DEFAULT NULL"))
                conn.commit()
        except Exception:
            pass

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
