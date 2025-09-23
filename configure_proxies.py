#!/usr/bin/env python3
"""
Interactive Proxy Configuration Script
Helps you easily configure proxy credentials for VFS Global automation
"""

import os
from pathlib import Path

def get_proxy_provider():
    """Get proxy provider choice from user"""
    print("\n🎯 Choose Your Proxy Provider:")
    print("=" * 50)
    print("1. Bright Data (Luminati) - Premium ($500-2000/month)")
    print("2. Oxylabs - Premium ($300-1500/month)")
    print("3. Smartproxy - Mid-range ($75-400/month)")
    print("4. NetNut - Mid-range ($50-300/month)")
    print("5. ProxyMesh - Budget ($10-50/month)")
    print("6. Storm Proxies - Budget ($15-60/month)")
    print("7. Custom - Enter your own proxy details")
    print("8. Skip - Use current configuration")
    
    while True:
        try:
            choice = int(input("\nEnter your choice (1-8): "))
            if 1 <= choice <= 8:
                return choice
            else:
                print("❌ Please enter a number between 1 and 8")
        except ValueError:
            print("❌ Please enter a valid number")

def get_proxy_credentials():
    """Get proxy credentials from user"""
    print("\n📝 Enter Your Proxy Credentials:")
    print("=" * 40)
    
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    
    if not username or not password:
        print("❌ Username and password are required!")
        return None, None
    
    return username, password

def get_proxy_count():
    """Get number of proxies to configure"""
    while True:
        try:
            count = int(input("\nHow many proxies do you want to configure? (1-10): "))
            if 1 <= count <= 10:
                return count
            else:
                print("❌ Please enter a number between 1 and 10")
        except ValueError:
            print("❌ Please enter a valid number")

def get_custom_proxy():
    """Get custom proxy details"""
    print("\n📝 Enter Custom Proxy Details:")
    print("Format: host:port:username:password")
    print("Example: proxy.example.com:8080:myuser:mypass")
    
    proxy = input("Proxy: ").strip()
    
    if not proxy:
        print("❌ Proxy details are required!")
        return None
    
    parts = proxy.split(':')
    if len(parts) < 2:
        print("❌ Invalid format! Use host:port:username:password")
        return None
    
    return proxy

def update_proxies_file(provider, username, password, count, custom_proxy=None):
    """Update proxies.txt with new configuration"""
    proxies_file = Path("proxies.txt")
    
    if not proxies_file.exists():
        print("❌ proxies.txt file not found!")
        return False
    
    # Read current content
    with open(proxies_file, 'r') as f:
        content = f.read()
    
    # Define proxy configurations
    proxy_configs = {
        1: {  # Bright Data
            'name': 'Bright Data (Luminati)',
            'templates': [
                'brd.superproxy.io:22225:brd-customer-hl_{username}-zone-residential:{password}',
                'brd.superproxy.io:22226:brd-customer-hl_{username}-zone-residential:{password}',
                'brd.superproxy.io:22227:brd-customer-hl_{username}-zone-residential:{password}',
                'brd.superproxy.io:22228:brd-customer-hl_{username}-zone-residential:{password}',
                'brd.superproxy.io:22229:brd-customer-hl_{username}-zone-residential:{password}'
            ]
        },
        2: {  # Oxylabs
            'name': 'Oxylabs',
            'templates': [
                'pr.oxylabs.io:7777:{username}:{password}',
                'pr.oxylabs.io:7778:{username}:{password}',
                'pr.oxylabs.io:7779:{username}:{password}',
                'pr.oxylabs.io:7780:{username}:{password}',
                'pr.oxylabs.io:7781:{username}:{password}'
            ]
        },
        3: {  # Smartproxy
            'name': 'Smartproxy',
            'templates': [
                'gateway.smartproxy.com:7000:{username}:{password}',
                'gateway.smartproxy.com:7001:{username}:{password}',
                'gateway.smartproxy.com:7002:{username}:{password}',
                'gateway.smartproxy.com:7003:{username}:{password}',
                'gateway.smartproxy.com:7004:{username}:{password}'
            ]
        },
        4: {  # NetNut
            'name': 'NetNut',
            'templates': [
                'gateway.netnut.io:5959:{username}:{password}',
                'gateway.netnut.io:5960:{username}:{password}',
                'gateway.netnut.io:5961:{username}:{password}',
                'gateway.netnut.io:5962:{username}:{password}',
                'gateway.netnut.io:5963:{username}:{password}'
            ]
        },
        5: {  # ProxyMesh
            'name': 'ProxyMesh',
            'templates': [
                'us-wa.proxymesh.com:31280:{username}:{password}',
                'us-ca.proxymesh.com:31280:{username}:{password}',
                'us-ny.proxymesh.com:31280:{username}:{password}',
                'us-tx.proxymesh.com:31280:{username}:{password}',
                'us-fl.proxymesh.com:31280:{username}:{password}'
            ]
        },
        6: {  # Storm Proxies
            'name': 'Storm Proxies',
            'templates': [
                'us.stormproxies.com:9000:{username}:{password}',
                'us.stormproxies.com:9001:{username}:{password}',
                'us.stormproxies.com:9002:{username}:{password}',
                'us.stormproxies.com:9003:{username}:{password}',
                'us.stormproxies.com:9004:{username}:{password}'
            ]
        }
    }
    
    # Generate proxy entries
    if provider == 7:  # Custom
        proxy_entries = [custom_proxy] * count
        provider_name = "Custom"
    else:
        config = proxy_configs[provider]
        provider_name = config['name']
        proxy_entries = []
        
        for i in range(count):
            template = config['templates'][i % len(config['templates'])]
            proxy_entry = template.format(username=username, password=password)
            proxy_entries.append(proxy_entry)
    
    # Create new section
    new_section = f"""
# ========================================
# CONFIGURED PROXIES - {provider_name}
# ========================================
# Configured: {username}
# Count: {count} proxies
# Status: Ready for testing

"""
    
    for proxy in proxy_entries:
        new_section += f"{proxy}\n"
    
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
    
    # Write back to file
    with open(proxies_file, 'w') as f:
        f.write('\n'.join(lines))
    
    return True

def main():
    """Main configuration function"""
    print("🚀 VFS Global Proxy Configuration")
    print("=" * 50)
    print("This script will help you configure proxy credentials")
    print("for the VFS Global automation system.")
    
    # Get provider choice
    provider = get_proxy_provider()
    
    if provider == 8:  # Skip
        print("✅ Skipping configuration. Using current setup.")
        return
    
    # Get credentials
    if provider == 7:  # Custom
        custom_proxy = get_custom_proxy()
        if not custom_proxy:
            return
        username, password = "custom", "custom"
        count = 1
    else:
        username, password = get_proxy_credentials()
        if not username or not password:
            return
        count = get_proxy_count()
    
    # Update proxies file
    print(f"\n🔄 Updating proxies.txt with {count} proxy(ies)...")
    
    if update_proxies_file(provider, username, password, count, custom_proxy if provider == 7 else None):
        print("✅ Successfully updated proxies.txt!")
        print(f"📊 Added {count} proxy(ies) for testing")
        
        print("\n🎯 Next Steps:")
        print("1. Test your proxies: python test_proxy_validation.py")
        print("2. Run VFS automation: python -m app.main")
        print("3. Monitor success rates in the logs")
        
    else:
        print("❌ Failed to update proxies.txt")

if __name__ == "__main__":
    main()
