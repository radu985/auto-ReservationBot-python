#!/usr/bin/env python3
"""
Quick setup script to add some free working proxies for immediate testing
"""

import requests
import time
from pathlib import Path

def get_free_proxies():
    """Get some free public proxies for testing"""
    # These are some known free proxy sources (use with caution)
    free_proxies = [
        # HTTP Proxies
        "103.152.112.162:80",
        "45.32.101.24:80", 
        "8.210.83.33:80",
        "47.74.152.29:8888",
        "47.88.3.69:8080",
        "185.162.251.76:80",
        "103.152.112.145:80",
        "45.32.101.24:80",
        "8.210.83.33:80",
        "47.74.152.29:8888",
        "47.88.3.69:8080",
        "185.162.251.76:80",
        "103.152.112.145:80",
        "45.32.101.24:80",
        "8.210.83.33:80",
        "47.74.152.29:8888",
        "47.88.3.69:8080",
        "185.162.251.76:80",
        "103.152.112.145:80",
        "45.32.101.24:80"
    ]
    return free_proxies

def test_proxy_quick(proxy):
    """Quick test for a single proxy"""
    try:
        proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        
        response = requests.get(
            'http://httpbin.org/ip',
            proxies=proxies,
            timeout=5,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        
        if response.status_code == 200:
            return True, response.json().get('origin', 'Unknown')
        return False, None
    except:
        return False, None

def main():
    print("🚀 Setting up free proxies for immediate testing...")
    
    # Get free proxies
    free_proxies = get_free_proxies()
    print(f"Found {len(free_proxies)} free proxies to test...")
    
    # Test proxies quickly
    working_proxies = []
    for i, proxy in enumerate(free_proxies, 1):
        print(f"Testing {i}/{len(free_proxies)}: {proxy}...", end=" ")
        working, ip = test_proxy_quick(proxy)
        
        if working:
            print(f"✅ Working (IP: {ip})")
            working_proxies.append(proxy)
        else:
            print("❌ Failed")
    
    print(f"\n📊 Results: {len(working_proxies)}/{len(free_proxies)} proxies working")
    
    if working_proxies:
        # Update proxies.txt with working free proxies
        proxies_file = Path("proxies.txt")
        
        # Read current content
        with open(proxies_file, 'r') as f:
            content = f.read()
        
        # Add working proxies section
        working_section = f"""
# ========================================
# WORKING FREE PROXIES (Auto-tested)
# ========================================
# These proxies were tested and confirmed working
# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
# Working: {len(working_proxies)}/{len(free_proxies)} tested

"""
        
        for proxy in working_proxies:
            working_section += f"{proxy}\n"
        
        working_section += "\n"
        
        # Insert after the first section
        lines = content.split('\n')
        insert_index = 0
        for i, line in enumerate(lines):
            if line.startswith('# ========================================'):
                insert_index = i
                break
        
        lines.insert(insert_index, working_section)
        
        # Write back
        with open(proxies_file, 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"✅ Added {len(working_proxies)} working proxies to proxies.txt")
        print("🎯 You can now run the VFS automation with these working proxies!")
    else:
        print("❌ No working free proxies found. Consider using paid proxy services.")
        print("💡 Check the proxy recommendations in proxies.txt for premium options.")

if __name__ == "__main__":
    main()
