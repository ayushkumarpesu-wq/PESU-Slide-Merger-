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

r = session.get('https://www.pesuacademy.com/Academy/a/g/getSubjectsCode')
soup2 = BeautifulSoup(r.text, 'html.parser')
options = soup2.find_all('option')
print("Total options:", len(options))
res = []
for o in options[:5]:
    res.append({"value": o.get('value'), "text": o.text.strip()})

with open("test_output.json", "w", encoding="utf-8") as f:
    json.dump(res, f)
