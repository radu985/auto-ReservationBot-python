#!/usr/bin/env python3
"""
Proxy Validation Script for VFS Global Automation
Tests all proxies in proxies.txt and provides performance metrics
"""

import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json
from typing import List, Dict, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProxyTester:
    def __init__(self, proxies_file: str = "proxies.txt"):
        self.proxies_file = Path(proxies_file)
        self.test_urls = [
            "http://httpbin.org/ip",
            "https://httpbin.org/ip",
            "https://www.google.com",
            "https://www.cloudflare.com"
        ]
        self.results = []
        
    def load_proxies(self) -> List[Dict]:
        """Load and parse proxies from file"""
        proxies = []
        
        if not self.proxies_file.exists():
            logger.error(f"Proxy file {self.proxies_file} not found!")
            return proxies
            
        with open(self.proxies_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                    
                try:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        proxy = {
                            'line': line_num,
                            'raw': line,
                            'host': parts[0],
                            'port': int(parts[1]),
                            'username': parts[2] if len(parts) > 2 else None,
                            'password': parts[3] if len(parts) > 3 else None
                        }
                        proxies.append(proxy)
                except ValueError as e:
                    logger.warning(f"Invalid proxy format at line {line_num}: {line}")
                    
        return proxies
    
    def test_proxy(self, proxy: Dict) -> Dict:
        """Test a single proxy"""
        result = {
            'proxy': proxy,
            'working': False,
            'response_time': None,
            'error': None,
            'ip': None,
            'success_rate': 0,
            'tested_urls': []
        }
        
        # Build proxy configuration
        proxy_url = f"http://{proxy['host']}:{proxy['port']}"
        
        if proxy['username'] and proxy['password']:
            proxy_url = f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
        
        proxies_config = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        # Test each URL
        successful_tests = 0
        total_response_time = 0
        
        for url in self.test_urls:
            try:
                start_time = time.time()
                response = requests.get(
                    url, 
                    proxies=proxies_config, 
                    timeout=10,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    successful_tests += 1
                    total_response_time += response_time
                    
                    # Extract IP from response
                    if 'httpbin.org/ip' in url:
                        try:
                            ip_data = response.json()
                            result['ip'] = ip_data.get('origin', 'Unknown')
                        except:
                            pass
                    
                    result['tested_urls'].append({
                        'url': url,
                        'status': response.status_code,
                        'response_time': response_time,
                        'success': True
                    })
                else:
                    result['tested_urls'].append({
                        'url': url,
                        'status': response.status_code,
                        'response_time': response_time,
                        'success': False
                    })
                    
            except Exception as e:
                result['tested_urls'].append({
                    'url': url,
                    'status': 'ERROR',
                    'response_time': None,
                    'success': False,
                    'error': str(e)
                })
        
        # Calculate results
        result['success_rate'] = (successful_tests / len(self.test_urls)) * 100
        result['response_time'] = total_response_time / successful_tests if successful_tests > 0 else None
        result['working'] = successful_tests > 0
        
        return result
    
    def test_all_proxies(self, max_workers: int = 10) -> List[Dict]:
        """Test all proxies concurrently"""
        proxies = self.load_proxies()
        
        if not proxies:
            logger.error("No proxies found to test!")
            return []
        
        logger.info(f"Testing {len(proxies)} proxies with {max_workers} workers...")
        
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all proxy tests
            future_to_proxy = {executor.submit(self.test_proxy, proxy): proxy for proxy in proxies}
            
            # Collect results as they complete
            for future in as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result['working']:
                        logger.info(f"✅ {proxy['host']}:{proxy['port']} - {result['success_rate']:.1f}% success, {result['response_time']:.2f}s avg")
                    else:
                        logger.warning(f"❌ {proxy['host']}:{proxy['port']} - Failed")
                        
                except Exception as e:
                    logger.error(f"Error testing {proxy['host']}:{proxy['port']}: {e}")
                    results.append({
                        'proxy': proxy,
                        'working': False,
                        'error': str(e),
                        'success_rate': 0
                    })
        
        self.results = results
        return results
    
    def generate_report(self) -> str:
        """Generate a detailed proxy performance report"""
        if not self.results:
            return "No test results available."
        
        working_proxies = [r for r in self.results if r['working']]
        total_proxies = len(self.results)
        working_count = len(working_proxies)
        
        report = f"""
{'='*80}
PROXY VALIDATION REPORT
{'='*80}

OVERVIEW:
- Total Proxies Tested: {total_proxies}
- Working Proxies: {working_count}
- Success Rate: {(working_count/total_proxies)*100:.1f}%

"""
        
        if working_proxies:
            # Sort by success rate and response time
            working_proxies.sort(key=lambda x: (x['success_rate'], -x['response_time'] or 0), reverse=True)
            
            report += "TOP PERFORMING PROXIES:\n"
            report += "-" * 80 + "\n"
            
            for i, result in enumerate(working_proxies[:10], 1):
                proxy = result['proxy']
                report += f"{i:2d}. {proxy['host']}:{proxy['port']}\n"
                report += f"    Success Rate: {result['success_rate']:.1f}%\n"
                report += f"    Avg Response Time: {result['response_time']:.2f}s\n"
                report += f"    IP: {result['ip'] or 'Unknown'}\n"
                report += f"    Raw: {proxy['raw']}\n"
                report += "\n"
        
        # Failed proxies
        failed_proxies = [r for r in self.results if not r['working']]
        if failed_proxies:
            report += f"\nFAILED PROXIES ({len(failed_proxies)}):\n"
            report += "-" * 80 + "\n"
            
            for result in failed_proxies[:5]:  # Show first 5 failed
                proxy = result['proxy']
                report += f"❌ {proxy['host']}:{proxy['port']} - {result.get('error', 'Unknown error')}\n"
        
        # Recommendations
        report += f"\nRECOMMENDATIONS:\n"
        report += "-" * 80 + "\n"
        
        if working_count == 0:
            report += "🚨 NO WORKING PROXIES FOUND!\n"
            report += "   - Check your proxy credentials\n"
            report += "   - Verify proxy servers are online\n"
            report += "   - Try different proxy providers\n"
        elif working_count < total_proxies * 0.5:
            report += "⚠️  LOW SUCCESS RATE!\n"
            report += "   - Consider upgrading to premium proxy services\n"
            report += "   - Check proxy authentication\n"
            report += "   - Verify proxy server locations\n"
        else:
            report += "✅ GOOD PROXY PERFORMANCE!\n"
            report += "   - Your proxy setup is working well\n"
            report += "   - Consider adding more proxies for redundancy\n"
        
        return report
    
    def save_working_proxies(self, output_file: str = "working_proxies.txt"):
        """Save only working proxies to a new file"""
        working_proxies = [r for r in self.results if r['working']]
        
        if not working_proxies:
            logger.warning("No working proxies to save!")
            return
        
        with open(output_file, 'w') as f:
            f.write("# Working Proxies - Generated by Proxy Tester\n")
            f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total Working: {len(working_proxies)}\n\n")
            
            for result in working_proxies:
                proxy = result['proxy']
                f.write(f"# Success: {result['success_rate']:.1f}%, Response: {result['response_time']:.2f}s\n")
                f.write(f"{proxy['raw']}\n")
        
        logger.info(f"Saved {len(working_proxies)} working proxies to {output_file}")

def main():
    """Main function to run proxy testing"""
    print("🚀 Starting Proxy Validation for VFS Global Automation...")
    print("=" * 80)
    
    tester = ProxyTester()
    
    # Test all proxies
    results = tester.test_all_proxies()
    
    # Generate and display report
    report = tester.generate_report()
    print(report)
    
    # Save working proxies
    tester.save_working_proxies()
    
    # Save detailed results
    with open("proxy_test_results.json", 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📊 Detailed results saved to: proxy_test_results.json")
    print(f"✅ Working proxies saved to: working_proxies.txt")

if __name__ == "__main__":
    main()
