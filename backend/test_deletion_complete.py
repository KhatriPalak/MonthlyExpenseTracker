import requests
import json

def test_category_operations():
    """Test category creation and deletion"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Category Operations")
    print("=" * 40)
    
    # Step 1: Get existing categories
    print("1. Getting existing categories...")
    response = requests.get(f"{base_url}/api/categories")
    if response.status_code == 200:
        categories = response.json().get('categories', [])
        print(f"   Found {len(categories)} categories")
        for cat in categories[:3]:  # Show first 3
            print(f"   - {cat['category_name']} (ID: {cat['category_id']})")
    else:
        print(f"   ❌ Error: {response.status_code} - {response.text}")
        return
    
    # Step 2: Create a test category
    print("\n2. Creating test category...")
    test_category_name = "Test Category For Deletion"
    create_response = requests.post(f"{base_url}/api/categories", 
        headers={'Content-Type': 'application/json'},
        json={'category_name': test_category_name}
    )
    
    if create_response.status_code in [200, 201]:
        created_category = create_response.json().get('category', {})
        test_category_id = created_category.get('category_id')
        print(f"   ✅ Created category: {test_category_name} (ID: {test_category_id})")
    else:
        print(f"   ❌ Failed to create category: {create_response.status_code} - {create_response.text}")
        return
    
    # Step 3: Delete the test category
    print(f"\n3. Deleting test category (ID: {test_category_id})...")
    delete_response = requests.delete(f"{base_url}/api/categories/{test_category_id}",
        headers={'Content-Type': 'application/json'}
    )
    
    if delete_response.status_code == 200:
        result = delete_response.json()
        print(f"   ✅ {result.get('message', 'Category deleted successfully')}")
    else:
        print(f"   ❌ Failed to delete category: {delete_response.status_code}")
        print(f"   Error: {delete_response.text}")
        return
    
    # Step 4: Verify category is gone from active list
    print("\n4. Verifying category is hidden from active list...")
    response = requests.get(f"{base_url}/api/categories")
    if response.status_code == 200:
        categories_after = response.json().get('categories', [])
        deleted_category_found = any(cat['category_id'] == test_category_id for cat in categories_after)
        
        if deleted_category_found:
            print("   ❌ Category still appears in active list (deletion failed)")
        else:
            print("   ✅ Category successfully hidden from active list")
            print(f"   Total categories now: {len(categories_after)}")
    
    print("\n" + "=" * 40)
    print("🎉 Test completed!")

if __name__ == "__main__":
    try:
        test_category_operations()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server")
        print("💡 Make sure your Flask server is running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Test failed: {e}")
