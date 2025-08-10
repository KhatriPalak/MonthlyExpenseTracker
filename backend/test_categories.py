import requests

def test_get_categories():
    try:
        response = requests.get("http://localhost:5000/api/categories")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_get_categories()
