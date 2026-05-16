# PESU Academy Course Downloader

A Python-based application to download, merge, and manage course materials from PESU (PES University) Academy. This tool provides both a web interface and interactive CLI for seamless course content management.

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

---

## ✨ Features

### Core Capabilities
- **PESU Academy Authentication**: Secure login with SRN (Student Registration Number) and password
- **Multiple Resource Types**: Download various course materials:
  - 📊 Slides
  - 📝 Notes
  - ❓ Q&A Materials
  - 📝 Assignments
  - 📚 Question Bank (QB)
  - ❔ MCQs
  - 🔗 References

### Download & Processing
- **Batch Download**: Download multiple courses/units efficiently
- **PDF Merging**: Combine multiple PDFs into single documents
- **Format Conversion**: Convert between multiple formats (PowerPoint, Word, PDF)
- **Progress Tracking**: Real-time download progress monitoring via web UI

### User Interfaces
- **Web UI** (Flask-based):
  - Browser-based interface for easy course selection
  - Real-time progress updates
  - Responsive design with CORS support
  
- **Interactive CLI**:
  - Terminal-based course navigation
  - Curses UI for better UX on command line
  - Colorized output with progress indicators

### Advanced Features
- **Voice Assistant**: Voice-controlled downloads with text-to-speech feedback
- **Session Persistence**: Maintains login session across requests
- **Course Caching**: Cached course data to reduce API calls
- **Error Handling**: Robust error recovery and logging

---

## 🛠 Tech Stack

### Core Framework & Libraries
| Component | Library | Version |
|-----------|---------|---------|
| **Web Framework** | Flask | ≥ 2.3.0 |
| **CORS Support** | Flask-CORS | ≥ 4.0.0 |
| **HTTP Client** | requests | ≥ 2.28.2 |
| **Web Scraping** | BeautifulSoup4 | ≥ 4.12.2 |
| **HTML Parser** | lxml | ≥ 4.9.3 |

### Document Processing
| Component | Library | Version |
|-----------|---------|---------|
| **PDF Handling** | pypdf | ≥ 3.11.0 |
| **PowerPoint** | python-pptx | ≥ 0.6.21 |
| **Word Documents** | python-docx | ≥ 0.8.11 |
| **COM Support** | comtypes | ≥ 1.1.11 |

---

## 📦 Prerequisites

- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Internet Connection**: Required for PESU Academy access
- **PESU Account**: Valid PESU Academy credentials (SRN and password)
- **pip**: Python package manager

---

## 🚀 Installation

### Step 1: Clone or Download the Repository
```bash
git clone <repository-url>
cd PESU_SLIDES_Merger/.venv/THE_SLIDE_MERGER
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```
## ⚙️ Configuration

### Step 1: Create `.env` File
Create a `.env` file in the project root directory with your credentials:

```bash
# PESU Academy Credentials
PESU_SRN=your_srn_number
PESU_PASSWORD=your_password

# Optional: API Settings
API_TIMEOUT=30
DOWNLOAD_TIMEOUT=60
CACHE_EXPIRY=3600
```

**Example:**
```bash
PESU_SRN=PES2UG20CS001
PESU_PASSWORD=your_secure_password
API_TIMEOUT=30
``
## 📖 Usage

### Option 1: Web Interface (Recommended)

#### Start the Web Server:
```bash
python pesu_course_downloader/run_web_app.py
```

**Expected Output:**
```
✓ Packages verified successfully!
✓ Running PESU Academy Downloader Web Interface
✓ Flask app running at http://127.0.0.1:5000
Opening browser...
```

The application will automatically open in your default browser at `http://localhost:5000`

**Features:**
- Click "Login" to authenticate with PESU Academy
- Select courses from the list
- Choose units and resource types
- Monitor real-time download progress
- Merge and convert documents as needed

---

### Option 2: Interactive CLI

#### Start Interactive Downloader:
```bash
python pesu_course_downloader/interactive_download.py
```

**Workflow:**
1. Enter your credentials when prompted
2. Select courses using arrow keys
3. Choose units within selected course
4. Pick resource types to download
5. Monitor download progress
6. Choose conversion/merge options
7. View downloaded files

**Keyboard Shortcuts (CLI):**
- ↑/↓ Arrow Keys: Navigate options
- Enter: Select option
- q: Quit/Go back
- Ctrl+C: Exit

---

### Option 3: Direct Script Testing

#### Test API Connection:
```bash
python pesu_course_downloader/test_api.py
```

#### Run Diagnostic:
```bash
python pesu_course_downloader/diagnostic.py
```

#### Run Unit Tests:
```bash
python pesu_course_downloader/test_units.py
```

---

## 📁 Project Structure

```
PESU_SLIDES_Merger/
├── .venv/
│   └── THE_SLIDE_MERGER/
│       └── pesu_course_downloader/
│           ├── web_app.py                 # Main Flask web application
│           ├── run_web_app.py             # Web app launcher
│           ├── interactive_download.py    # CLI interactive downloader
│           ├── requirements.txt           # Python dependencies
│           ├── setup.py                   # Package setup configuration
│           ├── courses.json               # Cached course data
│           ├── diagnostic.py              # Diagnostic utilities
│           ├── test_api.py                # API connection tests
│           ├── test_setup.py              # Setup verification tests
│           ├── test_subjects.py           # Subject data tests
│           ├── test_units.py              # Unit tests
│           ├── test_units_classes.py      # Unit class tests
│           ├── direct_test.py             # Direct functionality tests
│           ├── fix_app.py                 # App fixes/patches
│           ├── fix_web_app.py             # Web app fixes/patches
│           ├── templates/                 # Flask HTML templates
│           │   ├── index.html            # Main page
│           │   └── ...
│           └── static/                    # Static assets
│               ├── css/
│               ├── js/
│               └── assets/
└── .git/                                  # Git repository
```

