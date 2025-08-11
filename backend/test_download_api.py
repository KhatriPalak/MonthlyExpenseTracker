#!/usr/bin/env python3
"""
Test script for the download summary API endpoint
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_download_api():
    """Test the download summary API with different parameters"""
    
    print("🧪 Testing Download Summary API...")
    print("=" * 50)
    
    # Test cases for different summary types and formats
    test_cases = [
        {
            "name": "Monthly CSV Download",
            "params": {"type": "monthly", "year": "2024", "month": "12", "format": "csv"}
        },
        {
            "name": "Monthly PDF Download", 
            "params": {"type": "monthly", "year": "2024", "month": "12", "format": "pdf"}
        },
        {
            "name": "Yearly CSV Download",
            "params": {"type": "yearly", "year": "2024", "format": "csv"}
        },
        {
            "name": "Custom Range CSV Download",
            "params": {"type": "custom", "start_date": "2024-12-01", "end_date": "2024-12-31", "format": "csv"}
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 30)
        
        try:
            # Make API request
            response = requests.get(f"{BASE_URL}/api/summary/download", params=test_case['params'])
            
            print(f"Status Code: {response.status_code}")
            print(f"Content-Type: {response.headers.get('Content-Type', 'Not set')}")
            print(f"Content-Disposition: {response.headers.get('Content-Disposition', 'Not set')}")
            print(f"Content Length: {len(response.content)} bytes")
            
            if response.status_code == 200:
                # Try to save a sample file to verify content
                filename = f"test_download_{test_case['params']['format']}_{i}.{test_case['params']['format']}"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Downloaded sample file: {filename}")
                
                # Show first few bytes for verification
                if test_case['params']['format'] == 'csv':
                    print(f"Sample content: {response.content[:100].decode('utf-8', errors='ignore')}...")
                else:
                    print(f"Sample content (first 50 bytes): {response.content[:50]}...")
                    
            else:
                print(f"❌ Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Download API tests completed!")

if __name__ == "__main__":
    test_download_api()
