#!/usr/bin/env python3
"""
System Validation Script for VFS Global Guinea-Bissau Automation
Comprehensive validation of all components and functionality
"""

import sys
import os
import importlib
from pathlib import Path
import subprocess
import json

def validate_python_environment():
    """Validate Python environment and version."""
    print("🐍 Validating Python Environment...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Check virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if in_venv:
        print("✅ Virtual environment detected")
    else:
        print("⚠️  Not in virtual environment (recommended for production)")
    
    return True

def validate_dependencies():
    """Validate all required dependencies are installed."""
    print("\n📦 Validating Dependencies...")
    
    required_packages = {
        "PyQt6": "PyQt6",
        "selenium": "selenium", 
        "playwright": "playwright",
        "cv2": "opencv-python",
        "PIL": "Pillow",
        "numpy": "numpy",
        "requests": "requests",
        "flask": "Flask"
    }
    
    all_installed = True
    for import_name, package_name in required_packages.items():
        try:
            importlib.import_module(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} - Run: pip install {package_name}")
            all_installed = False
    
    return all_installed

def validate_file_structure():
    """Validate required files and directories exist."""
    print("\n📁 Validating File Structure...")
    
    required_files = [
        "app/main.py",
        "app/services/vfs_automation.py",
        "app/services/csv_io.py", 
        "app/services/country_codes.py",
        "mobile_app.py",
        "templates/mobile_index.html",
        "requirements.txt",
        "config.py",
        "start_production.py"
    ]
    
    required_dirs = [
        "app",
        "app/services", 
        "templates",
        "logs",
        "documents",
        "info"
    ]
    
    all_present = True
    
    # Check files
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            all_present = False
    
    # Check directories
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/")
            all_present = False
    
    return all_present

def validate_imports():
    """Validate critical imports work correctly."""
    print("\n🔗 Validating Critical Imports...")
    
    try:
        # Test app imports
        from app.services.vfs_automation import VFSAutomation, VFSBotWorker, AvailabilityStatus, BookingResult
        print("✅ VFS Automation classes")
        
        from app.services.csv_io import ClientRecord, load_clients, save_clients
        print("✅ CSV I/O functions")
        
        from app.services.country_codes import COUNTRY_CALLING_CODES
        print("✅ Country codes")
        
        # Test mobile app imports
        import mobile_app
        print("✅ Mobile app module")
        
        # Test config
        import config
        print("✅ Configuration module")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def validate_csv_functionality():
    """Validate CSV operations work correctly."""
    print("\n📊 Validating CSV Functionality...")
    
    try:
        from app.services.csv_io import ClientRecord, load_clients, save_clients
        
        # Test creating a client record
        test_client = ClientRecord(
            first_name="Test",
            last_name="User", 
            date_of_birth="01/01/1990",
            email="test@example.com",
            password="testpass",
            mobile_country_code="245",
            mobile_number="123456789"
        )
        print("✅ Client record creation")
        
        # Test loading clients (should handle missing file)
        try:
            clients = load_clients("clients.csv")
            print("✅ Load clients (existing file)")
        except FileNotFoundError:
            clients = []
            print("✅ Load clients (new file)")
        
        # Test saving clients
        save_clients("test_clients.csv", [test_client])
        print("✅ Save clients")
        
        # Cleanup test file
        Path("test_clients.csv").unlink(missing_ok=True)
        
        return True
        
    except Exception as e:
        print(f"❌ CSV functionality error: {e}")
        return False

def validate_automation_engine():
    """Validate automation engine can be instantiated."""
    print("\n🤖 Validating Automation Engine...")
    
    try:
        from app.services.vfs_automation import VFSAutomation
        
        # Test environment check
        automation = VFSAutomation(headless=True, use_playwright=True)
        ready, reason = automation.environment_ready()
        
        if ready:
            print("✅ Automation engine ready")
        else:
            print(f"⚠️  Automation engine not ready: {reason}")
            print("   Run: pip install playwright && python -m playwright install")
        
        return True
        
    except Exception as e:
        print(f"❌ Automation engine error: {e}")
        return False

def validate_mobile_app():
    """Validate mobile app can start."""
    print("\n📱 Validating Mobile App...")
    
    try:
        import mobile_app
        
        # Test Flask app creation
        app = mobile_app.app
        print("✅ Flask app creation")
        
        # Test routes exist
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        expected_routes = ['/', '/api/status', '/api/start_bot', '/api/stop_bot', '/api/clients', '/api/save_client', '/api/upload_image', '/api/ping']
        
        for route in expected_routes:
            if route in routes:
                print(f"✅ Route {route}")
            else:
                print(f"❌ Missing route {route}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Mobile app error: {e}")
        return False

def validate_configuration():
    """Validate configuration system."""
    print("\n⚙️  Validating Configuration...")
    
    try:
        import config
        
        # Test config loading
        cfg = config.CONFIG
        print("✅ Configuration loaded")
        
        # Test required config sections
        required_sections = ['vfs', 'browser', 'rate_limiting', 'cloudflare_bypass', 'mobile']
        for section in required_sections:
            if section in cfg:
                print(f"✅ Config section: {section}")
            else:
                print(f"❌ Missing config section: {section}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def validate_directories():
    """Validate required directories are writable."""
    print("\n📂 Validating Directory Permissions...")
    
    directories = ["logs", "documents", "info", "data"]
    
    for directory in directories:
        dir_path = Path(directory)
        try:
            # Create directory if it doesn't exist
            dir_path.mkdir(exist_ok=True)
            
            # Test write permission
            test_file = dir_path / "test_write.tmp"
            test_file.write_text("test")
            test_file.unlink()
            
            print(f"✅ {directory}/ (writable)")
        except Exception as e:
            print(f"❌ {directory}/ (not writable): {e}")
            return False
    
    return True

def run_comprehensive_validation():
    """Run all validation checks."""
    print("🔍 VFS Global Guinea-Bissau Automation - System Validation")
    print("=" * 70)
    
    validations = [
        ("Python Environment", validate_python_environment),
        ("Dependencies", validate_dependencies),
        ("File Structure", validate_file_structure),
        ("Critical Imports", validate_imports),
        ("CSV Functionality", validate_csv_functionality),
        ("Automation Engine", validate_automation_engine),
        ("Mobile App", validate_mobile_app),
        ("Configuration", validate_configuration),
        ("Directory Permissions", validate_directories),
    ]
    
    results = []
    for name, validation_func in validations:
        try:
            result = validation_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} validation failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📋 VALIDATION SUMMARY")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
        if result:
            passed += 1
    
    print(f"\n📊 Results: {passed}/{total} validations passed")
    
    if passed == total:
        print("\n🎉 ALL VALIDATIONS PASSED! System is ready for production.")
        return True
    else:
        print(f"\n⚠️  {total - passed} validation(s) failed. Please fix the issues above.")
        return False

def main():
    """Main validation function."""
    success = run_comprehensive_validation()
    
    if success:
        print("\n🚀 Next Steps:")
        print("1. Run: python start_production.py")
        print("2. Or manually: python -m app.main (desktop) or python mobile_app.py (mobile)")
        print("3. Access mobile app at: http://YOUR_IP:5000")
    else:
        print("\n🔧 Fix the failed validations above before proceeding.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
