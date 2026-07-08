from database import db
from datetime import datetime

class Complaint(db.Model):
    __tablename__ = 'complaints'
    id = db.Column(db.Integer, primary_key=True)
    villager_id = db.Column(db.Integer, db.ForeignKey('villagers.id'), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='Pending') # Pending, In Progress, Resolved
    remarks = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    villager = db.relationship('Villager', backref=db.backref('complaints', lazy=True))
