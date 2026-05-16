import requests
import sys
import os
import json
sys.path.append('.')
from web_app import get_session, load_dotenv
from bs4 import BeautifulSoup

load_dotenv()
session = get_session()
r1 = session.get('https://www.pesuacademy.com/Academy/', timeout=15)
soup = BeautifulSoup(r1.text, 'html.parser')
csrf = soup.find('input', {'name': '_csrf'}).get('value')
session.post('https://www.pesuacademy.com/Academy/j_spring_security_check', data={'j_username': os.getenv('PESU_SRN'), 'j_password': os.getenv('PESU_PASSWORD'), '_csrf': csrf})

# Get subjects
r = session.get('https://www.pesuacademy.com/Academy/a/g/getSubjectsCode')
soup2 = BeautifulSoup(r.text, 'html.parser')
options = soup2.find_all('option')
course_id = options[0].get('value').replace('\\"', "").replace("\\'", "").strip('"').strip("'").replace("\\", "")

print(f"Course ID: {course_id}")
r2 = session.get(f'https://www.pesuacademy.com/Academy/a/i/getCourse/{course_id}')
soup3 = BeautifulSoup(r2.text, 'html.parser')
unit_options = soup3.find_all('option')

units = []
for option in unit_options:
    unit_id = option.get("value").replace("\\", "").strip('"').strip("'")
    unit_name = option.text.strip()
    if unit_id and unit_name:
        units.append({"id": unit_id, "name": unit_name})

print("Units:", units)

if units:
    first_unit_id = units[0]["id"]
    print(f"Fetching classes for unit {first_unit_id}")
    r3 = session.get(f'https://www.pesuacademy.com/Academy/a/i/getCourseClasses/{first_unit_id}')
    try:
        html_content = r3.json() if 'application/json' in r3.headers.get("Content-Type", "") else r3.text
    except:
        html_content = r3.text
    soup4 = BeautifulSoup(html_content, 'html.parser')
    class_options = soup4.find_all('option')
    classes = []
    for option in class_options:
        cls_id = option.get("value")
        cls_name = option.text.strip()
        classes.append({"id": cls_id, "name": cls_name})
    print("Classes:", classes[:5])
