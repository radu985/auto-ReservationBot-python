#!/usr/bin/env python3
"""
Setup script for VFS Global Mobile App
This script helps you get the mobile app running on your phone
"""

import socket
import subprocess
import sys
import os
from pathlib import Path

def get_local_ip():
    """Get the local IP address of this computer."""
    try:
        # Connect to a remote server to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    required_packages = ['flask', 'pillow']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
            print("✅ All packages installed successfully!")
        except subprocess.CalledProcessError:
            print("❌ Failed to install packages. Please install manually:")
            print(f"pip install {' '.join(missing_packages)}")
            return False
    
    return True

def create_directories():
    """Create necessary directories."""
    print("📁 Creating directories...")
    
    directories = ['templates', 'static', 'info', 'documents']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ {directory}/")

def show_instructions():
    """Show instructions for accessing the mobile app."""
    local_ip = get_local_ip()
    
    print("\n" + "="*60)
    print("🚀 VFS Global Mobile App Setup Complete!")
    print("="*60)
    print(f"📱 Your computer's IP address: {local_ip}")
    print(f"🌐 Mobile app URL: http://{local_ip}:5000")
    print("\n📋 Instructions:")
    print("1. Make sure your phone is connected to the SAME WiFi network as this computer")
    print("2. Open your phone's web browser (Chrome, Safari, etc.)")
    print(f"3. Go to: http://{local_ip}:5000")
    print("4. The mobile app will load and you can start using it!")
    print("\n💡 Tips:")
    print("- Keep this computer running while using the mobile app")
    print("- The app works best on phones with modern browsers")
    print("- You can bookmark the URL for easy access")
    print("- The app will automatically update in real-time")
    print("\n🔧 Troubleshooting:")
    print("- If the app doesn't load, check your firewall settings")
    print("- Make sure both devices are on the same WiFi network")
    print("- Try restarting the app if you encounter issues")
    print("\n🎯 Features available on mobile:")
    print("- Start/stop the VFS automation bot")
    print("- Monitor availability in real-time")
    print("- Add and manage client data")
    print("- Upload passport photos")
    print("- View booking results and status")
    print("="*60)

def main():
    """Main setup function."""
    print("🇬🇼 VFS Global Mobile App Setup")
    print("="*40)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Setup failed due to missing dependencies")
        return False
    
    # Create directories
    create_directories()
    
    # Show instructions
    show_instructions()
    
    # Ask if user wants to start the app
    print("\n🚀 Ready to start the mobile app?")
    response = input("Type 'yes' to start the app now: ").lower().strip()
    
    if response in ['yes', 'y']:
        print("\n🌐 Starting mobile app...")
        print("Press Ctrl+C to stop the app")
        print("-" * 40)
        
        try:
            # Start the mobile app
            subprocess.run([sys.executable, 'mobile_app.py'])
        except KeyboardInterrupt:
            print("\n👋 Mobile app stopped. Goodbye!")
        except Exception as e:
            print(f"\n❌ Error starting app: {e}")
    else:
        print("\n📝 To start the app later, run:")
        print("python mobile_app.py")
    
    return True

if __name__ == "__main__":
    main()
