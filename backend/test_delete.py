import requests

# Test category deletion
def test_category_deletion():
    base_url = "http://localhost:5000"
    
    # First get all categories
    print("1. Getting all categories...")
    response = requests.get(f"{base_url}/api/categories")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        categories = response.json()['categories']
        print(f"Found {len(categories)} categories:")
        for cat in categories:
            print(f"  - ID: {cat['category_id']}, Name: {cat['category_name']}")
        
        if categories:
            # Try to delete the first category
            category_to_delete = categories[0]
            print(f"\n2. Deleting category: {category_to_delete['category_name']} (ID: {category_to_delete['category_id']})")
            
            delete_response = requests.delete(f"{base_url}/api/categories/{category_to_delete['category_id']}")
            print(f"Delete Status: {delete_response.status_code}")
            print(f"Delete Response: {delete_response.json()}")
            
            # Get categories again to verify deletion
            print(f"\n3. Getting categories after deletion...")
            response_after = requests.get(f"{base_url}/api/categories")
            if response_after.status_code == 200:
                categories_after = response_after.json()['categories']
                print(f"Found {len(categories_after)} categories after deletion:")
                for cat in categories_after:
                    print(f"  - ID: {cat['category_id']}, Name: {cat['category_name']}")
            
    else:
        print(f"Error getting categories: {response.json()}")

if __name__ == "__main__":
    test_category_deletion()
