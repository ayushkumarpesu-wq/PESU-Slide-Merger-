"""
PESU Academy Course Downloader - Web Application
"""

import os
import json
import threading
import re
import subprocess
import sys
import io
import zipfile
from urllib.parse import quote, unquote
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response, stream_with_context, redirect
from flask_cors import CORS
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# ============================================
# GLOBAL STATE
# ============================================

DOWNLOAD_PROGRESS = {
    'status': 'idle',
    'progress': 0,
    'current_file': '',
    'total_files': 0,
    'downloaded_files': 0,
    'start_time': None,
    'elapsed_time': 0,
    'error_message': '',
    'success_message': '',
    'last_download_dir': ''
}

# Shared requests session (persists login cookies)
_SESSION = None
_COURSES_CACHE = None

BASE_URL = "https://www.pesuacademy.com/Academy"

RESOURCE_TYPES = {
    "2": "Slides",
    "3": "Notes",
    "4": "QA",
    "5": "Assignments",
    "6": "QB",
    "7": "MCQs",
    "8": "References",
}

# ============================================
# HELPERS
# ============================================

def get_session():
    global _SESSION
    if _SESSION is None:
        _SESSION = requests.Session()
    return _SESSION

def reset_session():
    global _SESSION
    _SESSION = requests.Session()
    return _SESSION

def login_with_env_session():
    """Authenticate session using env credentials."""
    srn = os.getenv('PESU_SRN', '') or os.getenv('PESU_USERNAME', '')
    password = os.getenv('PESU_PASSWORD', '')
    if not srn or not password:
        return False, 'PESU credentials not configured. Set PESU_SRN/PESU_USERNAME and PESU_PASSWORD.'

    session = reset_session()
    r0 = session.get(f"{BASE_URL}/", timeout=15)
    soup = BeautifulSoup(r0.text, "html.parser")
    csrf_input = soup.find("input", {"name": "_csrf"})
    csrf_token = csrf_input.get("value") if csrf_input else None
    if not csrf_token:
        return False, 'Could not get CSRF token from PESU Academy'

    login_data = {"j_username": srn, "j_password": password, "_csrf": csrf_token}
    response = session.post(f"{BASE_URL}/j_spring_security_check", data=login_data, timeout=15)
    if "authfailed" in response.url:
        return False, 'Login failed. Check your SRN and password.'

    verify = session.get(f"{BASE_URL}/s/studentProfilePESU", timeout=15, allow_redirects=True)
    if is_auth_page(verify.text, verify.url):
        return False, 'Login session not established. Please try again.'
    return True, srn

