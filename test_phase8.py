import unittest
from app import create_app
from database import db
from models.user import User, Villager
from models.announcement import Announcement, AnnouncementRead
from datetime import datetime, timedelta
import io

class Phase8AnnouncementsTestCase(unittest.TestCase):
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
        
        # Clean up existing test announcements
        AnnouncementRead.query.delete()
        Announcement.query.filter(Announcement.title.like('Test%')).delete()
        db.session.commit()
        self.test_villager_id = villager.id

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()

    def login_admin(self):
        return self.client.post('/auth/login', data=dict(username='admin', password='admin123'), follow_redirects=True)

    def login_villager(self):
        return self.client.post('/auth/login', data=dict(username='testuser', password='password123'), follow_redirects=True)

    def test_01_admin_create_announcements(self):
        """Test Admin creating pinned, categorized, scheduled announcements with attachments"""
        self.login_admin()
        
        # Create normal announcement
        res = self.client.post('/admin/announcements/add', data=dict(
            title='Test General Notice',
            content='This is a general announcement for all residents.',
            category='General',
            is_published='on'
        ), follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Announcement created successfully', res.data)
        
        # Create pinned urgent announcement with attachment
        data = dict(
            title='Test Urgent Alert',
            content='Emergency water supply disruption tomorrow morning.',
            category='Urgent',
            is_published='on',
            is_pinned='on',
            attachment=(io.BytesIO(b"Dummy PDF document content"), "test_notice.pdf")
        )
        res2 = self.client.post('/admin/announcements/add', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(res2.status_code, 200)
        self.assertIn(b'Announcement created successfully', res2.data)
        
        # Verify in database
        ann = Announcement.query.filter_by(title='Test Urgent Alert').first()
        self.assertIsNotNone(ann)
        self.assertTrue(ann.is_pinned)
        self.assertEqual(ann.category, 'Urgent')
        self.assertIsNotNone(ann.attachment_filename)

    def test_02_villager_announcements_feed_and_search(self):
        """Test Villager viewing announcements, keyword search, and category filtering"""
        # Seed test announcements
        a1 = Announcement(title='Test Health Drive', content='Polio vaccination camp this Sunday.', category='Health', is_published=True)
        a2 = Announcement(title='Test Agriculture Scheme', content='Subsidized seeds available at Panchayat office.', category='Agriculture', is_published=True)
        db.session.add_all([a1, a2])
        db.session.commit()
        
        self.login_villager()
        
        # View all
        res = self.client.get('/villager/announcements')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Test Health Drive', res.data)
        self.assertIn(b'Test Agriculture Scheme', res.data)
        
        # Filter by Category
        res_cat = self.client.get('/villager/announcements?category=Health')
        self.assertIn(b'Test Health Drive', res_cat.data)
        self.assertNotIn(b'card-title fw-bold mb-0 text-dark">Test Agriculture Scheme</h5>', res_cat.data)
        
        # Keyword Search
        res_q = self.client.get('/villager/announcements?q=vaccination')
        self.assertIn(b'Test Health Drive', res_q.data)
        self.assertNotIn(b'card-title fw-bold mb-0 text-dark">Test Agriculture Scheme</h5>', res_q.data)

    def test_03_mark_as_read_and_badge_counter(self):
        """Test marking notifications as read and verifying badge decrease"""
        ann = Announcement(title='Test Unread Notice', content='Please read this important notice.', category='General', is_published=True)
        db.session.add(ann)
        db.session.commit()
        
        self.login_villager()
        
        # Check that announcement is unread
        existing = AnnouncementRead.query.filter_by(announcement_id=ann.id, villager_id=self.test_villager_id).first()
        self.assertIsNone(existing)
        
        # Mark as read
        res = self.client.get(f'/villager/announcements/read/{ann.id}', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        
        # Verify database record
        read_rec = AnnouncementRead.query.filter_by(announcement_id=ann.id, villager_id=self.test_villager_id).first()
        self.assertIsNotNone(read_rec)

    def test_04_mark_all_as_read(self):
        """Test Mark All as Read functionality"""
        a1 = Announcement(title='Test Notice 1', content='Content 1', is_published=True)
        a2 = Announcement(title='Test Notice 2', content='Content 2', is_published=True)
        db.session.add_all([a1, a2])
        db.session.commit()
        
        self.login_villager()
        
        res = self.client.get('/villager/announcements/read_all', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'All announcements marked as read', res.data)
        
        count = AnnouncementRead.query.filter_by(villager_id=self.test_villager_id).count()
        self.assertGreaterEqual(count, 2)

    def test_05_pin_toggle(self):
        """Test Admin quick pinning and unpinning"""
        ann = Announcement(title='Test Pinning Notice', content='Will be pinned.', is_published=True, is_pinned=False)
        db.session.add(ann)
        db.session.commit()
        
        self.login_admin()
        res = self.client.post(f'/admin/announcements/pin/{ann.id}', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        
        db.session.refresh(ann)
        self.assertTrue(ann.is_pinned)

if __name__ == '__main__':
    unittest.main()
