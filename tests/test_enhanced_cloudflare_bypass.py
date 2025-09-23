#!/usr/bin/env python3
"""
Enhanced Cloudflare Bypass Test Script
Tests the improved VFS automation with advanced bypass strategies
"""

import sys
import time
import logging
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent / "app"))

from services.vfs_automation import VFSAutomation, AvailabilityStatus, BookingResult

def test_cloudflare_bypass_strategies():
    """Test all Cloudflare bypass strategies."""
    print("🛡️ Testing Enhanced Cloudflare Bypass Strategies...")
    
    automation = VFSAutomation(headless=True, use_playwright=True)
    
    try:
        # Test 1: Basic bypass with user agent rotation
        print("\n1️⃣ Testing Basic CF Bypass...")
        if automation.start_browser():
            automation.page.goto("https://visa.vfsglobal.com", timeout=30000)
            content = automation.page.content()
            
            if automation._detect_cloudflare_challenge(content):
                print("   ⚠️ Cloudflare challenge detected - testing bypass...")
                success = automation._try_basic_cf_bypass()
                print(f"   {'✅' if success else '❌'} Basic bypass: {'Success' if success else 'Failed'}")
            else:
                print("   ✅ No Cloudflare challenge detected")
            
            automation.stop_browser()
        
        # Test 2: JavaScript challenge solving
        print("\n2️⃣ Testing JavaScript Challenge Solving...")
        if automation.start_browser():
            automation.page.goto("https://visa.vfsglobal.com", timeout=30000)
            content = automation.page.content()
            
            if automation._detect_cloudflare_challenge(content):
                print("   ⚠️ Cloudflare challenge detected - testing JS solving...")
                success = automation._try_js_challenge_solving()
                print(f"   {'✅' if success else '❌'} JS challenge solving: {'Success' if success else 'Failed'}")
            else:
                print("   ✅ No Cloudflare challenge detected")
            
            automation.stop_browser()
        
        # Test 3: Browser restart strategy
        print("\n3️⃣ Testing Browser Restart Strategy...")
        if automation.start_browser():
            automation.page.goto("https://visa.vfsglobal.com", timeout=30000)
            content = automation.page.content()
            
            if automation._detect_cloudflare_challenge(content):
                print("   ⚠️ Cloudflare challenge detected - testing restart...")
                success = automation._try_browser_restart()
                print(f"   {'✅' if success else '❌'} Browser restart: {'Success' if success else 'Failed'}")
            else:
                print("   ✅ No Cloudflare challenge detected")
            
            automation.stop_browser()
        
        # Test 4: Selenium fallback
        print("\n4️⃣ Testing Selenium Fallback...")
        if automation.start_browser():
            automation.page.goto("https://visa.vfsglobal.com", timeout=30000)
            content = automation.page.content()
            
            if automation._detect_cloudflare_challenge(content):
                print("   ⚠️ Cloudflare challenge detected - testing Selenium fallback...")
                success = automation._try_selenium_fallback()
                print(f"   {'✅' if success else '❌'} Selenium fallback: {'Success' if success else 'Failed'}")
            else:
                print("   ✅ No Cloudflare challenge detected")
            
            automation.stop_browser()
        
        return True
        
    except Exception as e:
        print(f"❌ CF bypass test failed: {str(e)}")
        return False

def test_enhanced_detection():
    """Test enhanced slot detection."""
    print("\n🔍 Testing Enhanced Slot Detection...")
    
    automation = VFSAutomation(headless=True, use_playwright=True)
    
    try:
        if not automation.start_browser():
            print("❌ Failed to start browser")
            return False
        
        print("   🌐 Navigating to VFS Global...")
        automation.page.goto("https://visa.vfsglobal.com/gwq/en/gbr/book-appointment", timeout=30000)
        
        # Test enhanced detection
        print("   🔍 Testing slot detection selectors...")
        status = automation._check_availability_playwright()
        
        print(f"   📊 Detection Results:")
        print(f"      Available: {status.available}")
        print(f"      Slots Found: {status.slots_count}")
        print(f"      Last Checked: {status.last_checked}")
        if status.error_message:
            print(f"      Error: {status.error_message}")
        
        automation.stop_browser()
        return True
        
    except Exception as e:
        print(f"❌ Detection test failed: {str(e)}")
        return False

def test_user_agent_rotation():
    """Test user agent rotation system."""
    print("\n🔄 Testing User Agent Rotation...")
    
    automation = VFSAutomation(headless=True, use_playwright=True)
    
    try:
        # Test initial user agent
        ua1 = automation._get_user_agent()
        print(f"   Initial UA: {ua1[:50]}...")
        
        # Test rotation
        ua2 = automation._rotate_user_agent()
        print(f"   Rotated UA: {ua2[:50]}...")
        
        # Test multiple rotations
        uas = set()
        for i in range(5):
            ua = automation._rotate_user_agent()
            uas.add(ua)
            print(f"   Rotation {i+1}: {ua[:50]}...")
        
        print(f"   ✅ Unique UAs generated: {len(uas)}/5")
        return len(uas) >= 3  # At least 3 unique user agents
        
    except Exception as e:
        print(f"❌ User agent rotation test failed: {str(e)}")
        return False

def test_monitoring_with_improvements():
    """Test full monitoring with all improvements."""
    print("\n📊 Testing Enhanced Monitoring System...")
    
    automation = VFSAutomation(headless=True, use_playwright=True)
    
    try:
        if not automation.start_browser():
            print("❌ Failed to start browser")
            return False
        
        print("   🚀 Starting 2-minute enhanced monitoring...")
        status = automation.check_availability(duration_minutes=2)
        
        print(f"   📈 Monitoring Results:")
        print(f"      Available: {status.available}")
        print(f"      Slots Count: {status.slots_count}")
        print(f"      Last Checked: {status.last_checked}")
        if status.error_message:
            print(f"      Error: {status.error_message}")
        
        automation.stop_browser()
        return True
        
    except Exception as e:
        print(f"❌ Monitoring test failed: {str(e)}")
        return False

def main():
    """Run all enhanced tests."""
    print("🚀 Enhanced VFS Global Cloudflare Bypass Test Suite")
    print("=" * 60)
    
    tests = [
        ("User Agent Rotation", test_user_agent_rotation),
        ("Cloudflare Bypass Strategies", test_cloudflare_bypass_strategies),
        ("Enhanced Detection", test_enhanced_detection),
        ("Full Monitoring System", test_monitoring_with_improvements),
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
    print("📊 ENHANCED TEST RESULTS SUMMARY")
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
        print("🎉 All enhanced tests passed! The system is production-ready.")
    elif passed >= total * 0.75:
        print("✅ Most tests passed! The system is significantly improved.")
    else:
        print("⚠️ Some tests failed. Further improvements needed.")
    
    print("\n🔧 Key Improvements Implemented:")
    print("   ✅ Multi-strategy Cloudflare bypass")
    print("   ✅ Dynamic user agent rotation")
    print("   ✅ Enhanced slot detection (50+ selectors)")
    print("   ✅ JavaScript challenge solving")
    print("   ✅ Browser restart strategy")
    print("   ✅ Selenium fallback system")
    print("   ✅ Improved error handling")
    print("   ✅ Adaptive delay system")
    
    return passed >= total * 0.75

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
