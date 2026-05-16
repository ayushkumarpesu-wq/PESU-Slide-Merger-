/**
 * PESU Course Downloader - Advanced Auto Edition
 * Automatic, intelligent, and minimal user interaction
 */

const ADVANCED_STATE = {
    isLoggedIn: false,
    allCourses: [],
    selectedCourses: [],
    selectedResources: [],
    selectedResourceNames: [],
    isDownloading: false,
    downloadQueue: [],
    currentDownload: null,
    courseUnitsCache: {},
    selectedUnitsByCourse: {},
    downloadStats: {
        total: 0,
        completed: 0,
        failed: 0,
        startTime: null
    }
};

// ============================================
// INITIALIZATION & AUTO-LOAD
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('Advanced app loading...');
    initializeApp();
    startAutoMode();
});

async function initializeApp() {
    try {
        const loginStatus = await checkLoginStatus();
        if (loginStatus) {
            ADVANCED_STATE.isLoggedIn = true;
            document.getElementById('courseSection').classList.remove('hidden');
            loadCoursesAutomatically();
        }

        setupAutoUpdates();
        setupEventListeners();
        updateUI();
    } catch (err) {
        console.error('Init error:', err);
    }
}

// ============================================
// AUTO-LOGIN
// ============================================

async function performLogin() {
    const loginBtn = document.getElementById('loginBtn');
    const loginStatus = document.getElementById('loginStatus');

    loginBtn.disabled = true;
    loginBtn.textContent = 'Logging in...';
    loginStatus.innerHTML = '<p class="loading">Authenticating...</p>';

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ auto: true })
        });

        const data = await response.json();

        if (data.success) {
            ADVANCED_STATE.isLoggedIn = true;
            loginStatus.innerHTML = '<p style="color:green;">Login successful</p>';
            loginStatus.style.display = 'block';

            document.getElementById('loginSection').style.opacity = '0.7';
            document.getElementById('courseSection').classList.remove('hidden');

            loadCoursesAutomatically();
        } else {
            loginStatus.innerHTML = `<p style="color:red;">${data.error}</p>`;
        }
    } catch (err) {
        loginStatus.innerHTML = `<p style="color:red;">Error: ${err.message}</p>`;
    } finally {
        loginBtn.disabled = false;
        loginBtn.textContent = 'Login & Load Courses';
    }
}

// ============================================
// AUTO-LOAD COURSES
// ============================================

async function loadCoursesAutomatically() {
    console.log('Auto-loading courses...');
    const coursesGrid = document.getElementById('coursesGrid');
    coursesGrid.innerHTML = '<p class="loading">Loading courses...</p>';

    try {
        let allCourses = [];
        let page = 1;
        let hasMore = true;

        while (hasMore) {
            const response = await fetch(`/api/courses?page=${page}&limit=100`);
            const data = await response.json();

            if (data.success && data.courses.length > 0) {
                allCourses = allCourses.concat(data.courses);
                page++;
                hasMore = page <= data.total_pages;
            } else {
                hasMore = false;
            }
        }

        ADVANCED_STATE.allCourses = allCourses;
        document.getElementById('coursesCount').textContent = allCourses.length;

        const years = [...new Set(allCourses.map(c => (c.subjectCode || '').substring(0, 4)).filter(y => y))].sort().reverse();

        const yearSelect = document.getElementById('yearFilter');
        yearSelect.innerHTML = '<option value="">All Years</option>';
        years.forEach(year => {
            const opt = document.createElement('option');
            opt.value = year;
            opt.textContent = year;
            yearSelect.appendChild(opt);
        });

        displayCoursesGrid(allCourses);
        await preloadUnitCounts(allCourses);
    } catch (err) {
        console.error('Load error:', err);
        coursesGrid.innerHTML = `<p style="color:red;">Error loading courses: ${err.message}</p>`;
    }
}

// ============================================
// DISPLAY & FILTER COURSES
// ============================================

