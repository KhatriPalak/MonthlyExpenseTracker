#!/usr/bin/env python3
"""
Script to create a default user for testing expenses
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.app import app, db, User
import hashlib

def create_default_user():
    with app.app_context():
        # Check if user with ID 1 exists
        existing_user = User.query.filter_by(user_id=1).first()
        if existing_user:
            print(f"User with ID 1 already exists: {existing_user.username} ({existing_user.email})")
            return
        
        # Create default user
        default_user = User(
            username="default_user",
            email="default@example.com",
            password=hashlib.sha256("password123".encode()).hexdigest(),
            global_limit=1000.0
        )
        
        db.session.add(default_user)
        db.session.commit()
        
        print(f"Created default user with ID: {default_user.user_id}")
        print(f"Username: {default_user.username}")
        print(f"Email: {default_user.email}")

if __name__ == "__main__":
    create_default_user()
