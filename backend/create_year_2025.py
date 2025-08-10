#!/usr/bin/env python3

import sys
import os

# Add the app directory to the path to import our models
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from models import db, Year
from app import app

def create_year_2025():
    """Create the year 2025 in the database if it doesn't exist"""
    with app.app_context():
        try:
            # Check if year 2025 already exists
            existing_year = Year.query.filter_by(year_number=2025).first()
            if existing_year:
                print(f"Year 2025 already exists with year_id: {existing_year.year_id}")
                return existing_year.year_id
            
            # Create new year record
            new_year = Year(year_number=2025)
            db.session.add(new_year)
            db.session.commit()
            
            print(f"Successfully created year 2025 with year_id: {new_year.year_id}")
            return new_year.year_id
            
        except Exception as e:
            print(f"Error creating year 2025: {str(e)}")
            db.session.rollback()
            return None

if __name__ == "__main__":
    create_year_2025()
