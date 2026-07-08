import requests
import os

session = requests.Session()

# 1. Login as villager (created in phase 2)
login_data = {
    'username': 'testuser',
    'password': 'password123'
}
r_login = session.post('http://127.0.0.1:5000/auth/login', data=login_data)
print("Villager Login Status:", r_login.status_code)

# 2. Apply for a Certificate
# Create a dummy file for upload
with open('dummy.txt', 'w') as f:
    f.write('This is a dummy document.')

with open('dummy.txt', 'rb') as f:
    files = {'document': ('dummy.txt', f, 'text/plain')}
    cert_data = {
        'type': 'Income Certificate',
        'applicant_name': 'Test User',
        'address': 'Test Village',
        'mobile': '9876543210',
        'aadhaar': '123456789012'
    }
    r_apply = session.post('http://127.0.0.1:5000/villager/certificates/apply', data=cert_data, files=files)
print("Apply Certificate Status:", r_apply.status_code)

# 3. View Villager Certificates
r_certs = session.get('http://127.0.0.1:5000/villager/certificates')
print("Villager Certificates Status:", r_certs.status_code)
if "Income Certificate" in r_certs.text:
    print("Certificate application appeared in villager dashboard.")
else:
    print("Certificate not found in villager dashboard.")

# 4. Login as Admin
# Need to create admin user first. Since we don't have register admin UI, we'll do it via a quick script inline or check if one exists.
# We'll just create a separate script to create the admin in DB, or I'll just write it here using sqlite3.
import sqlite3
conn = sqlite3.connect('digital_village.db')
c = conn.cursor()
# Import werkzeug hash
from werkzeug.security import generate_password_hash
pw_hash = generate_password_hash('admin123')
try:
    c.execute("INSERT INTO users (username, password_hash, role) VALUES ('admin', ?, 'admin')", (pw_hash,))
    conn.commit()
    print("Admin user created in DB.")
except sqlite3.IntegrityError:
    print("Admin user already exists.")
conn.close()

# Now login as admin
admin_session = requests.Session()
admin_login = admin_session.post('http://127.0.0.1:5000/auth/login', data={'username': 'admin', 'password': 'admin123'})
print("Admin Login Status:", admin_login.status_code)

# 5. Admin Dashboard
r_admin_dash = admin_session.get('http://127.0.0.1:5000/admin/dashboard')
print("Admin Dashboard Status:", r_admin_dash.status_code)

# 6. Admin Update Certificate (Assuming ID=1 since it's the first one)
update_data = {
    'status': 'Approved',
    'remarks': 'All documents verified.'
}
r_update = admin_session.post('http://127.0.0.1:5000/admin/certificates/update/1', data=update_data)
print("Admin Update Cert Status:", r_update.status_code)

# 7. Villager Download Acknowledgement
r_ack = session.get('http://127.0.0.1:5000/villager/certificates/1/acknowledgement')
print("Villager Acknowledgement Status:", r_ack.status_code)
if "All documents verified" in r_ack.text:
    print("Acknowledgement generated successfully with admin remarks.")

# Cleanup dummy file
if os.path.exists('dummy.txt'):
    os.remove('dummy.txt')
