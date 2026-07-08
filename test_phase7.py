import unittest
from app import create_app
from database import db
from models.user import User, Villager
from models.tax import Tax
from datetime import datetime, date, timedelta

class Phase7TaxManagementTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Ensure test admin and villager exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            
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
                full_name="Test User",
                mobile="9876543210",
                address="House No 12, MG Road, Rampur Village",
                aadhaar="123456789012"
            )
            db.session.add(villager)
            
        db.session.commit()
        
        # Clean up existing taxes for this villager to ensure clean test state
        if villager:
            Tax.query.filter_by(villager_id=villager.id).delete()
            db.session.commit()
            self.test_villager_id = villager.id
        else:
            self.test_villager_id = None

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()

    def login(self, username, password):
        return self.client.post('/auth/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/auth/logout', follow_redirects=True)

    def test_01_admin_issue_and_manage_taxes(self):
        print("\n--- Testing Step 1: Admin Issue & Manage Taxes ---")
        self.login('admin', 'admin123')
        
        self.assertIsNotNone(self.test_villager_id, "Test villager must exist.")
        
        # Issue Property Tax
        due_date_str = (date.today() + timedelta(days=30)).strftime('%Y-%m-%d')
        res = self.client.post('/admin/taxes/add', data=dict(
            villager_id=self.test_villager_id,
            tax_type='Property Tax',
            amount='1500.00',
            due_date=due_date_str,
            remarks='Annual Property Tax Assessment 2026'
        ), follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Tax record created successfully', res.data)
        
        # Issue House Tax
        res = self.client.post('/admin/taxes/add', data=dict(
            villager_id=self.test_villager_id,
            tax_type='House Tax',
            amount='800.00',
            due_date=due_date_str,
            remarks='Annual House Tax 2026'
        ), follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        
        # Issue Water Tax
        res = self.client.post('/admin/taxes/add', data=dict(
            villager_id=self.test_villager_id,
            tax_type='Water Tax',
            amount='300.00',
            due_date=due_date_str,
            remarks='Water Supply Tax Q2'
        ), follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        
        # Test Duplicate Unpaid Prevention
        res = self.client.post('/admin/taxes/add', data=dict(
            villager_id=self.test_villager_id,
            tax_type='Property Tax',
            amount='1500.00',
            due_date=due_date_str,
            remarks='Duplicate attempt'
        ), follow_redirects=True)
        self.assertIn(b'already exists for this villager', res.data)
        print("[OK] Admin successfully issued Property, House, and Water tax records, and duplicate check worked!")

    def test_02_admin_tax_list_filter_and_edit(self):
        print("\n--- Testing Step 2: Admin Tax List, Filter, & Edit ---")
        self.login('admin', 'admin123')
        
        # Create a tax record to edit
        tax = Tax(villager_id=self.test_villager_id, tax_type='House Tax', amount=800.0, due_date=date.today(), payment_status='Unpaid')
        db.session.add(tax)
        db.session.commit()
        
        res = self.client.get('/admin/taxes')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Tax Management Portal', res.data)
        
        # Filter by House Tax
        res = self.client.get('/admin/taxes?tax_type=House+Tax')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'House Tax', res.data)
        
        # Edit tax record
        res = self.client.post(f'/admin/taxes/edit/{tax.id}', data=dict(
            tax_type='House Tax',
            amount='850.00',
            due_date=tax.due_date.strftime('%Y-%m-%d'),
            remarks='Updated assessment amount',
            payment_status='Unpaid'
        ), follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Tax record updated successfully', res.data)
        updated_tax = db.session.get(Tax, tax.id)
        self.assertEqual(updated_tax.amount, 850.0)
        print("[OK] Admin tax list, filters, and record editing verified!")

    def test_03_admin_mark_paid_and_reports(self):
        print("\n--- Testing Step 3: Admin Mark Paid & Collection Report ---")
        self.login('admin', 'admin123')
        
        tax = Tax(villager_id=self.test_villager_id, tax_type='Water Tax', amount=300.0, due_date=date.today(), payment_status='Unpaid')
        db.session.add(tax)
        db.session.commit()
        
        res = self.client.post(f'/admin/taxes/mark_paid/{tax.id}', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'marked as Paid', res.data)
        paid_tax = db.session.get(Tax, tax.id)
        self.assertEqual(paid_tax.payment_status, 'Paid')
        self.assertIsNotNone(paid_tax.receipt_number)
            
        # Test Tax Collection Report
        res = self.client.get('/admin/taxes/report')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Tax Collection & Revenue Report', res.data)
        self.assertIn(b'Total Revenue Collected', res.data)
        print("[OK] Admin Mark Paid workflow and Tax Collection Report verified!")

    def test_04_villager_my_taxes_and_online_payment(self):
        print("\n--- Testing Step 4: Villager My Taxes & Demo Online Payment ---")
        self.logout()
        self.login('testuser', 'password123')
        
        # Create an unpaid tax for testuser
        unpaid_tax = Tax(villager_id=self.test_villager_id, tax_type='Property Tax', amount=1500.0, due_date=date.today(), payment_status='Unpaid')
        db.session.add(unpaid_tax)
        db.session.commit()
        
        res = self.client.get('/villager/taxes')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'My Village Taxes & Bills', res.data)
        self.assertIn(b'Property Tax Due', res.data)
        
        res = self.client.post(f'/villager/taxes/pay/{unpaid_tax.id}', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Online Payment successful', res.data)
        self.assertIn(b'Receipt generated', res.data)
        
        paid_tax = db.session.get(Tax, unpaid_tax.id)
        self.assertEqual(paid_tax.payment_status, 'Paid')
        self.assertIsNotNone(paid_tax.receipt_number)
        
        # Test Receipt View
        res_receipt = self.client.get(f'/villager/taxes/receipt/{paid_tax.id}')
        self.assertEqual(res_receipt.status_code, 200)
        self.assertIn(b'OFFICIAL TAX PAYMENT RECEIPT', res_receipt.data)
        self.assertIn(paid_tax.receipt_number.encode(), res_receipt.data)
        print("[OK] Villager My Taxes, Demo Online Payment, and official PDF receipt verified!")

    def test_05_dashboard_and_global_search_integration(self):
        print("\n--- Testing Step 5: Dashboard & Global Search Integration ---")
        self.login('testuser', 'password123')
        
        # Create a tax record to verify stats and search
        tax = Tax(villager_id=self.test_villager_id, tax_type='Property Tax', amount=1500.0, due_date=date.today(), payment_status='Unpaid')
        db.session.add(tax)
        db.session.commit()
        
        res_v_dash = self.client.get('/villager/dashboard')
        self.assertEqual(res_v_dash.status_code, 200)
        self.assertIn(b'Pending / Unpaid Taxes', res_v_dash.data)
        
        self.logout()
        self.login('admin', 'admin123')
        res_a_dash = self.client.get('/admin/dashboard')
        self.assertEqual(res_a_dash.status_code, 200)
        self.assertIn(b'Total Tax Bills Issued', res_a_dash.data)
        
        # Test Global Search for tax keywords
        res_search = self.client.get('/admin/search?q=Property')
        self.assertEqual(res_search.status_code, 200)
        self.assertIn(b'Property Tax', res_search.data)
        print("[OK] Dashboard statistics cards and Global Portal Search integration verified!")

if __name__ == '__main__':
    unittest.main()