def load_courses_data():
    """Load courses from courses.json — simple and direct."""
    global _COURSES_CACHE
    if _COURSES_CACHE is not None:
        return _COURSES_CACHE

    courses_file = os.path.join(os.path.dirname(__file__), 'courses.json')
    courses = []

    if os.path.exists(courses_file):
        try:
            with open(courses_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Structure is always: {"_saved_at": float, "courses": [...]}
            if isinstance(data, dict) and 'courses' in data:
                raw = data['courses']
                if isinstance(raw, list):
                    courses = [c for c in raw if isinstance(c, dict)]
            elif isinstance(data, list):
                courses = [c for c in data if isinstance(c, dict)]

            print(f"[OK] Loaded {len(courses)} courses")
        except Exception as e:
            print(f"[ERROR] courses.json: {e}")

    # Vercel fallback: courses.json may be absent due repo/.gitignore layout.
    # If local file has no data, fetch live course list from authenticated PESU session.
    if not courses:
        ok, _ = login_with_env_session()
        if not ok:
            _COURSES_CACHE = []
            return _COURSES_CACHE
        courses = fetch_courses_from_pesu()

    _COURSES_CACHE = courses
    return courses

def fetch_courses_from_pesu():
    """Fetch courses live from PESU when local courses.json is unavailable."""
    try:
        session = get_session()
        response = session.get(f"{BASE_URL}/a/g/getSubjectsCode", timeout=20, allow_redirects=True)
        content_type = (response.headers.get("Content-Type", "") or "").lower()

        # If login/session is missing, avoid returning auth HTML as course data.
        if is_auth_page(response.text, response.url):
            print("[WARN] Cannot fetch live courses: session not authenticated")
            return []

        payload = response.json() if "json" in content_type else None
        if not isinstance(payload, list):
            print("[WARN] Live courses response is not a list")
            return []

        normalized = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            normalized.append({
                "id": safe_str(item.get("id")),
                "subjectCode": safe_str(item.get("subjectCode") or item.get("code")),
                "subjectName": safe_str(item.get("subjectName") or item.get("name")),
            })

        print(f"[OK] Loaded {len(normalized)} courses from live PESU API")
        return normalized
    except Exception as e:
        print(f"[WARN] Live courses fetch failed: {e}")
        return []

def safe_str(value):
    if value is None:
        return ''
    if isinstance(value, (list, dict)):
        return ''
    return str(value).strip()

def canonical_course_title(course):
    """Build a stable title key so same course across years/codes deduplicates."""
    subject_name = safe_str(course.get('subjectName'))
    subject_code = safe_str(course.get('subjectCode'))
    text = subject_name or subject_code

    if '-' in text:
        left, right = text.split('-', 1)
        left = left.strip().upper()
        if left == subject_code.upper() or re.fullmatch(r'[A-Z0-9]+', left):
            text = right

    text = text.lower()
    text = re.sub(r'[\s_&/-]+', ' ', text)
    return text.strip()

def course_sort_key(course):
    """Prefer newer batches when choosing one representative duplicate."""
    code = safe_str(course.get('subjectCode')).upper()
    m_ue = re.match(r'^UE(\d{2})', code)
    if m_ue:
        return (2, int(m_ue.group(1)), code)

    m_legacy = re.match(r'^(\d{2})', code)
    if m_legacy:
        return (1, int(m_legacy.group(1)), code)

    return (0, 0, code)

def deduplicate_courses(courses):
    """Keep one course per canonical title (newest batch wins)."""
    picked = {}
    for c in courses:
        key = canonical_course_title(c)
        if not key:
            key = safe_str(c.get('subjectCode')).lower()
        existing = picked.get(key)
        if existing is None or course_sort_key(c) > course_sort_key(existing):
            picked[key] = c
    return list(picked.values())

def is_auth_page(html: str, final_url: str = "") -> bool:
    """Detect PESU login/auth pages to avoid treating them as real data.
    NOTE: Do NOT check for _csrf — every PESU page has CSRF tokens in forms."""
    text = (html or "").lower()
    url = (final_url or "").lower()
    return (
        "j_spring_security_check" in text or
        'name="j_username"' in text or
        'name="j_password"' in text or
        "authfailed" in url
    )

def get_units_from_pesu(course_id: str):
    """Fetch units for a course from PESU Academy (requires active session)."""
    session = get_session()
    url = f"{BASE_URL}/a/i/getCourse/{course_id}"
    response = session.get(url, timeout=15, allow_redirects=True)
    if is_auth_page(response.text, response.url):
        raise RuntimeError("Session expired or not logged in")

    soup = BeautifulSoup(response.text, "html.parser")

    units = []
    for option in soup.find_all("option"):
        unit_id = option.get("value", "").strip().replace("\\", "").strip('"').strip("'")
        unit_name = option.text.strip()
        if unit_id and unit_name:
            units.append({"id": unit_id, "name": unit_name})

    if not units:
        raise RuntimeError("No units returned by PESU for this course")

    return units

def get_classes_from_pesu(unit_id: str):
    """Fetch classes for a given unit from PESU Academy."""
    session = get_session()
    classes_url = f"{BASE_URL}/a/i/getCourseClasses/{unit_id}"
    try:
        r = session.get(classes_url, timeout=15)
        html = r.json() if 'application/json' in r.headers.get('Content-Type', '') else r.text
        soup = BeautifulSoup(html, "html.parser")
        classes = []
        for opt in soup.find_all("option"):
            cid = opt.get("value", "").strip().replace("\\", "").strip('"').strip("'")
            cname = opt.text.strip()
            if cid and cname:
                classes.append({"id": cid, "name": cname})
        return classes
    except Exception as e:
        print(f"[WARN] Could not get classes for unit {unit_id}: {e}")
        return []

def parse_selected_classes(selected_classes_raw):
    """Parse selected classes format: unit_id|class_id|unit_name|class_name."""
    selected_classes = []
    for c in selected_classes_raw or []:
        parts = c.split('|')
        if len(parts) == 4:
            selected_classes.append({
                'unit_id': parts[0],
                'class_id': parts[1],
                'unit_name': parts[2],
                'class_name': parts[3]
            })
    return selected_classes

def parse_selected_resource_ids(selected_resource_names):
    """Map resource names back to resource IDs."""
    name_to_id = {v: k for k, v in RESOURCE_TYPES.items()}
    return [name_to_id[r] for r in (selected_resource_names or []) if r in name_to_id]

def fetch_resource_response(session, pesu_id: str, class_id: str, resource_id: str):
    """Fetch PESU resource response for class/resource pair."""
    params = {
        "url": "studentProfilePESUAdmin",
        "controllerMode": "6403",
        "actionType": "60",
        "selectedData": pesu_id,
        "id": resource_id,
        "unitid": class_id,
    }
    return session.get(f"{BASE_URL}/s/studentProfilePESUAdmin", params=params, timeout=20)

def extract_resource_links_from_html(html: str):
    """Extract file download links from PESU resource HTML page."""
    links = []
    soup2 = BeautifulSoup(html or "", "html.parser")
    for el in soup2.find_all(onclick=True):
        onclick = el.get("onclick", "")
        if "downloadslidecoursedoc" in onclick:
            m = re.search(r"loadIframe\('([^']+)'", onclick)
            if m:
                url = m.group(1).split("#")[0]
                if url.startswith("/Academy"):
                    links.append(f"https://www.pesuacademy.com{url}")
        elif "downloadcoursedoc" in onclick:
            m = re.search(r"downloadcoursedoc\('([^']+)'", onclick)
            if m:
                links.append(f"{BASE_URL}/s/referenceMeterials/downloadcoursedoc/{m.group(1)}")
    return links

# ============================================
# ROUTES
# ============================================

@app.route('/api/health', methods=['GET'])
def api_health():
    return jsonify({'status': 'ok', 'courses_loaded': len(load_courses_data())})

@app.route('/')
def index():
    return render_template('index.html')

# ============================================
# LOGIN
# ============================================

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        ok, result = login_with_env_session()
        if not ok:
            return jsonify({'success': False, 'error': result}), 401
        return jsonify({'success': True, 'message': 'Login successful', 'user': result})

    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': 'Cannot connect to PESU Academy. Check your internet connection.'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# COURSES
# ============================================

@app.route('/api/courses', methods=['GET'])
def api_get_courses():
    try:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '', type=str).lower().strip()
        year = request.args.get('year', '', type=str).strip()
        items_per_page = 12

        all_courses = load_courses_data()

        # Hard fallback for Vercel: if cache/local file is empty, fetch live now.
        if not all_courses:
            ok, msg = login_with_env_session()
            if not ok:
                return jsonify({'success': False, 'error': f'Login required for courses: {msg}'}), 401

            session = get_session()
            r = session.get(f"{BASE_URL}/a/g/getSubjectsCode", timeout=20, allow_redirects=True)
            if is_auth_page(r.text, r.url):
                return jsonify({'success': False, 'error': 'Session became invalid while loading courses. Please retry login.'}), 401

            payload = r.json() if 'json' in (r.headers.get('Content-Type', '') or '').lower() else None
            if isinstance(payload, list):
                raw_list = payload
            elif isinstance(payload, dict):
                raw_list = payload.get('courses') or payload.get('data') or payload.get('subjects') or payload.get('result') or []
            else:
                raw_list = []

            all_courses = []
            if isinstance(raw_list, list):
                for item in raw_list:
                    if isinstance(item, dict):
                        all_courses.append({
                            'id': safe_str(item.get('id')),
                            'subjectCode': safe_str(item.get('subjectCode') or item.get('code')),
                            'subjectName': safe_str(item.get('subjectName') or item.get('name')),
                        })

        if not all_courses:
            return jsonify({'success': False, 'error': 'Courses API returned empty data. Check Vercel env vars and PESU account access.'}), 502

        filtered = all_courses

        if search:
            filtered = [c for c in filtered if (
                search in safe_str(c.get('subjectCode')).lower() or
                search in safe_str(c.get('subjectName')).lower()
            )]

        if year:
            filtered = [c for c in filtered if safe_str(c.get('subjectCode')).startswith(year)]

        filtered = deduplicate_courses(filtered)

        total_count = len(filtered)
        total_pages = max(1, (total_count + items_per_page - 1) // items_per_page)
        page = max(1, min(page, total_pages))

        start_idx = (page - 1) * items_per_page
        paginated = filtered[start_idx:start_idx + items_per_page]

        year_prefixes = set()
        for c in all_courses:
            code = safe_str(c.get('subjectCode'))
            if (len(code) >= 4 and code[:4].startswith('UE')) or (len(code) >= 2 and code[:2].isdigit()):
                prefix = code[:4] if code[:2].upper() == 'UE' else code[:2]
                if prefix:
                    year_prefixes.add(prefix)

        available_years = sorted(year_prefixes, reverse=True)

        return jsonify({
            'success': True,
            'courses': paginated,
            'total_courses': total_count,
            'page': page,
            'total_pages': total_pages,
            'available_years': available_years
        })

    except Exception as e:
        import traceback
        print(f"[ERROR] api_get_courses: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/courses/<course_id>', methods=['GET'])
def api_get_course_details(course_id):
    """Get units for a course — fetched live from PESU Academy."""
    print(f"[DEBUG] api_get_course_details called with course_id={course_id}")
    try:
        # Find the course in our cache to get its details
        all_courses = load_courses_data()
        course = None
        for c in all_courses:
            if (safe_str(c.get('id')) == course_id or
                    safe_str(c.get('subjectCode')) == course_id):
                course = c
                break

        if not course:
            return jsonify({'success': False, 'error': f'Course {course_id} not found'}), 404

        # Use course id (numeric) for the PESU API call
        pesu_id = safe_str(course.get('id'))
        print(f"[DEBUG] Found course: {course}, trying to fetch units...")
        
        # Fetch units live from PESU Academy
        try:
            units = get_units_from_pesu(pesu_id)
            print(f"[DEBUG] get_units_from_pesu returned: {units}")
            
            # Fetch classes for each unit
            for unit in units:
                unit['classes'] = get_classes_from_pesu(unit['id'])
                
        except RuntimeError as e:
            return jsonify({'success': False, 'error': str(e)}), 401
        except Exception as e:
            print(f"[WARN] Could not fetch units from PESU: {e}")
            return jsonify({'success': False, 'error': 'Unable to fetch units from PESU Academy'}), 502

        # Return unit names as a simple list for the frontend
        unit_names = [u['name'] for u in units]
        
        print(f"[DEBUG] Returning {len(unit_names)} units: {unit_names}")

        return jsonify({
            'success': True,
            'course': course,
            'units': unit_names,          # list of strings for checkboxes
            'unit_objects': units,        # list of {id, name, classes: [{id, name}]}
            'resource_types': list(RESOURCE_TYPES.values()),
            'resource_type_ids': RESOURCE_TYPES  # {"2": "Slides", ...}
        })

    except Exception as e:
        import traceback
        print(f"[ERROR] api_get_course_details: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# DOWNLOADS
# ============================================

@app.route('/api/download/status', methods=['GET'])
def api_download_status():
    return jsonify(DOWNLOAD_PROGRESS)

def sanitize_filename(name: str, max_len: int = 60):
    return "".join(c if c.isalnum() or c in (' ', '-', '_', '.') else '_' for c in (name or '')).strip()[:max_len] or "file"

@app.route('/api/download/zip', methods=['POST'])
def api_download_zip():
    """Vercel-friendly direct zip response."""
    try:
        data = request.json or {}
        course_id = data.get('course_code')
        selected_classes = parse_selected_classes(data.get('classes', []))
        selected_resource_ids = parse_selected_resource_ids(data.get('resources', []))

        if not course_id:
            return jsonify({'success': False, 'error': 'Course code is required'}), 400
        if not selected_classes:
            return jsonify({'success': False, 'error': 'No classes selected'}), 400
        if not selected_resource_ids:
            return jsonify({'success': False, 'error': 'No valid resource types selected'}), 400

        all_courses = load_courses_data()
        course = next((c for c in all_courses if
                       safe_str(c.get('id')) == course_id or
                       safe_str(c.get('subjectCode')) == course_id), None)
        if not course:
            return jsonify({'success': False, 'error': f'Course {course_id} not found'}), 404

        pesu_id = safe_str(course.get('id'))
        course_name = safe_str(course.get('subjectName') or course.get('subjectCode'))
        session = get_session()

        buf = io.BytesIO()
        file_count = 0
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for cls in selected_classes:
                unit_name = sanitize_filename(cls.get('unit_name', ''), 50)
                class_name = sanitize_filename(cls.get('class_name', ''), 60)
                for resource_id in selected_resource_ids:
                    resource_name = sanitize_filename(RESOURCE_TYPES.get(resource_id, resource_id), 30)
                    try:
                        resp = fetch_resource_response(session, pesu_id, cls["class_id"], resource_id)
                        content_type = (resp.headers.get("Content-Type", "") or "").lower()
                        ext = ".pdf"
                        if "presentation" in content_type:
                            ext = ".pptx"
                        elif "word" in content_type:
                            ext = ".docx"

                        if "application/" in content_type and "html" not in content_type:
                            zpath = f"{unit_name}/{resource_name}/{class_name}{ext}"
                            zf.writestr(zpath, resp.content)
                            file_count += 1
                        else:
                            links = extract_resource_links_from_html(resp.text)
                            idx = 1
                            for link_url in links:
                                try:
                                    lr = session.get(link_url, headers={"Referer": f"{BASE_URL}/s/studentProfilePESU"}, timeout=20)
                                    if lr.status_code == 200 and lr.content:
                                        zpath = f"{unit_name}/{resource_name}/{class_name}_{idx}{ext}"
                                        zf.writestr(zpath, lr.content)
                                        file_count += 1
                                        idx += 1
                                except Exception:
                                    pass
                    except Exception as e:
                        print(f"[WARN] zip fetch failed for {class_name}: {e}")

        if file_count == 0:
            return jsonify({'success': False, 'error': 'No files found for selected filters'}), 404

        buf.seek(0)
        out_name = sanitize_filename(course_name, 40)
        return Response(
            buf.getvalue(),
            headers={
                "Content-Type": "application/zip",
                "Content-Disposition": f'attachment; filename=\"{out_name}_resources.zip\"'
            }
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/download/start', methods=['POST'])
def api_start_download():
    try:
        if os.getenv('VERCEL'):
            return jsonify({
                'success': False,
                'error': 'Use direct ZIP download mode on Vercel.'
            }), 400

        data = request.json or {}
        course_id = data.get('course_code')  # frontend sends course_code
        selected_classes_raw = data.get('classes', [])
        selected_resource_names = data.get('resources', [])

        if not course_id:
            return jsonify({'success': False, 'error': 'Course code is required'}), 400

        selected_classes = parse_selected_classes(selected_classes_raw)
        selected_resource_ids = parse_selected_resource_ids(selected_resource_names)

        if not selected_resource_ids:
            return jsonify({'success': False, 'error': 'No valid resource types selected'}), 400
        if not selected_classes:
            return jsonify({'success': False, 'error': 'No classes selected'}), 400

        DOWNLOAD_PROGRESS.update({
            'status': 'starting',
            'progress': 0,
            'downloaded_files': 0,
            'total_files': 0,
            'current_file': '',
            'error_message': '',
            'success_message': '',
            'last_download_dir': '',
            'start_time': datetime.now().isoformat()
        })

        thread = threading.Thread(
            target=perform_download,
            args=(course_id, selected_classes, selected_resource_ids),
            daemon=True
        )
        thread.start()

        return jsonify({'success': True, 'message': 'Download started'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/download/cancel', methods=['POST'])
def api_cancel_download():
    DOWNLOAD_PROGRESS['status'] = 'cancelled'
    return jsonify({'success': True, 'message': 'Download cancelled'})

@app.route('/api/download/open-folder', methods=['POST'])
def api_open_download_folder():
    """Open last successful download folder in system file explorer."""
    try:
        folder = safe_str(DOWNLOAD_PROGRESS.get('last_download_dir'))
        if not folder:
            return jsonify({'success': False, 'error': 'No downloaded folder available yet'}), 400
        if not os.path.isdir(folder):
            return jsonify({'success': False, 'error': f'Folder not found: {folder}'}), 404

        if os.name == 'nt':
            os.startfile(folder)  # type: ignore[attr-defined]
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', folder])
        else:
            subprocess.Popen(['xdg-open', folder])

        return jsonify({'success': True, 'folder': folder})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/resources/view', methods=['POST'])
def api_view_resources():
    """List viewable links for selected classes/resources without downloading to disk."""
    try:
        data = request.json or {}
        course_id = safe_str(data.get('course_code'))
        selected_classes = parse_selected_classes(data.get('classes', []))
        selected_resource_ids = parse_selected_resource_ids(data.get('resources', []))

        if not course_id:
            return jsonify({'success': False, 'error': 'Course code is required'}), 400
        if not selected_classes:
            return jsonify({'success': False, 'error': 'No classes selected'}), 400
        if not selected_resource_ids:
            return jsonify({'success': False, 'error': 'No valid resource types selected'}), 400

        all_courses = load_courses_data()
        course = next((c for c in all_courses if
                       safe_str(c.get('id')) == course_id or
                       safe_str(c.get('subjectCode')) == course_id), None)
        if not course:
            return jsonify({'success': False, 'error': f'Course {course_id} not found'}), 404

        pesu_id = safe_str(course.get('id'))
        session = get_session()
        view_items = []

        for cls in selected_classes:
            for resource_id in selected_resource_ids:
                resource_name = RESOURCE_TYPES.get(resource_id, resource_id)
                try:
                    resp = fetch_resource_response(session, pesu_id, cls["class_id"], resource_id)
                    content_type = (resp.headers.get("Content-Type", "") or "").lower()

                    if "application/" in content_type and "html" not in content_type:
                        direct_url = (
                            f"/api/resources/direct?"
                            f"course_id={quote(course_id)}&class_id={quote(cls['class_id'])}"
                            f"&resource_id={quote(resource_id)}&class_name={quote(cls['class_name'])}"
                        )
                        view_items.append({
                            'unit_name': cls['unit_name'],
                            'class_name': cls['class_name'],
                            'resource_name': resource_name,
                            'view_url': direct_url,
                            'source': 'direct'
                        })
                    else:
                        links = extract_resource_links_from_html(resp.text)
                        for link in links:
                            proxy_url = f"/api/resources/proxy?url={quote(link, safe='')}"
                            view_items.append({
                                'unit_name': cls['unit_name'],
                                'class_name': cls['class_name'],
                                'resource_name': resource_name,
                                'view_url': proxy_url,
                                'source': 'linked'
                            })
                except Exception as e:
                    print(f"[WARN] view resource failed for {cls['class_name']} [{resource_name}]: {e}")

        return jsonify({
            'success': True,
            'total_items': len(view_items),
            'items': view_items
        })

    except Exception as e:
        import traceback
        print(f"[ERROR] api_view_resources: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/resources/proxy', methods=['GET'])
def api_proxy_resource():
    """Proxy a PESU file link through backend session so browser can view it."""
    try:
        url = unquote(request.args.get('url', ''))
        if not url:
            return jsonify({'success': False, 'error': 'Missing url'}), 400
        if not url.startswith("https://www.pesuacademy.com/Academy"):
            return jsonify({'success': False, 'error': 'Invalid resource url'}), 400

        session = get_session()
        upstream = session.get(
            url,
            headers={"Referer": f"{BASE_URL}/s/studentProfilePESU"},
            stream=True,
            timeout=30
        )
        content_type = upstream.headers.get("Content-Type", "application/octet-stream")

        def generate():
            for chunk in upstream.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

        headers = {
            "Content-Type": content_type,
            "Content-Disposition": upstream.headers.get("Content-Disposition", "inline")
        }
        return Response(stream_with_context(generate()), headers=headers)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/resources/direct', methods=['GET'])
def api_direct_resource():
    """Fetch and stream a direct resource response for a class/resource pair."""
    try:
        course_id = safe_str(request.args.get('course_id'))
        class_id = safe_str(request.args.get('class_id'))
        resource_id = safe_str(request.args.get('resource_id'))
        class_name = safe_str(request.args.get('class_name') or 'resource')

        if not course_id or not class_id or not resource_id:
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400

        all_courses = load_courses_data()
        course = next((c for c in all_courses if
                       safe_str(c.get('id')) == course_id or
                       safe_str(c.get('subjectCode')) == course_id), None)
        if not course:
            return jsonify({'success': False, 'error': f'Course {course_id} not found'}), 404

        pesu_id = safe_str(course.get('id'))
        session = get_session()
        resp = fetch_resource_response(session, pesu_id, class_id, resource_id)
        content_type = (resp.headers.get("Content-Type", "") or "").lower()

        if "html" in content_type:
            links = extract_resource_links_from_html(resp.text)
            if not links:
                return jsonify({'success': False, 'error': 'No viewable file links found'}), 404
            first = links[0]
            proxy_url = f"/api/resources/proxy?url={quote(first, safe='')}"
            return redirect(proxy_url, code=302)

        safe_cls = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in class_name).strip()[:50]
        ext = ".pdf"
        if "presentation" in content_type:
            ext = ".pptx"
        elif "word" in content_type:
            ext = ".docx"

        headers = {
            "Content-Type": resp.headers.get("Content-Type", "application/octet-stream"),
            "Content-Disposition": f'inline; filename="{safe_cls}{ext}"'
        }
        return Response(resp.content, headers=headers)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def perform_download(course_id, selected_classes, selected_resource_ids):
    """Real download using PESU Academy session."""
    try:
        from pathlib import Path

        all_courses = load_courses_data()
        course = next((c for c in all_courses if
                       safe_str(c.get('id')) == course_id or
                       safe_str(c.get('subjectCode')) == course_id), None)

        if not course:
            raise Exception(f"Course {course_id} not found")

        pesu_id = safe_str(course.get('id'))
        course_name = safe_str(course.get('subjectName') or course.get('subjectCode'))

        session = get_session()

        if not selected_classes:
            DOWNLOAD_PROGRESS['status'] = 'failed'
            DOWNLOAD_PROGRESS['error_message'] = 'No classes selected'
            return

        # Count total files (estimate)
        DOWNLOAD_PROGRESS['status'] = 'downloading'
        DOWNLOAD_PROGRESS['total_files'] = len(selected_classes) * len(selected_resource_ids)

        # Sanitize folder name
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in course_name).strip()[:60]
        downloads_root = Path(__file__).resolve().parent / "downloads"
        base_dir = downloads_root / safe_name
        base_dir.mkdir(parents=True, exist_ok=True)

        downloaded = 0
        
        # Group classes by unit for folder structure
        classes_by_unit = {}
        for cls in selected_classes:
            unit_name = cls['unit_name']
            if unit_name not in classes_by_unit:
                classes_by_unit[unit_name] = []
            classes_by_unit[unit_name].append(cls)

        for unit_name, classes in classes_by_unit.items():
            if DOWNLOAD_PROGRESS['status'] == 'cancelled':
                return

            safe_unit = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in unit_name).strip()[:50]

            for resource_id in selected_resource_ids:
                if DOWNLOAD_PROGRESS['status'] == 'cancelled':
                    return

                resource_name = RESOURCE_TYPES[resource_id]
                resource_dir = base_dir / safe_unit / resource_name
                resource_dir.mkdir(parents=True, exist_ok=True)

                counter = 1
                for cls in classes:
                    if DOWNLOAD_PROGRESS['status'] == 'cancelled':
                        return

                    DOWNLOAD_PROGRESS['current_file'] = f"{unit_name} → {resource_name} → {cls['class_name']}"

                    try:
                        params = {
                            "url": "studentProfilePESUAdmin",
                            "controllerMode": "6403",
                            "actionType": "60",
                            "selectedData": pesu_id,
                            "id": resource_id,
                            "unitid": cls["class_id"],
                        }
                        resp = fetch_resource_response(session, pesu_id, cls["class_id"], resource_id)

                        content_type = resp.headers.get("Content-Type", "")
                        safe_cls = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in cls['class_name']).strip()[:50]

                        # Determine extension
                        ext = ".pdf"
                        if "presentation" in content_type:
                            ext = ".pptx"
                        elif "word" in content_type:
                            ext = ".docx"

                        if "application/" in content_type and "html" not in content_type:
                            # Direct file download
                            filename = f"{counter}.{safe_cls}{ext}"
                            out = resource_dir / filename
                            out.write_bytes(resp.content)
                            if out.stat().st_size > 0:
                                downloaded += 1
                                counter += 1
                        else:
                            # Parse HTML for download links
                            links = extract_resource_links_from_html(resp.text)

                            for link_url in links:
                                if DOWNLOAD_PROGRESS['status'] == 'cancelled':
                                    return
                                try:
                                    lr = session.get(link_url, headers={"Referer": f"{BASE_URL}/s/studentProfilePESU"}, stream=True, timeout=15)
                                    filename = f"{counter}.{safe_cls}{ext}"
                                    out = resource_dir / filename
                                    with open(out, 'wb') as f:
                                        for chunk in lr.iter_content(8192):
                                            f.write(chunk)
                                    if out.stat().st_size > 0:
                                        downloaded += 1
                                        counter += 1
                                    else:
                                        out.unlink()
                                except Exception:
                                    pass

                    except Exception as e:
                        print(f"[WARN] {cls['class_name']}: {e}")

                DOWNLOAD_PROGRESS['downloaded_files'] = downloaded
                if DOWNLOAD_PROGRESS['total_files'] > 0:
                    DOWNLOAD_PROGRESS['progress'] = min(99, int((downloaded / DOWNLOAD_PROGRESS['total_files']) * 100))

        if downloaded <= 0:
            DOWNLOAD_PROGRESS['status'] = 'failed'
            DOWNLOAD_PROGRESS['progress'] = 0
            DOWNLOAD_PROGRESS['downloaded_files'] = 0
            DOWNLOAD_PROGRESS['error_message'] = (
                "No files were downloaded. Please try another unit/resource "
                "or re-login and retry."
            )
            return

        DOWNLOAD_PROGRESS['status'] = 'completed'
        DOWNLOAD_PROGRESS['progress'] = 100
        DOWNLOAD_PROGRESS['downloaded_files'] = downloaded
        DOWNLOAD_PROGRESS['last_download_dir'] = str(base_dir.resolve())
        DOWNLOAD_PROGRESS['success_message'] = (
            f"Downloaded {downloaded} files to {base_dir.resolve()}\\"
        )

    except Exception as e:
        import traceback
        print(f"[ERROR] perform_download: {e}")
        print(traceback.format_exc())
        DOWNLOAD_PROGRESS['status'] = 'failed'
        DOWNLOAD_PROGRESS['error_message'] = str(e)

if __name__ == '__main__':
    app.run(debug=True, port=5000)


