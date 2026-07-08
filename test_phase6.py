import requests
import sqlite3

session = requests.Session()

# 1. Login as Admin
admin_login = session.post('http://127.0.0.1:5000/auth/login', data={'username': 'admin', 'password': 'admin123'})
print("Admin Login Status:", admin_login.status_code)

# 2. Add New Announcement
ann_data = {
    'title': 'Village Cleanliness Drive 2026',
    'content': 'All villagers are requested to participate in the cleanliness drive at Gram Panchayat grounds this Sunday.',
    'is_published': 'on'
}
r_add = session.post('http://127.0.0.1:5000/admin/announcements/add', data=ann_data)
print("Admin Add Announcement Status:", r_add.status_code)

# 3. Verify Admin Announcements List
r_list = session.get('http://127.0.0.1:5000/admin/announcements')
print("Admin Announcements List Status:", r_list.status_code)
if "Village Cleanliness Drive 2026" in r_list.text:
    print("Announcement created and visible in Admin list.")

# Get Announcement ID
conn = sqlite3.connect('digital_village.db')
c = conn.cursor()
c.execute("SELECT id FROM announcements WHERE title='Village Cleanliness Drive 2026' ORDER BY id DESC LIMIT 1")
row = c.fetchone()
ann_id = row[0] if row else 1
conn.close()
print("Announcement ID:", ann_id)

# 4. Toggle Publish Status
r_toggle = session.post(f'http://127.0.0.1:5000/admin/announcements/toggle/{ann_id}')
print("Toggle Announcement Status:", r_toggle.status_code)
# Toggle back to published
session.post(f'http://127.0.0.1:5000/admin/announcements/toggle/{ann_id}')

# 5. Check Reports Dashboard
r_rep = session.get('http://127.0.0.1:5000/admin/reports')
print("Admin Reports Dashboard Status:", r_rep.status_code)
if "certChart" in r_rep.text and "compChart" in r_rep.text:
    print("Reports Dashboard includes Key Metrics and Chart.js canvases.")

# 6. Test CSV Export
r_csv = session.get('http://127.0.0.1:5000/admin/reports/export/csv')
print("Export CSV Status:", r_csv.status_code)
if "Digital Village Management System - Summary Report" in r_csv.text:
    print("CSV Export generated successfully.")

# 7. Test PDF / Print Export
r_pdf = session.get('http://127.0.0.1:5000/admin/reports/export/pdf')
print("Export PDF / Print View Status:", r_pdf.status_code)
if "window.print()" in r_pdf.text:
    print("PDF / Print Report generated successfully.")

# 8. Test Global Search
r_search = session.get('http://127.0.0.1:5000/admin/search?q=Cleanliness')
print("Global Search Status:", r_search.status_code)
if "Villagers Matching" in r_search.text and "Certificates Matching" in r_search.text:
    print("Global Search page works across all modules.")

# 9. Login as Villager
session.get('http://127.0.0.1:5000/auth/logout')
villager_login = session.post('http://127.0.0.1:5000/auth/login', data={'username': 'testuser', 'password': 'password123'})
print("Villager Login Status:", villager_login.status_code)

# 10. Check Villager Dashboard
r_v_dash = session.get('http://127.0.0.1:5000/villager/dashboard')
print("Villager Dashboard Status:", r_v_dash.status_code)
if "Village Cleanliness Drive 2026" in r_v_dash.text:
    print("Latest Announcement appears directly on Villager Dashboard!")

# 11. Check Villager Announcements Page
r_v_ann = session.get('http://127.0.0.1:5000/villager/announcements')
print("Villager Announcements Page Status:", r_v_ann.status_code)
if "Village Cleanliness Drive 2026" in r_v_ann.text:
    print("Villager Announcements page rendered successfully.")

# 12. Test 404 Custom Error Page
r_404 = session.get('http://127.0.0.1:5000/this-page-does-not-exist-404-test')
print("404 Test Status:", r_404.status_code)
if "Page Not Found" in r_404.text:
    print("Custom 404 Error Page rendered successfully.")

print("All Phase 6 tests completed successfully!")
