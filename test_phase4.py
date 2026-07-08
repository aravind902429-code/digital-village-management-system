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

# 2. Submit a Complaint
# Create a dummy image file for upload
with open('dummy_img.png', 'w') as f:
    f.write('dummy image data')

with open('dummy_img.png', 'rb') as f:
    files = {'image': ('dummy_img.png', f, 'image/png')}
    complaint_data = {
        'category': 'Water Supply',
        'description': 'No water supply since yesterday in block A.'
    }
    r_submit = session.post('http://127.0.0.1:5000/villager/complaints/submit', data=complaint_data, files=files)
print("Submit Complaint Status:", r_submit.status_code)

# 3. View Villager Complaints
r_cmplts = session.get('http://127.0.0.1:5000/villager/complaints')
print("Villager Complaints Status:", r_cmplts.status_code)
if "Water Supply" in r_cmplts.text:
    print("Complaint appeared in villager dashboard.")
else:
    print("Complaint not found in villager dashboard.")

# 4. View Villager Dashboard stats
r_dash = session.get('http://127.0.0.1:5000/villager/dashboard')
if "Active Complaints" in r_dash.text:
    print("Villager Dashboard stats updated.")

# 5. Login as Admin
admin_session = requests.Session()
admin_login = admin_session.post('http://127.0.0.1:5000/auth/login', data={'username': 'admin', 'password': 'admin123'})
print("Admin Login Status:", admin_login.status_code)

# 6. Admin Dashboard stats
r_admin_dash = admin_session.get('http://127.0.0.1:5000/admin/dashboard')
if "Pending Complaints" in r_admin_dash.text:
    print("Admin Dashboard stats updated.")

# 7. Admin Update Complaint (Assuming ID=1 since it's the first one)
update_data = {
    'status': 'Resolved',
    'remarks': 'Water supply restored successfully.'
}
r_update = admin_session.post('http://127.0.0.1:5000/admin/complaints/update/1', data=update_data)
print("Admin Update Complaint Status:", r_update.status_code)

# Cleanup dummy file
if os.path.exists('dummy_img.png'):
    os.remove('dummy_img.png')
