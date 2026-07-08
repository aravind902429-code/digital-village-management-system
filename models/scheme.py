from database import db
from datetime import datetime

favourite_schemes = db.Table('favourite_schemes',
    db.Column('villager_id', db.Integer, db.ForeignKey('villagers.id'), primary_key=True),
    db.Column('scheme_id', db.Integer, db.ForeignKey('schemes.id'), primary_key=True)
)

class Scheme(db.Model):
    __tablename__ = 'schemes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    eligibility = db.Column(db.Text, nullable=False)
    benefits = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    saved_by = db.relationship('Villager', secondary=favourite_schemes, backref=db.backref('favourite_schemes', lazy='dynamic'))
