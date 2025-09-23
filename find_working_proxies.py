#!/usr/bin/env python3
"""
Find Working Proxies Script
Automatically discovers and tests working proxies for VFS Global automation
"""

import requests
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json

class ProxyFinder:
    def __init__(self):
        self.working_proxies = []
        self.test_urls = [
            'http://httpbin.org/ip',
            'https://httpbin.org/ip',
            'https://www.google.com',
            'https://www.cloudflare.com'
        ]
        
    def get_free_proxy_sources(self):
        """Get proxies from various free sources"""
        proxy_sources = [
            # Proxy lists from various sources
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
            'https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt',
            'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt',
            'https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt',
            'https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTP_RAW.txt'
        ]
        
        all_proxies = []
        
        for source in proxy_sources:
            try:
                print(f"Fetching proxies from: {source}")
                response = requests.get(source, timeout=10)
                if response.status_code == 200:
                    proxies = response.text.strip().split('\n')
                    # Clean and validate proxy format
                    for proxy in proxies:
                        proxy = proxy.strip()
                        if ':' in proxy and len(proxy.split(':')) >= 2:
                            all_proxies.append(proxy)
                    print(f"Found {len(proxies)} proxies from {source}")
            except Exception as e:
                print(f"Failed to fetch from {source}: {e}")
        
        return list(set(all_proxies))  # Remove duplicates
    
    def test_proxy(self, proxy):
        """Test a single proxy"""
        try:
            # Parse proxy
            if ':' in proxy:
                parts = proxy.split(':')
                host = parts[0]
                port = int(parts[1])
            else:
                return None
                
            proxy_url = f"http://{host}:{port}"
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            # Test with multiple URLs
            success_count = 0
            total_time = 0
            
            for url in self.test_urls:
                try:
                    start_time = time.time()
                    response = requests.get(
                        url,
                        proxies=proxies,
                        timeout=5,
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                    )
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        success_count += 1
                        total_time += response_time
                        
                except Exception as e:
                    continue
            
            if success_count > 0:
                avg_time = total_time / success_count
                success_rate = (success_count / len(self.test_urls)) * 100
                
                return {
                    'proxy': proxy,
                    'host': host,
                    'port': port,
                    'success_rate': success_rate,
                    'avg_time': avg_time,
                    'working': True
                }
            
        except Exception as e:
            pass
        
        return None
    
    def find_working_proxies(self, max_workers=20, max_proxies=50):
        """Find working proxies using multiple sources"""
        print("🔍 Searching for working proxies...")
        
        # Get proxies from various sources
        all_proxies = self.get_free_proxy_sources()
        print(f"📊 Total proxies found: {len(all_proxies)}")
        
        if not all_proxies:
            print("❌ No proxies found from sources")
            return []
        
        # Test proxies concurrently
        working_proxies = []
        tested_count = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all proxy tests
            future_to_proxy = {
                executor.submit(self.test_proxy, proxy): proxy 
                for proxy in all_proxies[:max_proxies]
            }
            
            # Collect results
            for future in as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                tested_count += 1
                
                try:
                    result = future.result()
                    if result and result['working']:
                        working_proxies.append(result)
                        print(f"✅ {proxy} - {result['success_rate']:.1f}% success, {result['avg_time']:.2f}s avg")
                    else:
                        print(f"❌ {proxy} - Failed")
                        
                except Exception as e:
                    print(f"❌ {proxy} - Error: {e}")
                
                # Progress update
                if tested_count % 10 == 0:
                    print(f"📈 Progress: {tested_count}/{min(len(all_proxies), max_proxies)} tested, {len(working_proxies)} working")
        
        # Sort by success rate and speed
        working_proxies.sort(key=lambda x: (x['success_rate'], -x['avg_time']), reverse=True)
        
        print(f"\n🎉 Found {len(working_proxies)} working proxies!")
        return working_proxies
    
    def save_working_proxies(self, working_proxies, filename="working_proxies.txt"):
        """Save working proxies to file"""
        if not working_proxies:
            print("❌ No working proxies to save")
            return
        
        with open(filename, 'w') as f:
            f.write("# Working Proxies - Auto-discovered\n")
            f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total Working: {len(working_proxies)}\n\n")
            
            for proxy_data in working_proxies:
                f.write(f"# Success: {proxy_data['success_rate']:.1f}%, Avg Time: {proxy_data['avg_time']:.2f}s\n")
                f.write(f"{proxy_data['proxy']}\n")
        
        print(f"💾 Saved {len(working_proxies)} working proxies to {filename}")
    
    def update_proxies_txt(self, working_proxies):
        """Update the main proxies.txt file with working proxies"""
        proxies_file = Path("proxies.txt")
        
        if not proxies_file.exists():
            print("❌ proxies.txt not found")
            return
        
        # Read current content
        with open(proxies_file, 'r') as f:
            content = f.read()
        
        # Create new working proxies section
        new_section = f"""
# ========================================
# AUTO-DISCOVERED WORKING PROXIES
# ========================================
# These proxies were automatically discovered and tested
# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
# Total Working: {len(working_proxies)}
# Status: Ready for production use

"""
        
        for proxy_data in working_proxies[:20]:  # Top 20 proxies
            new_section += f"# Success: {proxy_data['success_rate']:.1f}%, Time: {proxy_data['avg_time']:.2f}s\n"
            new_section += f"{proxy_data['proxy']}\n"
        
        new_section += "\n"
        
        # Find insertion point (after first section)
        lines = content.split('\n')
        insert_index = 0
        
        for i, line in enumerate(lines):
            if line.startswith('# ========================================'):
                insert_index = i
                break
        
        # Insert new section
        lines.insert(insert_index, new_section)
        
        # Write back
        with open(proxies_file, 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"✅ Updated proxies.txt with {len(working_proxies)} working proxies")

def main():
    """Main function"""
    print("🚀 VFS Global Proxy Discovery Tool")
    print("=" * 50)
    
    finder = ProxyFinder()
    
    # Find working proxies
    working_proxies = finder.find_working_proxies(max_workers=15, max_proxies=100)
    
    if working_proxies:
        # Save to separate file
        finder.save_working_proxies(working_proxies)
        
        # Update main proxies.txt
        finder.update_proxies_txt(working_proxies)
        
        # Show top 10
        print(f"\n🏆 Top 10 Working Proxies:")
        print("-" * 50)
        for i, proxy_data in enumerate(working_proxies[:10], 1):
            print(f"{i:2d}. {proxy_data['proxy']} - {proxy_data['success_rate']:.1f}% success, {proxy_data['avg_time']:.2f}s")
        
        print(f"\n🎯 Ready to use! Run: python -m app.main")
    else:
        print("❌ No working proxies found")
        print("💡 Consider using premium proxy services")
        print("📖 Check PROXY_SETUP_GUIDE.md for premium options")

if __name__ == "__main__":
    main()
