import requests
from web_app import get_session
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()
srn = os.getenv('PESU_SRN')
pwd = os.getenv('PESU_PASSWORD')

session = get_session()
r1 = session.get('https://www.pesuacademy.com/', timeout=15)
soup = BeautifulSoup(r1.text, "html.parser")
csrf_input = soup.find("input", {"name": "_csrf"})
csrf = csrf_input.get("value")

session.post('https://www.pesuacademy.com/j_spring_security_check', data={'j_username': srn, 'j_password': pwd, '_csrf': csrf})

r = session.get('https://www.pesuacademy.com/a/i/getCourse/1')
print("--- RESPONSE FROM getCourse/1 ---")
print(r.text)