function displayCoursesGrid(courses) {
    const grid = document.getElementById('coursesGrid');

    if (!courses || courses.length === 0) {
        grid.innerHTML = '<p>No courses found</p>';
        return;
    }

    grid.innerHTML = courses.map((course, idx) => `
        <div class="course-card" data-index="${idx}">
            <div class="course-header">
                <input type="checkbox" class="course-checkbox" value="${course.subjectCode}"
                       onchange="updateSelectedCourses()">
                <span class="course-code">${course.subjectCode || course.code}</span>
            </div>
            <div class="course-body">
                <h3 class="course-name">${course.subjectName || course.name}</h3>
                <p class="course-id">ID: ${course.id}</p>
                <p class="course-id">Units: <span id="units-count-${course.subjectCode}">Loading...</span></p>
            </div>
            <div class="course-footer">
                <button onclick="selectSingleCourse('${course.subjectCode}', this)"
                        class="quick-select-btn">Select</button>
            </div>
        </div>
    `).join('');
}

async function preloadUnitCounts(courses) {
    const tasks = courses.map(async (course) => {
        const code = course.subjectCode;
        if (!code || ADVANCED_STATE.courseUnitsCache[code]) return;

        try {
            const response = await fetch(`/api/courses/${code}`);
            const data = await response.json();
            const units = Array.isArray(data.units) ? data.units : [];
            ADVANCED_STATE.courseUnitsCache[code] = units;
            const el = document.getElementById(`units-count-${code}`);
            if (el) el.textContent = `${units.length}`;
        } catch {
            ADVANCED_STATE.courseUnitsCache[code] = [];
            const el = document.getElementById(`units-count-${code}`);
            if (el) el.textContent = 'N/A';
        }
    });

    await Promise.all(tasks);
}

function filterCourses() {
    const search = document.getElementById('courseSearch').value.toLowerCase();
    const year = document.getElementById('yearFilter').value;

    const filtered = ADVANCED_STATE.allCourses.filter(c => {
        const matches = !search ||
            (c.subjectCode || '').toLowerCase().includes(search) ||
            (c.subjectName || '').toLowerCase().includes(search);

        const matchesYear = !year || (c.subjectCode || '').startsWith(year);

        return matches && matchesYear;
    });

    displayCoursesGrid(filtered);
    preloadUnitCounts(filtered);
}

function updateSelectedCourses() {
    const checkboxes = document.querySelectorAll('.course-checkbox:checked');
    ADVANCED_STATE.selectedCourses = Array.from(checkboxes).map(cb => cb.value);

    document.getElementById('selectedCount').textContent = ADVANCED_STATE.selectedCourses.length;

    const batchActions = document.getElementById('batchActions');
    if (ADVANCED_STATE.selectedCourses.length > 0) {
        batchActions.style.display = 'block';
        document.getElementById('selectedInfo').textContent =
            `${ADVANCED_STATE.selectedCourses.length} course(s) selected`;
    } else {
        batchActions.style.display = 'none';
    }
}

function selectAllVisible() {
    document.querySelectorAll('.course-checkbox:not(:checked)').forEach(cb => {
        cb.checked = true;
    });
    updateSelectedCourses();
}

function clearAllSelection() {
    document.querySelectorAll('.course-checkbox:checked').forEach(cb => {
        cb.checked = false;
    });
    updateSelectedCourses();
}

function selectSingleCourse(code, btn) {
    const checkbox = btn.closest('.course-card').querySelector('.course-checkbox');
    checkbox.checked = !checkbox.checked;
    updateSelectedCourses();
}

// ============================================
// BATCH DOWNLOAD
// ============================================

async function downloadSelectedBatch() {
    if (ADVANCED_STATE.selectedCourses.length === 0) {
        alert('No courses selected');
        return;
    }

    document.getElementById('courseSection').style.opacity = '0.5';
    document.getElementById('resourceSection').classList.remove('hidden');
    document.getElementById('resourceSection').style.opacity = '1';

    await loadResourcesForCourse(ADVANCED_STATE.selectedCourses[0]);
}

