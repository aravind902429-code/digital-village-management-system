from database import db
from datetime import datetime

class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='General')  # e.g. General, Health, Education, Agriculture, Scheme, Urgent
    is_pinned = db.Column(db.Boolean, default=False)
    scheduled_date = db.Column(db.DateTime, nullable=True)  # Optional future publication date
    attachment_filename = db.Column(db.String(255), nullable=True)  # PDF or image attachment
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    reads = db.relationship('AnnouncementRead', backref='announcement', lazy=True, cascade='all, delete-orphan')

class AnnouncementRead(db.Model):
    __tablename__ = 'announcement_reads'
    id = db.Column(db.Integer, primary_key=True)
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcements.id'), nullable=False)
    villager_id = db.Column(db.Integer, db.ForeignKey('villagers.id'), nullable=False)
    read_at = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (db.UniqueConstraint('announcement_id', 'villager_id', name='_announcement_villager_uc'),)
