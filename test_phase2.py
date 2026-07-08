import requests

session = requests.Session()

# 1. Register a user
register_data = {
    'username': 'testuser',
    'password': 'password123',
    'full_name': 'Test User',
    'mobile': '9876543210',
    'aadhaar': '123456789012',
    'address': 'Test Village'
}
r_reg = session.post('http://127.0.0.1:5000/auth/register', data=register_data)
print("Register Status:", r_reg.status_code)

# 2. Login
login_data = {
    'username': 'testuser',
    'password': 'password123'
}
r_login = session.post('http://127.0.0.1:5000/auth/login', data=login_data)
print("Login Status:", r_login.status_code)

# 3. Access Dashboard
r_dash = session.get('http://127.0.0.1:5000/villager/dashboard')
print("Dashboard Status:", r_dash.status_code)
if "Welcome, testuser" in r_dash.text:
    print("Dashboard loaded successfully with user context.")
else:
    print("Failed to load dashboard correctly.")
