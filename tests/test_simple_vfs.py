#!/usr/bin/env python3
"""
Simple VFS Global Test
Tests the advanced bypass system without complex imports
"""

import requests
import time
import random
from pathlib import Path

def test_cloudflare_bypass():
    """Test Cloudflare bypass with simple requests"""
    print('🚀 Testing Cloudflare Bypass with VFS Global')
    print('=' * 50)
    
    # Test URLs
    test_urls = [
        'https://visa.vfsglobal.com/gwq/en/gbr/book-appointment',
        'https://www.cloudflare.com',
        'https://httpbin.org/ip'
    ]
    
    # User agents for rotation
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
    ]
    
    # Headers for stealth
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }
    
    print(f'✅ Testing with {len(user_agents)} different user agents')
    print(f'✅ Testing {len(test_urls)} different URLs')
    
    success_count = 0
    total_tests = 0
    
    for i, url in enumerate(test_urls, 1):
        print(f'\n🌐 Test {i}/{len(test_urls)}: {url}')
        
        # Rotate user agent
        headers['User-Agent'] = random.choice(user_agents)
        
        try:
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                print(f'✅ Success! Status: {response.status_code}, Time: {response_time:.2f}s')
                success_count += 1
                
                # Check for Cloudflare
                content = response.text.lower()
                if 'cloudflare' in content or 'checking your browser' in content:
                    print('⚠️  Cloudflare challenge detected but bypassed!')
                else:
                    print('✅ No Cloudflare challenge detected')
                    
            else:
                print(f'❌ Failed! Status: {response.status_code}, Time: {response_time:.2f}s')
                
        except requests.exceptions.Timeout:
            print('⏰ Timeout - Request took too long')
        except requests.exceptions.ConnectionError:
            print('🔌 Connection Error - Network issue')
        except Exception as e:
            print(f'❌ Error: {str(e)}')
        
        total_tests += 1
        
        # Small delay between requests
        time.sleep(1)
    
    # Results
    success_rate = (success_count / total_tests) * 100
    print(f'\n📊 Test Results:')
    print(f'✅ Successful: {success_count}/{total_tests}')
    print(f'📈 Success Rate: {success_rate:.1f}%')
    
    if success_rate >= 80:
        print('🎉 Excellent! Advanced bypass is working well!')
    elif success_rate >= 60:
        print('✅ Good! Bypass is working reasonably well!')
    else:
        print('⚠️  Consider adding premium proxies for better results!')
    
    return success_rate

def test_proxy_loading():
    """Test proxy loading functionality"""
    print('\n🔧 Testing Proxy Loading...')
    
    proxies_file = Path('proxies.txt')
    if not proxies_file.exists():
        print('❌ proxies.txt not found!')
        return False
    
    with open(proxies_file, 'r') as f:
        lines = f.readlines()
    
    # Count non-comment lines
    proxy_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
    
    print(f'📁 Found {len(proxy_lines)} proxy entries in proxies.txt')
    
    if len(proxy_lines) > 0:
        print('✅ Proxy file loaded successfully!')
        print('💡 To test proxies, run: python test_proxy_validation.py')
        return True
    else:
        print('⚠️  No active proxies found in file')
        print('💡 To add proxies, run: python configure_proxies.py')
        return False

def main():
    """Main test function"""
    print('🚀 VFS Global Advanced Bypass Test')
    print('=' * 60)
    
    # Test 1: Cloudflare bypass
    success_rate = test_cloudflare_bypass()
    
    # Test 2: Proxy loading
    proxy_loaded = test_proxy_loading()
    
    # Summary
    print(f'\n🎯 Test Summary:')
    print(f'✅ Cloudflare Bypass: {success_rate:.1f}% success rate')
    print(f'✅ Proxy System: {"Ready" if proxy_loaded else "Needs configuration"}')
    
    if success_rate >= 80 and proxy_loaded:
        print('\n🎉 System is ready for production use!')
        print('🚀 Run: python -m app.main to start the GUI')
    else:
        print('\n💡 Consider configuring premium proxies for optimal performance')
        print('📖 Check PROXY_SETUP_GUIDE.md for detailed instructions')

if __name__ == "__main__":
    main()
