#!/usr/bin/env python3
"""Direct test of the course details API function"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from web_app import app, load_courses_data

# Create a test client
client = app.test_client()

print("Testing units endpoint directly...\n")

# Get first course
courses = load_courses_data()
if courses:
    first_course = courses[0]
    code = first_course.get('subjectCode')
    print(f"Testing with course: {code}\n")
    
    # Call the API endpoint  
    response = client.get(f'/api/courses/{code}')
    
    print(f"Status: {response.status_code}")
    data = response.get_json()
    
    print(f"Success: {data.get('success')}")
    print(f"Units: {data.get('units')}")
    
    if len(data.get('units', [])) > 0:
        print("\n[OK] Units are being returned!")
    else:
        print("\n[ERROR] Units are empty!")
        print(f"Full response: {data}")
else:
    print("No courses loaded!")
