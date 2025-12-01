from app import app, db
from models import User

with app.app_context():
    print("Checking for existing users...")
    user_count = User.query.count()
    print(f"User count: {user_count}")
    
    if user_count == 0:
        print("Creating test user...")
        user = User(username='testuser', email='test@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        print("Test user created.")
        
    user = User.query.first()
    print(f"Found user: {user.username}")
