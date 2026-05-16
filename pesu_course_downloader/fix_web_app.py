import sys

def fix_web_app():
    with open("web_app.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Find the start of the DOWNLOADS section
    idx = content.find("# ============================================\n# DOWNLOADS")
    if idx == -1:
        print("Could not find DOWNLOADS section")
        return

    # Keep everything before the DOWNLOADS section
    new_content = content[:idx]

    # Append the new DOWNLOADS section
    new_content += """# ============================================
# DOWNLOADS
# ============================================

@app.route('/api/download/status', methods=['GET'])
def api_download_status():
    return jsonify(DOWNLOAD_PROGRESS)


@app.route('/api/download/start', methods=['POST'])
def api_start_download():
    try:
        data = request.json or {}
        course_id = data.get('course_code')  # frontend sends course_code
        selected_classes_raw = data.get('classes', [])
        selected_resource_names = data.get('resources', [])

        if not course_id:
            return jsonify({'success': False, 'error': 'Course code is required'}), 400

        # Parse selected classes format: "unit_id|class_id|unit_name|class_name"
        selected_classes = []
        for c in selected_classes_raw:
            parts = c.split('|')
            if len(parts) == 4:
                selected_classes.append({
                    'unit_id': parts[0],
                    'class_id': parts[1],
                    'unit_name': parts[2],
                    'class_name': parts[3]
                })

        # Map resource names back to IDs
        name_to_id = {v: k for k, v in RESOURCE_TYPES.items()}
        selected_resource_ids = [name_to_id[r] for r in selected_resource_names if r in name_to_id]

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


def perform_download(course_id, selected_classes, selected_resource_ids):
    \"\"\"Real download using PESU Academy session.\"\"\"
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
        base_dir = Path("downloads") / safe_name
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
                        resp = session.get(f"{BASE_URL}/s/studentProfilePESUAdmin", params=params, timeout=15)

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
                            import re
                            soup2 = BeautifulSoup(resp.text, "html.parser")
                            links = []
                            for el in soup2.find_all(onclick=True):
                                onclick = el.get("onclick", "")
                                if "downloadslidecoursedoc" in onclick:
                                    m = re.search(r"loadIframe\\('([^']+)'", onclick)
                                    if m:
                                        url = m.group(1).split("#")[0]
                                        if url.startswith("/Academy"):
                                            links.append(f"https://www.pesuacademy.com{url}")
                                elif "downloadcoursedoc" in onclick:
                                    m = re.search(r"downloadcoursedoc\\('([^']+)'", onclick)
                                    if m:
                                        links.append(f"{BASE_URL}/s/referenceMeterials/downloadcoursedoc/{m.group(1)}")

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

        DOWNLOAD_PROGRESS['status'] = 'completed'
        DOWNLOAD_PROGRESS['progress'] = 100
        DOWNLOAD_PROGRESS['downloaded_files'] = downloaded
        DOWNLOAD_PROGRESS['success_message'] = f'Downloaded {downloaded} files to downloads/{safe_name}/'

    except Exception as e:
        import traceback
        print(f"[ERROR] perform_download: {e}")
        print(traceback.format_exc())
        DOWNLOAD_PROGRESS['status'] = 'failed'
        DOWNLOAD_PROGRESS['error_message'] = str(e)
"""
    # Write back
    with open("web_app.py", "w", encoding="utf-8") as f:
        f.write(new_content)
        
    print("Fixed web_app.py")

if __name__ == "__main__":
    fix_web_app()
