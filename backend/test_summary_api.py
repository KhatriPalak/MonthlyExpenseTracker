import requests
import json

def test_summary_endpoints():
    """Test the new summary endpoints"""
    base_url = "http://3.141.164.136:5000"
    
    print("🧪 Testing Summary Endpoints")
    print("=" * 50)
    
    # Test monthly summary
    print("1. Testing Monthly Summary...")
    response = requests.get(f"{base_url}/api/summary?type=monthly&year=2025&month=8")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        summary = data.get('summary', {})
        print(f"   ✅ Monthly summary: ${summary.get('total_amount', 0):.2f} in {summary.get('total_count', 0)} transactions")
    else:
        print(f"   ❌ Error: {response.text}")
    
    # Test yearly summary
    print("\n2. Testing Yearly Summary...")
    response = requests.get(f"{base_url}/api/summary?type=yearly&year=2025")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        summary = data.get('summary', {})
        print(f"   ✅ Yearly summary: ${summary.get('total_amount', 0):.2f} in {summary.get('total_count', 0)} transactions")
        monthly_breakdown = summary.get('monthly_breakdown', {})
        if monthly_breakdown:
            print("   📊 Monthly breakdown:")
            for month, data in monthly_breakdown.items():
                print(f"      {month}: ${data['total']:.2f}")
    else:
        print(f"   ❌ Error: {response.text}")
    
    # Test custom date range summary
    print("\n3. Testing Custom Date Range Summary...")
    response = requests.get(f"{base_url}/api/summary?type=custom&start_date=2025-08-01&end_date=2025-08-31")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        summary = data.get('summary', {})
        print(f"   ✅ Custom range summary: ${summary.get('total_amount', 0):.2f} in {summary.get('total_count', 0)} transactions")
        category_breakdown = summary.get('category_breakdown', {})
        if category_breakdown:
            print("   📊 Category breakdown:")
            for category, data in list(category_breakdown.items())[:3]:  # Show top 3
                print(f"      {category}: ${data['total']:.2f}")
    else:
        print(f"   ❌ Error: {response.text}")
    
    print("\n" + "=" * 50)
    print("🎉 Summary endpoint tests completed!")

if __name__ == "__main__":
    try:
        test_summary_endpoints()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server")
        print("💡 Make sure your Flask server is running on http://3.141.164.136:5000")
    except Exception as e:
        print(f"❌ Test failed: {e}")
