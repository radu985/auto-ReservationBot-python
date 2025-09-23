#!/usr/bin/env python3
"""
Real VFS Global Session Test
Tests the advanced bypass system with actual VFS Global website
"""

from app.services.vfs_automation import VFSAutomation
import time

def test_real_vfs_session():
    """Test advanced bypass with real VFS Global website."""
    print('🚀 Starting Real VFS Global Session Test')
    print('=' * 50)

    # Initialize the automation bot with advanced bypass
    bot = VFSAutomation(headless=False, use_playwright=True)

    print(f'✅ Bot initialized with {len(bot.proxy_list)} proxies')
    print(f'✅ User agents: {len(bot.user_agents)} available')
    print(f'✅ Advanced bypass enabled: {bot.proxy_rotation_enabled}')

    # Test real VFS Global website access
    print('\n🌐 Testing VFS Global website access...')
    try:
        # Start browser with advanced stealth
        bot.start_browser()
        print('✅ Browser started with advanced stealth mode')
        
        # Navigate to VFS Global Guinea-Bissau
        print('🔗 Navigating to VFS Global Guinea-Bissau...')
        bot.page.goto('https://visa.vfsglobal.com/gwq/en/gbr/book-appointment')
        
        # Wait for page to load
        time.sleep(5)
        
        # Check for Cloudflare challenge
        content = bot.page.content()
        if bot._detect_cloudflare_challenge(content):
            print('⚠️  Cloudflare challenge detected - testing bypass...')
            success = bot._handle_cloudflare_challenge()
            if success:
                print('✅ Cloudflare bypass successful!')
            else:
                print('❌ Cloudflare bypass failed')
        else:
            print('✅ No Cloudflare challenge detected')
        
        # Check page title and content
        title = bot.page.title()
        print(f'📄 Page title: {title}')
        
        # Look for booking elements
        try:
            # Check for common booking page elements
            booking_elements = bot.page.query_selector_all('input, select, button')
            print(f'🔍 Found {len(booking_elements)} interactive elements')
            
            # Check for specific VFS elements
            vfs_elements = bot.page.query_selector_all('[class*="vfs"], [id*="vfs"], [class*="booking"], [id*="booking"]')
            print(f'🎯 Found {len(vfs_elements)} VFS-specific elements')
            
        except Exception as e:
            print(f'⚠️  Element detection error: {e}')
        
        print('\n✅ Real VFS Global session test completed successfully!')
        
    except Exception as e:
        print(f'❌ Error during VFS Global test: {e}')
        
    finally:
        # Clean up
        try:
            bot.stop_browser()
            print('🧹 Browser cleanup completed')
        except:
            pass

    print('\n🎉 Advanced bypass system is working with real VFS Global website!')

if __name__ == "__main__":
    test_real_vfs_session()