async function loadResourcesForCourse(courseCode) {
    try {
        const response = await fetch(`/api/courses/${courseCode}`);
        const data = await response.json();

        if (data.success) {
            const resources = data.resource_types || [];
            const units = Array.isArray(data.units) ? data.units : [];
            ADVANCED_STATE.selectedUnitsByCourse[courseCode] = units;

            const grid = document.getElementById('resourcesGrid');

            grid.innerHTML = resources.map((resource) => `
                <label class="resource-item">
                    <input type="checkbox" class="resource-checkbox" value="${resource}" checked>
                    <span class="resource-name">${resource}</span>
                </label>
            `).join('');

            ADVANCED_STATE.selectedResources = resources.slice();
            ADVANCED_STATE.selectedResourceNames = resources.slice();
        }
    } catch (err) {
        console.error('Error loading resources:', err);
    }
}

function selectAllResources() {
    document.querySelectorAll('.resource-checkbox').forEach(cb => {
        cb.checked = true;
    });
    updateSelectedResources();
}

function updateSelectedResources() {
    const checkboxes = document.querySelectorAll('.resource-checkbox:checked');
    ADVANCED_STATE.selectedResources = Array.from(checkboxes).map(cb => cb.value);
    ADVANCED_STATE.selectedResourceNames = ADVANCED_STATE.selectedResources.slice();
}

// ============================================
// DOWNLOAD MANAGEMENT
// ============================================

async function proceedToDownload() {
    updateSelectedResources();

    if (ADVANCED_STATE.selectedCourses.length === 0) {
        alert('No courses selected');
        return;
    }

    for (const code of ADVANCED_STATE.selectedCourses) {
        if (!ADVANCED_STATE.selectedUnitsByCourse[code]) {
            await loadResourcesForCourse(code);
        }
    }

    ADVANCED_STATE.downloadQueue = ADVANCED_STATE.selectedCourses.map(courseCode => ({
        courseCode: courseCode,
        units: ADVANCED_STATE.selectedUnitsByCourse[courseCode] || ADVANCED_STATE.courseUnitsCache[courseCode] || [],
        resources: ADVANCED_STATE.selectedResourceNames
    }));

    document.getElementById('resourceSection').classList.add('hidden');
    document.getElementById('downloadSection').classList.remove('hidden');

    ADVANCED_STATE.isDownloading = true;
    ADVANCED_STATE.downloadStats.total = ADVANCED_STATE.downloadQueue.length;
    ADVANCED_STATE.downloadStats.startTime = Date.now();

    startBatchDownload();
}

async function startBatchDownload() {
    while (ADVANCED_STATE.downloadQueue.length > 0 && ADVANCED_STATE.isDownloading) {
        const download = ADVANCED_STATE.downloadQueue.shift();
        await downloadCourse(download);
        updateProgressBars();
    }

    if (ADVANCED_STATE.isDownloading) {
        completeDownload();
    }
}

async function downloadCourse(downloadItem) {
    ADVANCED_STATE.currentDownload = downloadItem;

    document.getElementById('currentCourseName').textContent = downloadItem.courseCode;
    document.getElementById('downloadInfo').innerHTML = `
        <p>Downloading: <strong>${downloadItem.courseCode}</strong></p>
        <p>Units: ${downloadItem.units.length} | Resources: ${downloadItem.resources.length}</p>
    `;

    addLogEntry(`Starting download for ${downloadItem.courseCode}...`);

    try {
        const response = await fetch('/api/download/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                course_code: downloadItem.courseCode,
                units: downloadItem.units,
                resources: downloadItem.resources
            })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            await pollDownloadProgress();
            ADVANCED_STATE.downloadStats.completed++;
            addLogEntry(`Completed: ${downloadItem.courseCode}`);
        } else {
            ADVANCED_STATE.downloadStats.failed++;
            addLogEntry(`Failed: ${downloadItem.courseCode} - ${data.error || 'unknown error'}`);
        }
    } catch (err) {
        ADVANCED_STATE.downloadStats.failed++;
        addLogEntry(`Failed: ${downloadItem.courseCode} - ${err.message}`);
    }
}

