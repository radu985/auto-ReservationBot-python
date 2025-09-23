#!/usr/bin/env python3
"""
Mobile Environment Setup Script
Ensures all dependencies are installed for mobile app functionality
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def main():
    """Main setup function."""
    print("🚀 Setting up VFS Global Mobile App Environment")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Not running in a virtual environment")
        print("   Consider creating one with: python -m venv .venv")
        print("   Then activate it before running this script")
        print()
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        return False
    
    # Install Playwright browsers
    if not run_command("python -m playwright install", "Installing Playwright browsers"):
        return False
    
    # Test imports
    print("🧪 Testing imports...")
    try:
        import PyQt6
        print("✅ PyQt6 imported successfully")
    except ImportError:
        print("❌ PyQt6 import failed")
        return False
    
    try:
        import playwright
        print("✅ Playwright imported successfully")
    except ImportError:
        print("❌ Playwright import failed")
        return False
    
    try:
        import selenium
        print("✅ Selenium imported successfully")
    except ImportError:
        print("❌ Selenium import failed")
        return False
    
    # Test automation worker import
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from app.services.vfs_automation import VFSBotWorker
        print("✅ VFSBotWorker imported successfully")
    except ImportError as e:
        print(f"❌ VFSBotWorker import failed: {e}")
        return False
    
    print("\n🎉 Setup completed successfully!")
    print("\n📱 To start the mobile app:")
    print("   1. Activate virtual environment: .\\.venv\\Scripts\\activate")
    print("   2. Run mobile app: python mobile_app.py")
    print("   3. Open on phone: http://YOUR_COMPUTER_IP:5000")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
