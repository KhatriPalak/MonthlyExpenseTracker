#!/usr/bin/env python3
"""
Quick test script for PDF download functionality
"""
import requests
import os

BASE_URL = "http://localhost:5000"

def test_pdf_download():
    """Test the PDF download endpoint"""
    
    print("🔧 Testing PDF Download API...")
    print("=" * 40)
    
    try:
        # Test monthly PDF download
        params = {
            "type": "monthly", 
            "year": "2024", 
            "month": "12", 
            "format": "pdf"
        }
        
        print("Making request to download API...")
        response = requests.get(f"{BASE_URL}/api/summary/download", params=params)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'Not set')}")
        print(f"Content-Disposition: {response.headers.get('Content-Disposition', 'Not set')}")
        print(f"Content Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            # Save the PDF file
            filename = "test_pdf_download.pdf"
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ PDF file saved as: {filename}")
            print(f"File size: {os.path.getsize(filename)} bytes")
            
            # Check if it's actually a PDF
            with open(filename, 'rb') as f:
                header = f.read(8)
                if header.startswith(b'%PDF'):
                    print("✅ File is a valid PDF!")
                else:
                    print(f"❌ File doesn't appear to be a PDF. Header: {header}")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Make sure the backend server is running on localhost:5000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_pdf_download()
