#!/usr/bin/env python3
"""
PESU Web Downloader - Quick Setup Guide
Run this file to set everything up and start the web app
"""

import subprocess
import sys
import os
from pathlib import Path

def print_header(text):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_section(text):
    """Print a formatted section"""
    print(f"\n>>> {text}")

def main():
    print_header("PESU ACADEMY COURSE DOWNLOADER - SETUP")
    
    # Step 1: Check Python version
    print_section("Step 1: Checking Python version")
    version = sys.version_info
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    
    if version < (3, 8):
        print("❌ Python 3.8+ is required!")
        sys.exit(1)
    
    # Step 2: Install dependencies
    print_section("Step 2: Installing/updating dependencies")
    requirements_file = Path('requirements.txt')
    
    if requirements_file.exists():
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', 
                '-r', str(requirements_file), '--quiet'
            ])
            print("✓ All dependencies installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing dependencies: {e}")
            sys.exit(1)
    else:
        print("❌ requirements.txt not found!")
        sys.exit(1)
    
    # Step 3: Create necessary directories
    print_section("Step 3: Setting up directories")
    for directory in ['downloads', 'templates', 'static']:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ {directory}/ ready")
    
    # Step 4: Check .env file
    print_section("Step 4: Checking credentials")
    env_file = Path('.env')
    
    if env_file.exists():
        print("✓ .env file found")
    else:
        print("⚠️  No .env file found")
        print("\nYou need to manually create a .env file with:")
        print("  PESU_EMAIL=your_email@pesu.edu")
        print("  PESU_PASSWORD=your_password")
        print("\nSkipping this for now, but you must add it before downloading.")
    
    # Step 5: Verify key files
    print_section("Step 5: Verifying required files")
    required_files = [
        'web_app.py',
        'interactive_download.py',
        'templates/index.html',
        'static/style.css',
        'static/app.js'
    ]
    
    for file in required_files:
        if Path(file).exists():
            print(f"✓ {file}")
        else:
            print(f"❌ {file} - MISSING!")
    
    print_header("SETUP COMPLETE!")
    
    print("\n📖  NEXT STEPS:\n")
    print("1. Create/update your .env file with PESU credentials:")
    print("   PESU_EMAIL=your_email@pesu.edu")
    print("   PESU_PASSWORD=your_password")
    
    print("\n2. Run the web app in one of two ways:\n")
    print("   Option A (Recommended): Use the quick start script")
    print("   $ python run_web_app.py\n")
    print("   Option B: Start Flask directly")
    print("   $ python web_app.py\n")
    
    print("3. Open your browser at:")
    print("   http://localhost:5000\n")
    
    print("4. Follow the step-by-step wizard to:")
    print("   - Login to PESU Academy")
    print("   - Select your course")
    print("   - Choose units and resources")
    print("   - Download and merge PDFs\n")
    
    print("="*60)
    print("\n💡 For detailed documentation, see: WEB_APP_README.md\n")
    
    # Ask if user wants to start now
    print("Would you like to start the web app now?")
    response = input("Enter 'y' to start, or 'n' to exit: ").strip().lower()
    
    if response == 'y':
        print("\n🚀 Starting web app...")
        os.system('python run_web_app.py')
    else:
        print("\n👋 Run 'python run_web_app.py' when ready!\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user\n")
        sys.exit(0)
