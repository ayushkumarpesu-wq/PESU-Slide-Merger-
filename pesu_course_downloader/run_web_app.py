#!/usr/bin/env python3
"""
Quick Start Script for PESU Web Downloader
This script initializes the web app and opens it in your browser
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed"""
    required = ['flask', 'flask_cors']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print("\nInstalling missing packages...")
        for package in missing:
            pip_name = package.replace('_', '-')
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', pip_name])
        print("✓ Packages installed successfully!\n")

def check_env_file():
    """Check if .env file exists with credentials"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("⚠️  .env file not found!")
        print("\nPlease create a .env file with your PESU Academy credentials:")
        print("─" * 50)
        print("PESU_SRN=your_srn_number")
        print("PESU_PASSWORD=your_password")
        print("─" * 50)
        
        create = input("\nCreate .env file now? (y/n): ").lower() == 'y'
        if create:
            srn = input("Enter your PESU Academy SRN: ")
            password = input("Enter your PESU Academy password: ")
            with open('.env', 'w') as f:
                f.write(f"PESU_SRN={srn}\n")
                f.write(f"PESU_PASSWORD={password}\n")
            print("✓ .env file created!\n")
        else:
            print("⚠️  Cannot proceed without .env file\n")
            return False
    
    return True

def main():
    print("┌" + "─" * 58 + "┐")
    print("│" + " PESU Academy Course Downloader - Web Edition ".center(58) + "│")
    print("└" + "─" * 58 + "┘\n")
    
    # Check dependencies
    print("📦 Checking dependencies...")
    check_dependencies()
    
    # Check .env file
    print("🔐 Checking credentials...")
    if not check_env_file():
        sys.exit(1)
    
    # Create necessary directories
    print("📁 Creating directories...")
    Path('downloads').mkdir(exist_ok=True)
    Path('templates').mkdir(exist_ok=True)
    Path('static').mkdir(exist_ok=True)
    print("✓ Directories ready!\n")
    
    # Start Flask app
    print("🚀 Starting Flask server...\n")
    print("─" * 60)
    print("Server will be available at: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("─" * 60 + "\n")
    
    time.sleep(2)
    
    # Open browser
    print("🌐 Opening browser...")
    webbrowser.open('http://localhost:5000')
    
    # Run Flask app
    try:
        subprocess.run([sys.executable, 'web_app.py'])
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Thank you for using PESU Downloader!")

if __name__ == '__main__':
    main()
