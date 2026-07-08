import unittest
from app import create_app
from database import db
from models.user import User, Villager
from models.certificate import Certificate
from models.complaint import Complaint
from models.scheme import Scheme
from models.announcement import Announcement
from models.tax import Tax
from datetime import datetime, timedelta
import io
import csv

class Phase9AnalyticsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.create_test_data()

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()

    def create_test_data(self):
        # Admin
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
        
        # Villager
        user = User.query.filter_by(username='testuser').first()
        if not user:
            user = User(username='testuser', role='villager')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
        
        villager = Villager.query.filter_by(user_id=user.id).first()
        if not villager:
            villager = Villager(
                user_id=user.id,
                full_name='Ramesh Kumar',
                mobile='9876543210',
                address='Ward No 4, Digital Village',
                aadhaar='123456789012'
            )
            db.session.add(villager)
            db.session.commit()
        
        # Certificate
        cert = Certificate.query.filter_by(villager_id=villager.id, type='Income Certificate').first()
        if not cert:
            cert = Certificate(
                villager_id=villager.id,
                type='Income Certificate',
                applicant_name=villager.full_name,
                address=villager.address,
                mobile=villager.mobile,
                aadhaar=villager.aadhaar,
                status='Approved'
            )
            db.session.add(cert)
        
        # Complaint
        comp = Complaint.query.filter_by(villager_id=villager.id, category='Water Supply').first()
        if not comp:
            comp = Complaint(villager_id=villager.id, category='Water Supply', description='No water for 2 days', status='Resolved')
            db.session.add(comp)
        
        # Scheme
        scheme = Scheme.query.filter_by(title='Kisan Samman Nidhi').first()
        if not scheme:
            scheme = Scheme(title='Kisan Samman Nidhi', description='Farmer support', eligibility='Small farmers', benefits='Rs 6000', is_active=True)
            db.session.add(scheme)
            db.session.flush()
            if villager not in scheme.saved_by:
                scheme.saved_by.append(villager)
        
        # Tax
        tax = Tax.query.filter_by(villager_id=villager.id, tax_type='Property Tax').first()
        if not tax:
            tax = Tax(villager_id=villager.id, tax_type='Property Tax', amount=1200.0, due_date=datetime.now().date(), payment_status='Paid')
            db.session.add(tax)
        
        # Announcement
        ann = Announcement.query.filter_by(title='Gram Sabha Meeting').first()
        if not ann:
            ann = Announcement(title='Gram Sabha Meeting', content='Attend meeting on Friday.', category='General', is_pinned=True, is_published=True)
            db.session.add(ann)
        
        db.session.commit()

    def login_admin(self):
        return self.client.post('/auth/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)

    def test_01_analytics_dashboard_and_filtering(self):
        """Test accessing Analytics dashboard with various time periods and date ranges"""
        self.login_admin()
        
        # All time
        res = self.client.get('/admin/reports?period=all')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Executive Analytics & Village Reports', res.data)
        self.assertIn(b'Certificate Verification SLA', res.data)
        self.assertIn(b'Grievances Registered by Category', res.data)
        
        # 7 days
        res_7d = self.client.get('/admin/reports?period=7d')
        self.assertEqual(res_7d.status_code, 200)
        
        # 30 days
        res_30d = self.client.get('/admin/reports?period=30d')
        self.assertEqual(res_30d.status_code, 200)
        
        # Custom range
        res_custom = self.client.get('/admin/reports?period=custom&start_date=2025-01-01&end_date=2026-12-31')
        self.assertEqual(res_custom.status_code, 200)

    def test_02_modular_data_exports_csv(self):
        """Test downloading CSV reports for all granular modules"""
        self.login_admin()
        
        modules = ['villagers', 'certificates', 'complaints', 'taxes', 'schemes', 'summary']
        for mod in modules:
            res = self.client.get(f'/admin/reports/export/{mod}/csv')
            self.assertEqual(res.status_code, 200, f"Failed CSV export for module: {mod}")
            self.assertEqual(res.mimetype, 'text/csv')
            self.assertIn('attachment;filename=', res.headers['Content-Disposition'])
            
            # Verify CSV content structure
            content = res.data.decode('utf-8')
            reader = csv.reader(io.StringIO(content))
            rows = list(reader)
            self.assertGreaterEqual(len(rows), 2, f"CSV for {mod} has fewer than 2 rows")

    def test_03_printable_executive_summary_pdf(self):
        """Test viewing/exporting the official Gram Panchayat Executive Audit PDF view"""
        self.login_admin()
        
        res = self.client.get('/admin/reports/executive_summary')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'GRAM PANCHAYAT EXECUTIVE AUDIT SUMMARY', res.data)
        self.assertIn(b'Demographics & Citizen Engagement Audit', res.data)
        self.assertIn(b'Municipal Tax Financial Revenue Audit', res.data)
        self.assertIn(b'Certificate Verification & Issuance SLA Audit', res.data)
        self.assertIn(b'Grievance Redressal & Resolution SLA Audit', res.data)
        self.assertIn(b'Sarpanch (Panchayat Head)', res.data)
        
        # Also test alias route
        res_alias = self.client.get('/admin/reports/export/pdf')
        self.assertEqual(res_alias.status_code, 200)
        self.assertIn(b'GRAM PANCHAYAT EXECUTIVE AUDIT SUMMARY', res_alias.data)

if __name__ == '__main__':
    unittest.main()