async function pollDownloadProgress() {
    return new Promise((resolve) => {
        const checkProgress = setInterval(async () => {
            try {
                const response = await fetch('/api/download/status');
                const data = await response.json();

                if (data.status === 'completed' || data.status === 'failed' || data.status === 'cancelled') {
                    clearInterval(checkProgress);
                    resolve();
                }

                if (typeof data.progress === 'number') {
                    document.getElementById('courseFill').style.width = data.progress + '%';
                    document.getElementById('coursePercent').textContent = data.progress + '%';
                }

                if (data.current_file) {
                    document.getElementById('currentFile').textContent = `File: ${data.current_file}`;
                    document.getElementById('downloadStats').textContent =
                        `Downloaded: ${data.downloaded_files || 0} / ${data.total_files || 0}`;
                }
            } catch (err) {
                console.error('Progress check error:', err);
            }
        }, 500);
    });
}

function updateProgressBars() {
    const totalDownloads = ADVANCED_STATE.downloadStats.total || 1;
    const completed = ADVANCED_STATE.downloadStats.completed;
    const percent = (completed / totalDownloads) * 100;

    document.getElementById('overallFill').style.width = percent + '%';
    document.getElementById('overallPercent').textContent = Math.round(percent) + '%';
}

function addLogEntry(message) {
    const log = document.getElementById('downloadLog');
    const entry = document.createElement('p');
    entry.className = 'log-entry';
    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    log.appendChild(entry);
    log.scrollTop = log.scrollHeight;
}

function pauseDownload() {
    ADVANCED_STATE.isDownloading = false;
    document.getElementById('pauseBtn').style.display = 'none';
    document.getElementById('resumeBtn').style.display = 'inline';
    updateStatusBadge('Paused');
}

function resumeDownload() {
    ADVANCED_STATE.isDownloading = true;
    document.getElementById('pauseBtn').style.display = 'inline';
    document.getElementById('resumeBtn').style.display = 'none';
    updateStatusBadge('Downloading');
    startBatchDownload();
}

function cancelDownload() {
    if (confirm('Cancel current download?')) {
        ADVANCED_STATE.isDownloading = false;
        ADVANCED_STATE.downloadQueue = [];
        fetch('/api/download/cancel', { method: 'POST' }).catch(() => {});
        goHome();
    }
}

function completeDownload() {
    ADVANCED_STATE.isDownloading = false;
    document.getElementById('pauseBtn').style.display = 'none';
    document.getElementById('cancelBtn').style.display = 'none';
    document.getElementById('completeBtn').style.display = 'inline';

    addLogEntry(`All downloads completed (${ADVANCED_STATE.downloadStats.completed}/${ADVANCED_STATE.downloadStats.total})`);
    updateStatusBadge('Completed');

    if (document.getElementById('autoOpenFolder').checked) {
        addLogEntry('Downloads are available in the downloads folder.');
    }
}

function goHome() {
    location.reload();
}

// ============================================
// UI UPDATES
// ============================================

function updateStatusBadge(status) {
    const badge = document.getElementById('statusBadge');
    badge.textContent = status;
    badge.className = `stat-value status ${status.toLowerCase()}`;
}

function updateUI() {
    updateStatusBadge(ADVANCED_STATE.isLoggedIn ? 'Ready' : 'Login Required');
}

// ============================================
// AUTO UPDATES & CHECKS
// ============================================

function setupAutoUpdates() {
    setInterval(checkConnectionStatus, 5000);
}

async function checkConnectionStatus() {
    try {
        await fetch('/api/health');
        document.getElementById('connectionStatus').textContent = 'Connected';
        document.getElementById('connectionStatus').style.color = '#4ade80';
    } catch (err) {
        document.getElementById('connectionStatus').textContent = 'Offline';
        document.getElementById('connectionStatus').style.color = '#ef4444';
    }
}

async function checkLoginStatus() {
    try {
        const response = await fetch('/api/health');
        if (!response.ok) return null;
        return await response.json();
    } catch {
        return null;
    }
}

// ============================================
// AUTO MODE
// ============================================

function startAutoMode() {
    console.log('Starting auto-mode...');
    updateStatusBadge('Auto Mode Active');
}

function setupEventListeners() {
    document.getElementById('courseSearch').addEventListener('input', filterCourses);
}

function toggleLoginForm() {
    const form = document.getElementById('loginFormDiv');
    form.classList.toggle('hidden');
}
