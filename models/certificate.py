from database import db
from datetime import datetime

class Certificate(db.Model):
    __tablename__ = 'certificates'
    id = db.Column(db.Integer, primary_key=True)
    villager_id = db.Column(db.Integer, db.ForeignKey('villagers.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    applicant_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    aadhaar = db.Column(db.String(12), nullable=False)
    document_filename = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='Pending') # Pending, Approved, Rejected
    remarks = db.Column(db.Text, nullable=True)
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    villager = db.relationship('Villager', backref=db.backref('certificates', lazy=True))
