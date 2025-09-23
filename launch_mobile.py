#!/usr/bin/env python3
"""
Mobile App Launcher
Automatically handles virtual environment and launches mobile app
"""

import sys
import os
import subprocess
from pathlib import Path

def check_virtual_environment():
    """Check if we're in a virtual environment"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def activate_virtual_environment():
    """Activate virtual environment if available"""
    venv_python = Path(".venv/Scripts/python.exe")
    if venv_python.exists():
        return str(venv_python)
    
    venv_python = Path(".venv/bin/python")
    if venv_python.exists():
        return str(venv_python)
    
    return None

def main():
    """Launch mobile app with proper environment"""
    print("🚀 VFS Global Mobile App Launcher")
    print("=" * 40)
    
    # Check if we're already in a virtual environment
    if check_virtual_environment():
        print("✅ Virtual environment detected")
        print("🌐 Starting mobile app...")
        try:
            import mobile_app
            mobile_app.app.run(host='0.0.0.0', port=5000, debug=False)
        except Exception as e:
            print(f"❌ Error starting mobile app: {e}")
            return False
    else:
        print("⚠️  No virtual environment detected")
        
        # Try to find and use virtual environment
        venv_python = activate_virtual_environment()
        if venv_python:
            print(f"🔧 Using virtual environment: {venv_python}")
            try:
                subprocess.run([venv_python, "mobile_app.py"], check=True)
            except subprocess.CalledProcessError as e:
                print(f"❌ Error running mobile app: {e}")
                return False
        else:
            print("❌ No virtual environment found")
            print("💡 Please run: python -m venv .venv")
            print("💡 Then: .venv\\Scripts\\activate")
            print("💡 Finally: python mobile_app.py")
            return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
