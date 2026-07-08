from database import db
from datetime import datetime

class Tax(db.Model):
    __tablename__ = 'taxes'
    id = db.Column(db.Integer, primary_key=True)
    villager_id = db.Column(db.Integer, db.ForeignKey('villagers.id'), nullable=False)
    tax_type = db.Column(db.String(50), nullable=False) # e.g. Property Tax, House Tax, Water Tax
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    payment_date = db.Column(db.DateTime, nullable=True)
    payment_status = db.Column(db.String(20), nullable=False, default='Unpaid') # Paid, Unpaid, Overdue
    receipt_number = db.Column(db.String(50), nullable=True, unique=True)
    remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    villager = db.relationship('Villager', backref=db.backref('taxes', lazy=True))
