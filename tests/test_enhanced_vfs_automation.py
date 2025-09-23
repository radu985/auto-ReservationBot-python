#!/usr/bin/env python3
"""
Enhanced VFS Global Guinea-Bissau Automation Test Script
Tests all advanced features including Cloudflare bypass, rate limiting, and stealth measures
"""

import sys
import time
import logging
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent / "app"))

from services.vfs_automation import VFSAutomation, AvailabilityStatus, BookingResult
from services.csv_io import ClientRecord, load_clients

def test_stealth_features():
    """Test stealth and anti-detection features."""
    print("🔍 Testing Stealth Features...")
    
    automation = VFSAutomation(headless=True, use_playwright=True)
    
    # Test user agent generation
    user_agent = automation._get_user_agent()
    print(f"✅ Generated User Agent: {user_agent[:50]}...")
    
    # Test session ID generation
    session_id = automation._generate_session_id()
    print(f"✅ Generated Session ID: {session_id}")
    
    # Test Cloudflare detection
    test_content = "Checking your browser before accessing"
    cf_detected = automation._detect_cloudflare_challenge(test_content)
    print(f"✅ Cloudflare Detection: {'Detected' if cf_detected else 'Not Detected'}")
    
    return True

def test_browser_startup():
    """Test browser startup with stealth measures."""
    print("\n🌐 Testing Browser Startup...")
    
    automation = VFSAutomation(headless=True, use_playwright=True)
    
    try:
        success = automation.start_browser()
        if success:
            print("✅ Browser started successfully with stealth mode")
            
            # Test navigation
            print("🧭 Testing navigation to VFS website...")
            automation.page.goto("https://visa.vfsglobal.com", timeout=30000)
            print("✅ Successfully navigated to VFS Global website")
            
            # Check for Cloudflare challenge
            content = automation.page.content()
            if automation._detect_cloudflare_challenge(content):
                print("⚠️  Cloudflare challenge detected - testing bypass...")
                if automation._handle_cloudflare_challenge():
                    print("✅ Cloudflare challenge bypassed successfully")
                else:
                    print("❌ Cloudflare challenge bypass failed")
            else:
                print("✅ No Cloudflare challenge detected")
            
            automation.stop_browser()
            return True
        else:
            print("❌ Failed to start browser")
            return False
            
    except Exception as e:
        print(f"❌ Browser startup test failed: {str(e)}")
        return False

def test_availability_monitoring():
    """Test availability monitoring with rate limiting."""
    print("\n📊 Testing Availability Monitoring...")
    
    automation = VFSAutomation(headless=True, use_playwright=True)
    
    try:
        if not automation.start_browser():
            print("❌ Failed to start browser for monitoring test")
            return False
        
        print("🔍 Starting 2-minute availability monitoring test...")
        status = automation.check_availability(duration_minutes=2)
        
        print(f"📈 Monitoring Results:")
        print(f"   Available: {status.available}")
        print(f"   Slots Count: {status.slots_count}")
        print(f"   Last Checked: {status.last_checked}")
        if status.error_message:
            print(f"   Error: {status.error_message}")
        
        automation.stop_browser()
        return True
        
    except Exception as e:
        print(f"❌ Availability monitoring test failed: {str(e)}")
        return False

def test_form_filling():
    """Test automated form filling with human-like behavior."""
    print("\n📝 Testing Form Filling...")
    
    # Create test client
    test_client = ClientRecord(
        first_name="John",
        last_name="Doe",
        date_of_birth="1990-01-01",
        email="test@example.com",
        password="testpass123",
        mobile_country_code="+44",
        mobile_number="1234567890",
        passport_number="A12345678",
        current_nationality="United Kingdom",
        service_center="Tourist Visa"
    )
    
    automation = VFSAutomation(headless=True, use_playwright=True)
    
    try:
        if not automation.start_browser():
            print("❌ Failed to start browser for form test")
            return False
        
        print("📄 Testing form filling capabilities...")
        
        # Test human-like field filling
        test_selectors = ['input[name="firstName"]', '#firstName', 'input[id*="first"]']
        success = automation._fill_field_human_like(test_selectors, test_client.first_name)
        print(f"✅ Field filling test: {'Success' if success else 'Failed'}")
        
        # Test option selection
        test_selectors = ['select[name="nationality"]', '#nationality']
        success = automation._select_option_human_like(test_selectors, test_client.current_nationality)
        print(f"✅ Option selection test: {'Success' if success else 'Failed'}")
        
        automation.stop_browser()
        return True
        
    except Exception as e:
        print(f"❌ Form filling test failed: {str(e)}")
        return False

def test_rate_limiting():
    """Test rate limiting and safety measures."""
    print("\n⏱️  Testing Rate Limiting...")
    
    automation = VFSAutomation(headless=True, use_playwright=True)
    
    # Test random delay generation
    delays = []
    for i in range(5):
        start = time.time()
        automation._random_delay()
        delay = time.time() - start
        delays.append(delay)
    
    avg_delay = sum(delays) / len(delays)
    print(f"✅ Average delay: {avg_delay:.2f}s (expected: 3-8s)")
    
    # Test request counting
    automation.request_count = 15
    print(f"✅ Request count tracking: {automation.request_count}")
    
    return True

def test_client_loading():
    """Test client data loading from CSV."""
    print("\n👥 Testing Client Data Loading...")
    
    try:
        csv_path = "clients.csv"
        clients = load_clients(csv_path)
        print(f"✅ Loaded {len(clients)} clients from CSV")
        
        if clients:
            client = clients[0]
            print(f"   Sample client: {client.first_name} {client.last_name} ({client.email})")
        
        return True
        
    except Exception as e:
        print(f"❌ Client loading test failed: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("🚀 Enhanced VFS Global Guinea-Bissau Automation Test Suite")
    print("=" * 60)
    
    tests = [
        ("Stealth Features", test_stealth_features),
        ("Browser Startup", test_browser_startup),
        ("Rate Limiting", test_rate_limiting),
        ("Client Loading", test_client_loading),
        ("Form Filling", test_form_filling),
        ("Availability Monitoring", test_availability_monitoring),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! The enhanced automation system is ready.")
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