---

## 🔍 Key Modules

### `web_app.py`
Main Flask application handling:
- Route management
- Session persistence
- Download coordination
- Real-time progress tracking
- Static file serving

### `interactive_download.py`
Terminal-based interface providing:
- Course navigation
- Unit selection
- Resource type filtering
- Progress visualization
- Format conversion options

### `run_web_app.py`
Application launcher handling:
- Dependency verification
- Environment configuration
- Browser auto-launch
- Server initialization

### `diagnostic.py`
Troubleshooting tools for:
- Connection verification
- Credential validation
- Permission checks
- Cache integrity

---

## 🐛 Troubleshooting

### Common Issues

#### 1. **ImportError: No module named 'flask'**
```bash
pip install -r pesu_course_downloader/requirements.txt
```

#### 2. **Connection Timeout**
- Verify internet connection
- Check PESU Academy website status
- Increase timeout in `.env`: `API_TIMEOUT=60`

#### 3. **Authentication Failed**
```bash
# Run diagnostic
python pesu_course_downloader/diagnostic.py

# Verify credentials in .env
# Reset session:
python pesu_course_downloader/test_api.py
```

#### 4. **PyAudio Installation Issues (Windows)**
```bash
# Use wheels repository
pip install pipwin
pipwin install pyaudio
```

#### 5. **Permission Denied (Downloads)**
- Ensure write permissions in download folder
- Run as administrator if needed
- Check disk space availability

#### 6. **Curses Display Issues (Windows)**
```bash
pip install windows-curses --upgrade
```

#### 7. **Port Already in Use**
```bash
# Kill process on port 5000 (Windows)
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Or use different port in code
```

---

## 🚀 Advanced Usage

### Download to Custom Location
Modify the download path in `.env`:
```bash
DOWNLOAD_PATH=/custom/path/to/downloads
```

### Batch Download with Conversion
```bash
python pesu_course_downloader/interactive_download.py --batch --convert-format pdf
```

### Using Voice Control
```bash
python pesu_course_downloader/interactive_download.py --voice
```

### Generate Detailed Logs
```bash
python pesu_course_downloader/web_app.py --debug --log-level DEBUG
```

---

## 📝 Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `PESU_SRN` | Required | Student Registration Number |
| `PESU_PASSWORD` | Required | PESU Academy password |
| `API_TIMEOUT` | 30 | API request timeout (seconds) |
| `DOWNLOAD_TIMEOUT` | 60 | Download timeout (seconds) |
| `CACHE_EXPIRY` | 3600 | Cache validity (seconds) |
| `DOWNLOAD_PATH` | ./downloads | Download destination |
| `LOG_LEVEL` | INFO | Logging verbosity |
| `FLASK_DEBUG` | False | Flask debug mode |

---

## ✅ Verification Checklist

Before using the application:

- [ ] Python 3.8+ installed: `python --version`
- [ ] Virtual environment created and activated
- [ ] All dependencies installed: `pip list | grep -i flask`
- [ ] `.env` file created with credentials
- [ ] Internet connection available
- [ ] PESU Academy credentials verified
- [ ] Download folder has write permissions
- [ ] Port 5000 is available (for web UI)

---

## 📞 Support & Debugging

### Get Detailed Logs
```bash
python pesu_course_downloader/diagnostic.py --verbose
```

### Run All Tests
```bash
python pesu_course_downloader/test_setup.py
python pesu_course_downloader/test_api.py
python pesu_course_downloader/test_units.py
```

### Clear Cache
```bash
# Remove courses.json
rm pesu_course_downloader/courses.json

# Restart application
python pesu_course_downloader/run_web_app.py
```

---

## 📄 License

[Add your license information here]

---

## 👨‍💻 Development

### Contributing
1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to branch: `git push origin feature/your-feature`
5. Submit pull request

### Running Tests During Development
```bash
# Run all tests
python -m pytest pesu_course_downloader/test_*.py -v

# Run specific test
python -m pytest pesu_course_downloader/test_units.py -v

# With coverage
pip install pytest-cov
python -m pytest --cov=pesu_course_downloader
```

---

## 🔐 Security Notes

- **Never commit `.env` file** containing credentials
- Use environment variables for sensitive data
- Validate all downloaded files before opening
- Keep dependencies updated: `pip install --upgrade -r requirements.txt`
- Review logs for suspicious activity: `cat debug.log`

---

## ⚠️ Disclaimer

This tool is for personal educational use only. Ensure compliance with PESU Academy's terms of service and copyright policies before downloading materials. The developers assume no responsibility for misuse or policy violations.

---

## 📞 Contact & Support

For issues, suggestions, or improvements:
- Open an issue on GitHub
- Contact the development team
- Check existing documentation

---

**Last Updated**: May 2026  
**Version**: 1.0.0  
**Status**: ✅ Active Development

---

## 🎯 Quick Start Summary

```bash
# 1. Clone & navigate
cd PESU_SLIDES_Merger/.venv/THE_SLIDE_MERGER

# 2. Create virtual environment
python -m venv venv && venv\Scripts\activate

# 3. Install dependencies
pip install -r pesu_course_downloader/requirements.txt

# 4. Configure credentials
echo "PESU_SRN=your_srn" > .env
echo "PESU_PASSWORD=your_pwd" >> .env

# 5. Run web interface
python pesu_course_downloader/run_web_app.py

# 6. Or use interactive CLI
python pesu_course_downloader/interactive_download.py
```

Happy learning! 🎓
