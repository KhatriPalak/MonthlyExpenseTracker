#!/usr/bin/env python3
"""
Script to update all hardcoded backend URLs in the frontend
"""
import os
import re

def update_urls_in_file(filepath, old_url, new_url):
    """Update URLs in a single file"""
    try:
        with open(filepath, 'r') as file:
            content = file.read()
        
        # Count replacements
        count = content.count(old_url)
        
        if count > 0:
            # Replace the URL
            updated_content = content.replace(old_url, new_url)
            
            # Write back
            with open(filepath, 'w') as file:
                file.write(updated_content)
            
            print(f"✅ Updated {filepath}: {count} replacements")
            return count
        else:
            print(f"⏭️  Skipped {filepath}: No matches found")
            return 0
    except Exception as e:
        print(f"❌ Error updating {filepath}: {e}")
        return 0

def main():
    print("🔧 Frontend URL Update Script")
    print("=" * 50)
    
    # Configuration
    OLD_URL = "http://3.141.164.136:5000"
    NEW_URL = "http://localhost:5002"
    
    print(f"📝 Replacing: {OLD_URL}")
    print(f"📝 With:      {NEW_URL}")
    print("=" * 50)
    
    # Frontend source directory
    frontend_dir = "frontend/src"
    
    if not os.path.exists(frontend_dir):
        print("❌ Frontend directory not found!")
        print("   Please run this script from the project root directory")
        return
    
    # Files to update
    files_to_update = [
        "frontend/src/App.js",
        "frontend/src/App_backup_current.js",
        "frontend/src/Login.js",
        "frontend/src/Signup.js",
        "frontend/src/ExpenseTracker.js"
    ]
    
    total_replacements = 0
    
    # Update each file
    for filepath in files_to_update:
        if os.path.exists(filepath):
            count = update_urls_in_file(filepath, OLD_URL, NEW_URL)
            total_replacements += count
        else:
            print(f"⚠️  File not found: {filepath}")
    
    print("=" * 50)
    print(f"✨ Update complete! Total replacements: {total_replacements}")
    
    if total_replacements > 0:
        print("\n📌 Next steps:")
        print("   1. Start backend: cd backend/app && python3 app_integrated.py")
        print("   2. Start frontend: cd frontend && npm start")
        print("   3. Open browser: http://localhost:3000")

if __name__ == "__main__":
    main()