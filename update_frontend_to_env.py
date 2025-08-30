#!/usr/bin/env python3
"""
Script to update frontend files to use environment variables instead of hardcoded URLs
"""
import os
import re

def update_file_to_use_config(filepath):
    """Update a single file to use API_CONFIG"""
    
    with open(filepath, 'r') as file:
        content = file.read()
    
    # Check if already updated
    if 'API_CONFIG' in content:
        print(f"⏭️  {filepath} already uses API_CONFIG")
        return 0
    
    # Add import if not present
    if 'import { API_CONFIG' not in content:
        # Find the last import statement
        import_pattern = r'(import.*?;[\n\r]*)'
        last_import = list(re.finditer(import_pattern, content))
        if last_import:
            insert_pos = last_import[-1].end()
            content = content[:insert_pos] + "import { API_CONFIG, buildUrl } from './config/api';\n" + content[insert_pos:]
        else:
            # Add at the beginning after React import
            content = content.replace(
                "import React",
                "import React\nimport { API_CONFIG, buildUrl } from './config/api';"
            )
    
    # Replace hardcoded URLs with API_CONFIG references
    replacements = [
        # Auth endpoints
        (r'[\'"`]http://[^\'"`]+/api/auth/login[\'"`]', 'API_CONFIG.ENDPOINTS.LOGIN'),
        (r'[\'"`]http://[^\'"`]+/api/auth/signup[\'"`]', 'API_CONFIG.ENDPOINTS.SIGNUP'),
        
        # Expenses - need special handling for query params
        (r'fetch\([\'"`]http://[^\'"`]+/api/expenses\?year=\$\{year\}&month=\$\{month(?:Id|Idx)?\}[\'"`]\)', 
         'fetch(buildUrl(API_CONFIG.ENDPOINTS.EXPENSES, { year, month: monthId || monthIdx || month }))'),
        (r'[\'"`]http://[^\'"`]+/api/expenses[\'"`]', 'API_CONFIG.ENDPOINTS.EXPENSES'),
        
        # Categories
        (r'[\'"`]http://[^\'"`]+/api/categories[\'"`]', 'API_CONFIG.ENDPOINTS.CATEGORIES'),
        
        # Limits - need special handling for query params
        (r'fetch\([\'"`]http://[^\'"`]+/api/limit\?year=\$\{year\}&month=\$\{month(?:Id|Idx)?\}[\'"`]\)',
         'fetch(buildUrl(API_CONFIG.ENDPOINTS.MONTHLY_LIMIT, { year, month: monthId || monthIdx || month }))'),
        (r'[\'"`]http://[^\'"`]+/api/limit[\'"`]', 'API_CONFIG.ENDPOINTS.MONTHLY_LIMIT'),
        (r'[\'"`]http://[^\'"`]+/api/global_limit[\'"`]', 'API_CONFIG.ENDPOINTS.GLOBAL_LIMIT'),
        
        # Currencies
        (r'[\'"`]http://[^\'"`]+/api/currencies[\'"`]', 'API_CONFIG.ENDPOINTS.CURRENCIES'),
        (r'[\'"`]http://[^\'"`]+/api/user/currency[\'"`]', 'API_CONFIG.ENDPOINTS.USER_CURRENCY'),
        
        # Months
        (r'[\'"`]http://[^\'"`]+/api/months[\'"`]', 'API_CONFIG.ENDPOINTS.MONTHS'),
        
        # Summary
        (r'[\'"`]http://[^\'"`]+/api/summary[\'"`]', 'API_CONFIG.ENDPOINTS.SUMMARY'),
        
        # Test DB
        (r'[\'"`]http://[^\'"`]+/api/test-db[\'"`]', 'API_CONFIG.ENDPOINTS.TEST_DB'),
    ]
    
    count = 0
    for pattern, replacement in replacements:
        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, replacement, content)
            count += matches
    
    # Handle template literals with embedded expressions
    # Replace ${year} style URLs
    template_pattern = r'`http://[^`]+/api/([^`]+)`'
    
    def replace_template(match):
        url = match.group(0)
        if '/api/expenses?' in url:
            return 'buildUrl(API_CONFIG.ENDPOINTS.EXPENSES, { year, month: monthId || monthIdx || month })'
        elif '/api/limit?' in url:
            return 'buildUrl(API_CONFIG.ENDPOINTS.MONTHLY_LIMIT, { year, month: monthId || monthIdx || month })'
        elif '/api/summary?' in url:
            return 'buildUrl(API_CONFIG.ENDPOINTS.SUMMARY, { type, year, month })'
        else:
            # For other endpoints, try to map them
            endpoint_map = {
                'expenses': 'EXPENSES',
                'categories': 'CATEGORIES',
                'months': 'MONTHS',
                'currencies': 'CURRENCIES',
                'global_limit': 'GLOBAL_LIMIT',
                'limit': 'MONTHLY_LIMIT',
                'user/currency': 'USER_CURRENCY',
            }
            for key, value in endpoint_map.items():
                if f'/api/{key}' in url:
                    return f'API_CONFIG.ENDPOINTS.{value}'
            return url
    
    template_matches = len(re.findall(template_pattern, content))
    if template_matches > 0:
        content = re.sub(template_pattern, replace_template, content)
        count += template_matches
    
    if count > 0:
        # Write updated content
        with open(filepath, 'w') as file:
            file.write(content)
        print(f"✅ Updated {filepath}: {count} replacements")
        return count
    else:
        print(f"ℹ️  No changes needed in {filepath}")
        return 0

def main():
    print("🔧 Frontend Environment Variable Migration")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('frontend/src'):
        print("❌ Please run this script from the project root directory")
        return
    
    # Files to update
    files_to_update = [
        'frontend/src/App.js',
        'frontend/src/Login.js',
        'frontend/src/Signup.js',
        'frontend/src/ExpenseTracker.js',
    ]
    
    # Also check for backup files
    if os.path.exists('frontend/src/App_backup_current.js'):
        files_to_update.append('frontend/src/App_backup_current.js')
    
    total_replacements = 0
    
    print("\n📝 Updating files to use environment variables...")
    print("-" * 50)
    
    for filepath in files_to_update:
        if os.path.exists(filepath):
            count = update_file_to_use_config(filepath)
            total_replacements += count
        else:
            print(f"⚠️  File not found: {filepath}")
    
    print("-" * 50)
    print(f"\n✨ Migration complete! Total replacements: {total_replacements}")
    
    if total_replacements > 0:
        print("\n📌 Next steps:")
        print("   1. Check frontend/.env file for correct API URL")
        print("   2. Restart the frontend: npm start")
        print("   3. The app will now use environment variables!")
        print("\n💡 To change the API URL, edit frontend/.env")
        print("   No need to modify code files anymore!")

if __name__ == "__main__":
    main()