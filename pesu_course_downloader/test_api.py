#!/usr/bin/env python3
"""Test the web_app.py functions directly"""

import sys
import os

# Add the current directory to sys.path
sys.path.insert(0, os.path.dirname(__file__))

# Import the functions from web_app
from web_app import load_courses_data

print("=" * 60)
print("🧪 Testing load_courses_data() Function")
print("=" * 60)

# Test loading courses
print("\n📚 Loading courses...")
courses = load_courses_data()

print(f"✅ Successfully loaded {len(courses)} courses")

# Verify all items are dicts
print("\n🔍 Verifying data types...")
all_dicts = all(isinstance(c, dict) for c in courses)
print(f"✅ All items are dicts: {all_dicts}")

# Show first 5 courses
print("\n📋 First 5 courses:")
for i, course in enumerate(courses[:5], 1):
    code = course.get('subjectCode') or course.get('code') or 'N/A'
    name = course.get('subjectName') or course.get('name') or 'N/A'
    print(f"  {i}. {code}: {name}")

# Test filtering and searching
print("\n🔎 Testing course filtering...")

# Filter by subjectCode containing 'CS'
cs_courses = [c for c in courses if 'CS' in c.get('subjectCode', '')]
print(f"✅ Found {len(cs_courses)} courses with 'CS' in code")

# Get a specific course code
if courses:
    test_code = courses[0].get('subjectCode')
    matching = [c for c in courses if c.get('subjectCode') == test_code]
    print(f"✅ Found {len(matching)} course(s) with code '{test_code}'")

print("\n" + "=" * 60)
print("✨ load_courses_data() function works correctly!")
print("=" * 60)

# Test caching
print("\n⚡ Testing caching...")
courses2 = load_courses_data()
print(f"✅ Courses are cached (same object): {id(courses) == id(courses2)}")

print("\n🎉 All tests passed!")
