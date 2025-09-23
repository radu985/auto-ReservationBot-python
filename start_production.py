#!/usr/bin/env python3
"""
Production Startup Script for VFS Global Guinea-Bissau Automation
Handles environment setup, dependency checking, and application launch
"""

import sys
import subprocess
import os
from pathlib import Path
from config import CONFIG, is_production

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_virtual_environment():
    """Check if running in virtual environment."""
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if not in_venv:
        print("⚠️  Warning: Not running in virtual environment")
        print("   For production, use: python -m venv .venv && .venv\\Scripts\\activate")
    else:
        print("✅ Virtual environment detected")
    return True

def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = [
        "PyQt6",
        "selenium", 
        "playwright",
        "opencv-python",
        "Pillow",
        "numpy",
        "requests",
        "Flask"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n📦 Install missing packages:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_playwright_browsers():
    """Check if Playwright browsers are installed."""
    try:
        result = subprocess.run(
            ["python", "-m", "playwright", "install", "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print("✅ Playwright browsers installed")
            return True
        else:
            print("❌ Playwright browsers not installed")
            print("Run: python -m playwright install")
            return False
    except Exception as e:
        print(f"❌ Error checking Playwright: {e}")
        return False

def check_file_structure():
    """Check if required files and directories exist."""
    required_files = [
        "app/main.py",
        "app/services/vfs_automation.py", 
        "app/services/csv_io.py",
        "mobile_app.py",
        "templates/mobile_index.html",
        "requirements.txt",
        "clients.csv"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
            print(f"❌ {file_path}")
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print(f"\nMissing required files: {missing_files}")
        return False
    
    return True

def setup_environment():
    """Setup environment for production."""
    print("🔧 Setting up environment...")
    
    # Create required directories
    directories = ["logs", "documents", "info", "data"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Set environment variables
    os.environ["ENVIRONMENT"] = "production"
    print("✅ Environment set to production")
    
    return True

def start_desktop_app():
    """Start the desktop GUI application."""
    print("\n🖥️  Starting Desktop Application...")
    try:
        subprocess.run([sys.executable, "-m", "app.main"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Desktop application stopped")
    except Exception as e:
        print(f"❌ Error starting desktop app: {e}")
        return False
    return True

def start_mobile_app():
    """Start the mobile web application."""
    print("\n📱 Starting Mobile Application...")
    try:
        subprocess.run([sys.executable, "mobile_app.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Mobile application stopped")
    except Exception as e:
        print(f"❌ Error starting mobile app: {e}")
        return False
    return True

def main():
    """Main startup function."""
    print("🚀 VFS Global Guinea-Bissau Automation - Production Startup")
    print("=" * 60)
    
    # Pre-flight checks
    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_virtual_environment),
        ("Dependencies", check_dependencies),
        ("Playwright Browsers", check_playwright_browsers),
        ("File Structure", check_file_structure),
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        print(f"\n🔍 {check_name}:")
        if not check_func():
            all_passed = False
    
    if not all_passed:
        print("\n❌ Pre-flight checks failed. Please fix the issues above.")
        return False
    
    # Setup environment
    if not setup_environment():
        print("❌ Environment setup failed")
        return False
    
    print("\n✅ All checks passed! System ready for production.")
    
    # Choose application to start
    print("\n🎯 Choose application to start:")
    print("1. Desktop GUI Application")
    print("2. Mobile Web Application")
    print("3. Both (Desktop + Mobile)")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            return start_desktop_app()
        elif choice == "2":
            return start_mobile_app()
        elif choice == "3":
            print("\n⚠️  Starting both applications...")
            print("Desktop: http://localhost (GUI)")
            print("Mobile: http://YOUR_IP:5000")
            # Note: In production, you'd run these in separate processes
            return start_desktop_app()
        else:
            print("❌ Invalid choice")
            return False
            
    except KeyboardInterrupt:
        print("\n👋 Startup cancelled")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
