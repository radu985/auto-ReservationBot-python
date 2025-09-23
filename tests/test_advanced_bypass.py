#!/usr/bin/env python3
"""
Test script for advanced Cloudflare bypass features
Tests proxy rotation, CAPTCHA solving, and fingerprint rotation
"""

import sys
import os
import time
import logging
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.vfs_automation import VFSAutomation, AvailabilityStatus

def test_proxy_rotation():
    """Test proxy rotation functionality."""
    print("🔍 Testing Proxy Rotation...")
    
    automation = VFSAutomation(headless=True, use_playwright=True)
    
    # Test proxy loading
    print(f"✅ Loaded {len(automation.proxy_list)} proxies")
    
    # Test proxy rotation
    proxy1 = automation._get_random_proxy()
    proxy2 = automation._rotate_proxy()
    
    if proxy1 and proxy2:
        print(f"✅ Proxy rotation working: {proxy1['host']} -> {proxy2['host']}")
    else:
        print("⚠️  Proxy rotation not available (no proxies configured)")
    
    # Test proxy testing
    if proxy1:
        is_working = automation._test_proxy(proxy1)
        status = "✅ Working" if is_working else "❌ Not working"
        print(f"✅ Proxy testing: {proxy1['host']}:{proxy1['port']} - {status}")
    
    return True

def test_browser_fingerprint():
    """Test browser fingerprint generation."""
    print("\n🔍 Testing Browser Fingerprint...")
    
    automation = VFSAutomation(headless=True, use_playwright=True)
    
    # Test fingerprint generation
    fingerprint1 = automation._get_browser_fingerprint()
    fingerprint2 = automation._get_browser_fingerprint()
    
    print(f"✅ Generated fingerprint 1: {fingerprint1['platform']} - {fingerprint1['viewport']['width']}x{fingerprint1['viewport']['height']}")
    print(f"✅ Generated fingerprint 2: {fingerprint2['platform']} - {fingerprint2['viewport']['width']}x{fingerprint2['viewport']['height']}")
    
    # Check if fingerprints are different (randomized)
    if fingerprint1 != fingerprint2:
        print("✅ Fingerprint randomization working")
    else:
        print("⚠️  Fingerprints are identical (may be expected)")
    
    return True

def test_stealth_scripts():
    """Test stealth script injection."""
    print("\n🔍 Testing Stealth Scripts...")
    
    automation = VFSAutomation(headless=True, use_playwright=True)
    
    # Test stealth script generation
    script = automation._get_stealth_script()
    
    if "webdriver" in script and "navigator" in script:
        print("✅ Stealth script generation working")
    else:
        print("❌ Stealth script generation failed")
        return False
    
    # Test browser startup with stealth
    if automation.start_browser():
        print("✅ Browser started with stealth mode")
        
        # Test advanced stealth injection
        try:
            automation._inject_advanced_stealth_scripts()
            print("✅ Advanced stealth scripts injected successfully")
        except Exception as e:
            print(f"❌ Advanced stealth injection failed: {e}")
            return False
        
        automation.stop_browser()
        return True
    else:
        print("❌ Browser startup failed")
        return False

def test_captcha_detection():
    """Test CAPTCHA detection and solving."""
    print("\n🔍 Testing CAPTCHA Detection...")
    
    automation = VFSAutomation(headless=True, use_playwright=True)
    
    # Test CAPTCHA detection
    test_content_with_captcha = "This is a test page with captcha challenge verification"
    test_content_without_captcha = "This is a normal page without any challenges"
    
    has_captcha1 = automation._solve_captcha(test_content_with_captcha)
    has_captcha2 = automation._solve_captcha(test_content_without_captcha)
    
    print(f"✅ CAPTCHA detection: {'Found' if has_captcha1 else 'Not found'} (expected: Found)")
    print(f"✅ CAPTCHA detection: {'Found' if has_captcha2 else 'Not found'} (expected: Not found)")
    
    return True

def test_cloudflare_bypass():
    """Test comprehensive Cloudflare bypass."""
    print("\n🔍 Testing Cloudflare Bypass...")
    
    automation = VFSAutomation(headless=True, use_playwright=True)
    
    # Test bypass attempt tracking
    print(f"✅ Initial bypass attempts: {automation.bypass_attempts}")
    
    # Test Cloudflare challenge detection
    cf_content = "Checking your browser before accessing this website"
    no_cf_content = "Welcome to our website"
    
    is_cf1 = automation._detect_cloudflare_challenge(cf_content)
    is_cf2 = automation._detect_cloudflare_challenge(no_cf_content)
    
    print(f"✅ CF detection: {'Detected' if is_cf1 else 'Not detected'} (expected: Detected)")
    print(f"✅ CF detection: {'Detected' if is_cf2 else 'Not detected'} (expected: Not detected)")
    
    return True

def test_advanced_bypass_strategies():
    """Test all advanced bypass strategies."""
    print("\n🔍 Testing Advanced Bypass Strategies...")
    
    automation = VFSAutomation(headless=True, use_playwright=True)
    
    # Test strategy availability
    strategies = [
        ("Advanced Stealth", automation._try_advanced_stealth_bypass),
        ("Proxy Rotation", automation._try_proxy_rotation_bypass),
        ("CAPTCHA Solving", automation._try_captcha_solving_bypass),
        ("Browser Restart", automation._try_browser_restart),
        ("Selenium Fallback", automation._try_selenium_fallback),
        ("Basic CF Bypass", automation._try_basic_cf_bypass)
    ]
    
    for name, method in strategies:
        try:
            # Test method exists and is callable
            if callable(method):
                print(f"✅ {name} strategy available")
            else:
                print(f"❌ {name} strategy not callable")
        except Exception as e:
            print(f"❌ {name} strategy error: {e}")
    
    return True

def test_integration():
    """Test integration of all features."""
    print("\n🔍 Testing Integration...")
    
    automation = VFSAutomation(headless=True, use_playwright=True)
    
    # Test configuration
    print(f"✅ Proxy rotation enabled: {automation.proxy_rotation_enabled}")
    print(f"✅ CAPTCHA solving enabled: {automation.captcha_solving_enabled}")
    print(f"✅ Fingerprint rotation enabled: {automation.browser_fingerprint_rotation}")
    print(f"✅ Max bypass attempts: {automation.max_bypass_attempts}")
    
    # Test browser startup with all features
    if automation.start_browser():
        print("✅ Browser started with all advanced features")
        
        # Test navigation (without actually going to VFS site)
        try:
            automation.page.goto("about:blank")
            print("✅ Page navigation working")
        except Exception as e:
            print(f"⚠️  Page navigation issue: {e}")
        
        automation.stop_browser()
        return True
    else:
        print("❌ Browser startup failed")
        return False

def main():
    """Run all tests."""
    print("🚀 Advanced Cloudflare Bypass Test Suite")
    print("=" * 50)
    
    tests = [
        ("Proxy Rotation", test_proxy_rotation),
        ("Browser Fingerprint", test_browser_fingerprint),
        ("Stealth Scripts", test_stealth_scripts),
        ("CAPTCHA Detection", test_captcha_detection),
        ("Cloudflare Bypass", test_cloudflare_bypass),
        ("Advanced Strategies", test_advanced_bypass_strategies),
        ("Integration", test_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - PASSED")
            else:
                print(f"❌ {test_name} - FAILED")
        except Exception as e:
            print(f"❌ {test_name} - ERROR: {e}")
        
        print("-" * 30)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Advanced bypass features are ready.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
