#!/usr/bin/env python3
"""
Diagnostic script to check courses.json structure
"""

import json
import os

def diagnose_courses_json():
    """Diagnose the structure of courses.json"""
    courses_file = 'courses.json'
    
    print("=" * 60)
    print("DIAGNOSTIC: courses.json Check")
    print("=" * 60)
    
    if not os.path.exists(courses_file):
        print(f"❌ {courses_file} not found!")
        return
    
    print(f"✅ {courses_file} found\n")
    
    try:
        with open(courses_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print(f"1. Data Type: {type(data)}")
        print(f"2. Data is dict: {isinstance(data, dict)}")
        print(f"3. Data is list: {isinstance(data, list)}")
        
        if isinstance(data, dict):
            print(f"\n4. Dict Keys: {list(data.keys())}")
            
            if 'courses' in data:
                courses = data['courses']
                print(f"\n5. 'courses' Type: {type(courses)}")
                print(f"6. 'courses' is list: {isinstance(courses, list)}")
                print(f"7. Number of courses: {len(courses) if isinstance(courses, list) else 'N/A'}")
                
                if isinstance(courses, list) and len(courses) > 0:
                    first = courses[0]
                    print(f"\n8. First course type: {type(first)}")
                    print(f"9. First course is dict: {isinstance(first, dict)}")
                    if isinstance(first, dict):
                        print(f"10. First course keys: {list(first.keys())}")
                        print(f"11. First course: {first}")
        
        elif isinstance(data, list):
            print(f"\n4. List length: {len(data)}")
            if len(data) > 0:
                print(f"5. First item type: {type(data[0])}")
                print(f"6. First item: {data[0]}")
        
        print("\n" + "=" * 60)
        print("✅ JSON structure looks good!")
        print("=" * 60)
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON Decode Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    diagnose_courses_json()
