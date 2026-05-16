# PESU Academy Course Downloader - Web Edition 🎓

A modern, beautiful web application for downloading and managing course materials from PESU Academy with an intuitive step-by-step interface.

## Features ✨

- 🎯 **Easy-to-use Interface**: Multi-step wizard for course selection and downloading
- 📊 **Real-time Progress Tracking**: Live updates on download progress with file count and elapsed time
- 🔍 **Smart Course Discovery**: Filter courses by academic year, search by code or name, and pagination support
- 📁 **Flexible Resource Download**: Select specific units and resource types (Slides, Notes, Assignments, etc.)
- 🔗 **PDF Merging**: Automatically merge multiple PDFs by resource type
- 💾 **Organized Downloads**: Downloads automatically organized by course and unit
- 🎨 **Beautiful UI**: Modern, responsive design with gradient themes and smooth animations
- 🔐 **Session Management**: Secure login handling with state management

## Requirements 📋

- Python 3.8+
- Virtual environment setup
- Dependencies in `requirements.txt`

## Installation 🚀

### 1. Install Required Packages

```bash
# Activate your virtual environment first
python -m pip install -r requirements.txt
```

Or manually install Flask and Flask-CORS:

```bash
pip install Flask>=2.3.0 Flask-CORS>=4.0.0
```

### 2. Verify Environment Setup

Ensure you have a `.env` file with your PESU Academy credentials:

```
PESU_EMAIL=your_email@pesu.edu
PESU_PASSWORD=your_password
```

## Running the Web App 🌐

### Start the Flask Development Server

```bash
python web_app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

### Open in Browser

Open your web browser and navigate to:
```
http://localhost:5000
```

## Usage Guide 📖

### Step 1: Login
- Click "Login to PESU Academy" button
- The app will authenticate using your credentials from `.env`
- Proceed when login is successful

### Step 2: Select Course
- Choose an academic year from the dropdown
- Browse available courses or search by course code/name
- Click on a course card to select it
- Use pagination to navigate through courses

### Step 3: Choose Units & Resources
- Select the units you want to download (months/sections of the course)
- Choose resource types: Slides, Notes, QA, Assignments, QB, MCQs, References
- Optionally enable "Merge PDFs by resource type" to combine all PDFs
- Click "Start Download" to begin

### Step 4: Monitor Progress
- Watch real-time progress with percentage completion
- See current file being downloaded and total file count
- View elapsed time and current operation step
- Download location displayed upon completion

## API Endpoints 🔌

- `POST /api/login` - Authenticate user
- `POST /api/courses` - Fetch available courses (year may be supplied). The frontend will automatically request all years when performing a search so that results are global regardless of the selected year.
- `POST /api/course-details` - Get course units and resources
- `POST /api/download` - Start downloading course materials
- `GET /api/status` - Check current download status
- `GET /api/downloads` - List completed downloads
- `POST /api/download-file` - Download specific file

## Project Structure 📁

```
pesu_course_downloader/
├── web_app.py              # Flask backend application
├── interactive_download.py  # Core downloader logic
├── templates/
│   └── index.html          # Main web interface
├── static/
│   ├── style.css           # Modern styling
│   └── app.js              # Frontend logic & interactions
├── downloads/              # Downloaded course materials
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
└── README.md              # This file
```

## Key Features Breakdown 🔧

### Frontend (HTML/CSS/JavaScript)
- **Modern Design**: Gradient backgrounds, smooth animations, responsive grid layout
- **Step Wizard**: Visual progress indicator showing current step and completion
- **Real-time Updates**: Status polling for live download progress
- **Responsive**: Works on desktop, tablet, and mobile devices
- **Accessibility**: Proper labels, form validation, helpful error messages

### Backend (Flask/Python)
- **Thread Safety**: Background download processing with thread-safe state management
- **REST API**: Clean endpoints for all operations
- **Modular Design**: Integrates seamlessly with existing downloader code
- **Error Handling**: Comprehensive error logging and user-friendly messages
- **Progress Tracking**: Real-time state updates for frontend consumption

## Troubleshooting 🔧

### Port Already in Use
If port 5000 is already in use:
```bash
# Change the port in web_app.py:
app.run(debug=True, host='0.0.0.0', port=5001)  # Use 5001 instead
```

### Login Fails
- Check `.env` file has correct credentials
- Verify PESU Academy website is accessible
- Check internet connection

### Downloads Not Starting
- Ensure at least one unit and resource type is selected
- Check browser console for error messages
- Verify you have write permissions in the `downloads` directory

### Progress Not Updating
- Check browser console for JavaScript errors
- Ensure Flask server is still running
- Try refreshing the page

## Advanced Configuration 🎛️

### Debug Mode
Edit `web_app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5000)  # debug=True enables hot reload
```

### Change Download Directory
Edit `web_app.py` and modify the downloads path:
```python
downloads_dir = Path('your_custom_path')
```

### Disable CORS (if needed)
The app uses Flask-CORS for security. To restrict origins:
```python
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5000"}})
```

## Performance Tips ⚡

- Use pagination when browsing large course lists
- Filter courses by year to reduce list size
- Download during off-peak hours for faster speeds
- PDF merging is automatic but can take time for large files

## Known Limitations ⚠️

- Requires active internet connection
- PDF merging depends on file availability
- Large course downloads may take time
- Some office formats may not convert perfectly to PDF

## Future Enhancements 🚀

- [ ] Batch download multiple courses
- [ ] Schedule downloads at specific times
- [ ] Email notifications on completion
- [ ] Download history and resume capability
- [ ] Custom naming and organization options
- [ ] Export download logs

## Contributing 🤝

Feel free to report issues and suggest improvements!

## License 📄

This project is provided as-is for educational purposes.

---

**Made with ❤️ for PESU Academy students**

For support, check the troubleshooting section or review Flask/Python documentation.
