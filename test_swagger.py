#!/usr/bin/env python3
"""
Script to test Swagger UI functionality
"""

import requests
import webbrowser
import time
import subprocess
import sys
from pathlib import Path

def check_server_running(url="http://localhost:8000"):
    """Check if the FastAPI server is running"""
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def test_swagger_endpoints():
    """Test that Swagger endpoints are accessible"""
    base_url = "http://localhost:8000"
    
    endpoints = {
        "Swagger UI": f"{base_url}/docs",
        "ReDoc": f"{base_url}/redoc", 
        "OpenAPI JSON": f"{base_url}/openapi.json"
    }
    
    print("🧪 Testing Swagger Documentation Endpoints")
    print("=" * 50)
    
    for name, url in endpoints.items():
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {name}: {url} - Working")
                if name == "OpenAPI JSON":
                    # Check if it's valid JSON
                    try:
                        data = response.json()
                        print(f"   📊 API Title: {data.get('info', {}).get('title', 'Unknown')}")
                        print(f"   📊 API Version: {data.get('info', {}).get('version', 'Unknown')}")
                        print(f"   📊 Total Endpoints: {len(data.get('paths', {}))}")
                    except:
                        print(f"   ⚠️  Response is not valid JSON")
            else:
                print(f"❌ {name}: {url} - Error {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {name}: {url} - Connection Error: {e}")
    
    return endpoints

def open_browser_tabs(endpoints):
    """Open Swagger documentation in browser tabs"""
    try:
        print(f"\n🌐 Opening Swagger documentation in browser...")
        webbrowser.open(endpoints["Swagger UI"])
        time.sleep(1)
        webbrowser.open(endpoints["ReDoc"])
        print("✅ Browser tabs opened successfully!")
        return True
    except Exception as e:
        print(f"❌ Error opening browser: {e}")
        return False

def start_server_if_needed():
    """Start the FastAPI server if it's not running"""
    if not check_server_running():
        print("⚠️  Server not running. Attempting to start...")
        try:
            # Try to start the server
            print("🚀 Starting FastAPI server...")
            subprocess.Popen([
                sys.executable, "main.py"
            ], cwd=Path(__file__).parent)
            
            # Wait for server to start
            for i in range(10):
                time.sleep(1)
                if check_server_running():
                    print("✅ Server started successfully!")
                    return True
                print(f"   Waiting for server... ({i+1}/10)")
            
            print("❌ Server failed to start within 10 seconds")
            return False
        except Exception as e:
            print(f"❌ Error starting server: {e}")
            return False
    else:
        print("✅ Server is already running!")
        return True

def main():
    """Main function"""
    print("🔧 FastAPI Swagger UI Test")
    print("=" * 50)
    
    # Check if server is running, start if needed
    if not start_server_if_needed():
        print("\n❌ Cannot proceed without running server")
        print("💡 Manual start: python main.py")
        return
    
    # Test Swagger endpoints
    endpoints = test_swagger_endpoints()
    
    # Ask user if they want to open browser
    print(f"\n🌐 Swagger Documentation URLs:")
    for name, url in endpoints.items():
        print(f"   {name}: {url}")
    
    try:
        choice = input(f"\nOpen Swagger UI in browser? (y/n): ").lower().strip()
        if choice in ['y', 'yes']:
            open_browser_tabs(endpoints)
        else:
            print("📝 You can manually open the URLs above in your browser")
    except KeyboardInterrupt:
        print(f"\n👋 Cancelled by user")
    
    print(f"\n🎉 Swagger UI testing complete!")
    print(f"📖 Access documentation at: http://localhost:8000/docs")

if __name__ == "__main__":
    main()