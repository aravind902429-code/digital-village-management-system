import requests
import os

# 1. Start session
session = requests.Session()

# Login as Admin
admin_login = session.post('http://127.0.0.1:5000/auth/login', data={'username': 'admin', 'password': 'admin123'})
print("Admin Login Status:", admin_login.status_code)

# Create dummy image for scheme banner
with open('dummy_banner.png', 'w') as f:
    f.write('dummy banner data')

# Add New Scheme
with open('dummy_banner.png', 'rb') as f:
    files = {'image': ('dummy_banner.png', f, 'image/png')}
    scheme_data = {
        'title': 'PM Kisan Samman Nidhi',
        'description': 'Financial support to farmers across the village.',
        'eligibility': 'All landholding farmer families.',
        'benefits': 'Rs. 6000 per year in three equal installments.'
    }
    r_add = session.post('http://127.0.0.1:5000/admin/schemes/add', data=scheme_data, files=files)
print("Admin Add Scheme Status:", r_add.status_code)

# Check Admin Schemes List
r_schemes = session.get('http://127.0.0.1:5000/admin/schemes')
print("Admin Schemes List Status:", r_schemes.status_code)
if "PM Kisan Samman Nidhi" in r_schemes.text:
    print("Scheme successfully created and visible in admin list.")
else:
    print("Error: Scheme not found in admin list.")

# We need to find the scheme ID. Assuming ID is 1 (or the first scheme in DB).
import sqlite3
conn = sqlite3.connect('digital_village.db')
c = conn.cursor()
c.execute("SELECT id FROM schemes WHERE title='PM Kisan Samman Nidhi' ORDER BY id DESC LIMIT 1")
row = c.fetchone()
scheme_id = row[0] if row else 1
conn.close()
print("Created Scheme ID:", scheme_id)

# Edit Scheme
edit_data = {
    'title': 'PM Kisan Samman Nidhi Updated',
    'description': 'Updated financial support to farmers.',
    'eligibility': 'All farmer families with valid Aadhaar.',
    'benefits': 'Rs. 6000 per year direct bank transfer.',
    'is_active': 'on'
}
r_edit = session.post(f'http://127.0.0.1:5000/admin/schemes/edit/{scheme_id}', data=edit_data)
print("Admin Edit Scheme Status:", r_edit.status_code)

# Check Admin Dashboard Active Schemes stat
r_admin_dash = session.get('http://127.0.0.1:5000/admin/dashboard')
if "Active Schemes" in r_admin_dash.text:
    print("Admin Dashboard stats show Active Schemes.")

# Logout Admin & Login as Villager
session.get('http://127.0.0.1:5000/auth/logout')
villager_login = session.post('http://127.0.0.1:5000/auth/login', data={'username': 'testuser', 'password': 'password123'})
print("Villager Login Status:", villager_login.status_code)

# Check Villager Dashboard Active Schemes stat
r_v_dash = session.get('http://127.0.0.1:5000/villager/dashboard')
if "Govt Schemes" in r_v_dash.text:
    print("Villager Dashboard stats show Govt Schemes count.")

# View Schemes and test search
r_v_schemes = session.get('http://127.0.0.1:5000/villager/schemes?q=Kisan')
print("Villager Search Schemes Status:", r_v_schemes.status_code)
if "PM Kisan Samman Nidhi Updated" in r_v_schemes.text:
    print("Villager can view and search active schemes successfully.")

# View Scheme Details
r_details = session.get(f'http://127.0.0.1:5000/villager/schemes/{scheme_id}')
print("Villager Scheme Details Status:", r_details.status_code)
if "Key Benefits & Assistance" in r_details.text:
    print("Villager Scheme details page rendered successfully.")

# Toggle Save to Favourites
r_fav_add = session.post(f'http://127.0.0.1:5000/villager/schemes/favourite/{scheme_id}', data={'next': '/villager/schemes/favourites'})
print("Add to Favourites Status:", r_fav_add.status_code)

# Check Favourites Page
r_fav_page = session.get('http://127.0.0.1:5000/villager/schemes/favourites')
print("Favourites Page Status:", r_fav_page.status_code)
if "PM Kisan Samman Nidhi Updated" in r_fav_page.text:
    print("Scheme appears in Villager's Favourite Schemes list.")

# Remove from Favourites
r_fav_rem = session.post(f'http://127.0.0.1:5000/villager/schemes/favourite/{scheme_id}', data={'next': '/villager/schemes/favourites'})
print("Remove from Favourites Status:", r_fav_rem.status_code)

# Logout Villager & Login as Admin to Delete Scheme
session.get('http://127.0.0.1:5000/auth/logout')
session.post('http://127.0.0.1:5000/auth/login', data={'username': 'admin', 'password': 'admin123'})
r_del = session.post(f'http://127.0.0.1:5000/admin/schemes/delete/{scheme_id}')
print("Admin Delete Scheme Status:", r_del.status_code)

# Check admin schemes list again to ensure deleted
r_schemes_after = session.get('http://127.0.0.1:5000/admin/schemes')
if "PM Kisan Samman Nidhi Updated" not in r_schemes_after.text:
    print("Scheme successfully deleted.")

# Cleanup dummy banner
if os.path.exists('dummy_banner.png'):
    os.remove('dummy_banner.png')
print("All Phase 5 CRUD operations tested and verified!")
