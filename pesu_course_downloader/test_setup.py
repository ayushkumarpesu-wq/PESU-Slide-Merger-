#!/usr/bin/env python3
"""Test script to verify Flask and course loading"""

import sys
import json
import os

print("=" * 60)
print("🧪 Testing Web App Setup")
print("=" * 60)

# Test Flask import
try:
    import flask
    print("✅ Flask imported successfully")
except ImportError as e:
    print(f"❌ Flask import failed: {e}")
    sys.exit(1)

# Test Flask-CORS import
try:
    from flask_cors import CORS
    print("✅ Flask-CORS imported successfully")
except ImportError as e:
    print(f"❌ Flask-CORS import failed: {e}")
    sys.exit(1)

# Test python-dotenv import
try:
    from dotenv import load_dotenv
    print("✅ python-dotenv imported successfully")
except ImportError as e:
    print(f"❌ python-dotenv import failed: {e}")
    sys.exit(1)

# Test loading courses.json
print("\n📚 Testing course data loading...")
courses_file = os.path.join(os.path.dirname(__file__), 'courses.json')

if not os.path.exists(courses_file):
    print(f"❌ courses.json not found at {courses_file}")
    sys.exit(1)

try:
    with open(courses_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print("✅ courses.json loaded successfully")
    
    if isinstance(data, dict) and 'courses' in data:
        courses = data['courses']
        print(f"✅ Found 'courses' key with {len(courses)} items")
        
        # Check data types
        dict_count = sum(1 for c in courses if isinstance(c, dict))
        string_count = sum(1 for c in courses if isinstance(c, str))
        other_count = len(courses) - dict_count - string_count
        
        print(f"   - Dict items: {dict_count}")
        print(f"   - String items: {string_count}")
        print(f"   - Other items: {other_count}")
        
        if dict_count > 0:
            first_course = courses[0]
            if isinstance(first_course, dict):
                print(f"\n✅ First course structure:")
                print(f"   Keys: {list(first_course.keys())}")
                print(f"   Sample: {first_course}")
    else:
        print("❌ Unexpected courses.json structure")
        sys.exit(1)
        
except json.JSONDecodeError as e:
    print(f"❌ courses.json is not valid JSON: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error loading courses.json: {e}")
    sys.exit(1)

# Test .env file
print("\n⚙️  Checking .env file...")
env_file = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_file):
    print("✅ .env file exists")
else:
    print("⚠️  .env file not found (will be created when app runs)")

print("\n" + "=" * 60)
print("✨ All setup checks passed!")
print("=" * 60)
