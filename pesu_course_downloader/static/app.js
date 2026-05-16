/* ============================================
   PESU ACADEMY COURSE DOWNLOADER - APP.JS
   Frontend Logic & State Management
   ============================================ */

/* ============================================
   GLOBAL STATE
   ============================================ */

const STATE = {
    currentStep: 1,
    totalSteps: 4,
    selectedCourse: null,
    selectedUnits: [],
    selectedResources: [],
    currentPage: 1,
    searchQuery: '',
    yearFilter: '',
    isLoggedIn: false,
    isDownloading: false,
};

let searchTimeout;
let statusCheckInterval;

/* ============================================
   INITIALIZATION
   ============================================ */

document.addEventListener('DOMContentLoaded', initializeApp);

function initializeApp() {
    console.log('ðŸš€ App initializing...');
    setupEventListeners();
    updateUI();
    attemptAutoLogin();
    console.log('âœ… App initialized');
}

function setupEventListeners() {
    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
}

function handleKeyboardShortcuts(e) {
    if (e.key === 'ArrowRight') nextStep();
    if (e.key === 'ArrowLeft') prevStep();
}

/* ============================================
   STEP NAVIGATION
   ============================================ */

function goToStep(step) {
    if (step < 1 || step > STATE.totalSteps) return;
    
    // Disable clicking on future steps
    if (step > STATE.currentStep + 1) return;
    
    STATE.currentStep = step;
    updateUI();
}

async function nextStep() {
    if (!validateCurrentStep()) return;

    if (STATE.currentStep === STATE.totalSteps) {
        await handleFinishAction();
        return;
    }
    
    if (STATE.currentStep < STATE.totalSteps) {
        if (STATE.currentStep === 1) {
            // After login, load courses
            loadCourses();
        } else if (STATE.currentStep === 2) {
            // After course selection, load course details
            loadCourseDetails();
        }
        
        STATE.currentStep += 1;
        updateUI();
    }
}

function prevStep() {
    if (STATE.currentStep > 1) {
        STATE.currentStep -= 1;
        updateUI();
    }
}

/* ============================================
   VALIDATION
   ============================================ */

function validateCurrentStep() {
    const step = STATE.currentStep;
    
    if (step === 1) {
        // Wait for login
        return STATE.isLoggedIn;
    }
    
    if (step === 2 && !STATE.selectedCourse) {
        showStatusMessage('login-status', 'Please select a course', 'error');
        return false;
    }
    
    if (step === 3) {
        const unitsCount = document.querySelectorAll('.units-list input[type="checkbox"]:checked').length;
        const resourcesCount = document.querySelectorAll('.resources-list input[type="checkbox"]:checked').length;
        
        if (unitsCount === 0 || resourcesCount === 0) {
            showStatusMessage('selection-summary', 'Please select at least one unit and one resource', 'error');
            return false;
        }
    }
    
    return true;
}

/* ============================================
   LOGIN
   ============================================ */

async function performLogin() {
    const btn = document.getElementById('login-btn');
    const statusEl = document.getElementById('login-status');
    
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="btn-icon">â³</span> Logging in...';
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Login failed');
        }
        
        STATE.isLoggedIn = true;
        showStatusMessage('login-status', 'âœ… Login successful!', 'success');
        
        // Enable next button
        document.getElementById('next-btn').disabled = false;
        
        // Auto-advance after 1.5 seconds
        setTimeout(() => {
            nextStep();
        }, 1500);
        
    } catch (error) {
        console.error('Login error:', error);
        showStatusMessage('login-status', `âŒ ${error.message}`, 'error');
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

async function attemptAutoLogin() {
    const statusEl = document.getElementById('login-status');
    if (statusEl) {
        showStatusMessage('login-status', 'Trying auto-login...', 'info');
    }
    await performLogin();
}

/* ============================================
   COURSES MANAGEMENT
   ============================================ */

async function loadCourses() {
    const container = document.getElementById('courses-list');
    const search = document.getElementById('course-search')?.value || '';
    const year = document.getElementById('year-filter')?.value || '';
    
    STATE.searchQuery = search;
    STATE.yearFilter = year;
    STATE.currentPage = 1;
    
    container.innerHTML = `
        <div class="loading-spinner" style="grid-column: 1/-1;">
            <div class="spinner"></div>
            <p>Loading courses...</p>
        </div>
    `;
    
    try {
        const params = new URLSearchParams({
            page: STATE.currentPage,
            search: search,
            year: year
        });
        
        const response = await fetch(`/api/courses?${params}`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to load courses');
        }
        
        // Update year filter options
        updateYearFilter(data.available_years);
        
        // Display courses
        displayCourses(data.courses);
        
        // Update pagination
        updatePagination(data.page, data.total_pages);
        
    } catch (error) {
        console.error('Course loading error:', error);
        container.innerHTML = `
            <div class="loading-spinner" style="grid-column: 1/-1;">
                <p style="color: var(--color-danger);">âŒ ${error.message}</p>
            </div>
        `;
    }
}

function displayCourses(courses) {
    const container = document.getElementById('courses-list');
    
    if (courses.length === 0) {
        container.innerHTML = `
            <div class="loading-spinner" style="grid-column: 1/-1;">
                <p>No courses found</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = courses.map(course => {
        // Handle both formats: {code, name} and {subjectCode, subjectName, id}
        const code = course.code || course.subjectCode || course.id || '';
        const name = course.name || course.subjectName || '';
        const inferredYear = inferYearFromCode(code);
        const isSelected = STATE.selectedCourse?.code === code || STATE.selectedCourse?.subjectCode === code;
        
        return `
            <div class="course-card ${isSelected ? 'selected' : ''}" 
                 onclick="selectCourse('${escapeHtml(code)}', '${escapeHtml(name)}', '${escapeHtml(course.id || '')}', event)">
                <div class="course-code">${escapeHtml(code)}</div>
                <div class="course-name">${escapeHtml(name)}</div>
                <div class="course-info">ðŸ“š Click to view units</div>
                <div class="course-info">ðŸ“… ${escapeHtml(course.year || inferredYear)}</div>
                ${course.description ? `<div class="course-info">${escapeHtml(course.description.substring(0, 50))}...</div>` : ''}
            </div>
        `;
    }).join('');

    // Load unit counts asynchronously for visible cards
    loadVisibleUnitCounts(courses);
    
    // Re-highlight selected course if exists
    if (STATE.selectedCourse) {
        const cards = document.querySelectorAll('.course-card');
        cards.forEach(card => {
            if (card.textContent.includes(STATE.selectedCourse.code) || 
                card.textContent.includes(STATE.selectedCourse.name)) {
                card.classList.add('selected');
            }
        });
    }
}

async function selectCourse(code, name, id, clickEvent) {
    const stableId = id || code;
    STATE.selectedCourse = { code, name, id: stableId };
    
    // Update UI
    const cards = document.querySelectorAll('.course-card');
    cards.forEach(card => card.classList.remove('selected'));
    
    if (clickEvent && clickEvent.currentTarget) {
        clickEvent.currentTarget.classList.add('selected');
    }
    
    // Show selected info
    const selectedInfo = document.getElementById('selected-course-info');
    document.getElementById('selected-course-name').textContent = name;
    selectedInfo.style.display = 'block';
    
    // Enable next button
    document.getElementById('next-btn').disabled = false;

    // Open units/resource selection immediately on click.
    await openCourseResources();
}

function inferYearFromCode(code) {
    const value = String(code || '').trim();
    if (!value) return 'Unknown';
    if (value.startsWith('UE') && value.length >= 4) return value.slice(0, 4);
    if (/^\d{2}/.test(value)) return value.slice(0, 2);
    return 'Unknown';
}

async function loadVisibleUnitCounts(courses) {
    // Disabled: fetching unit counts for every card hammers the PESU API
    // and causes the UI to freeze. Units are loaded when the user clicks a course.
}

function updateYearFilter(years) {
    const yearSelect = document.getElementById('year-filter');
    if (!yearSelect) return;
    
    const currentValue = yearSelect.value;
    
    yearSelect.innerHTML = `
        <option value="">All Years</option>
        ${years.map(year => `
            <option value="${year}">${escapeHtml(year)}</option>
        `).join('')}
    `;
    
    yearSelect.value = currentValue;
}

function updatePagination(currentPage, totalPages) {
    const paginationDiv = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        paginationDiv.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Previous button
    if (currentPage > 1) {
        html += `<button class="pagination-btn" onclick="goToPage(${currentPage - 1})">â† Previous</button>`;
    }
    
    // Page numbers
    for (let i = Math.max(1, currentPage - 1); i <= Math.min(totalPages, currentPage + 1); i++) {
        html += `<button class="pagination-btn ${i === currentPage ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
    }
    
    // Next button
    if (currentPage < totalPages) {
        html += `<button class="pagination-btn" onclick="goToPage(${currentPage + 1})">Next â†’</button>`;
    }
    
    paginationDiv.innerHTML = html;
}

function goToPage(page) {
    STATE.currentPage = page;
    loadCourses();
}


function debounceSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(loadCourses, 300);
}

/* ============================================
   COURSE DETAILS
   ============================================ */

async function loadCourseDetails() {
    if (!STATE.selectedCourse) return;
    
    const container = document.getElementById('units-list');
    
    container.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner"></div>
            <p>Loading course details...</p>
        </div>
    `;
    
    try {
        const courseKey = STATE.selectedCourse.id || STATE.selectedCourse.code;
        const response = await fetch(`/api/courses/${courseKey}`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to load course details');
        }
        
        // Pass unit_objects instead of units to get the nested classes
        displayUnits(data.unit_objects);
        return true;

    } catch (error) {
        console.error('Course details error:', error);
        container.innerHTML = `
            <p style="color: var(--color-danger);">âŒ ${error.message}</p>
        `;
        return false;
    }
}

async function openCourseResources() {
    if (!STATE.selectedCourse) return;
    const loaded = await loadCourseDetails();
    if (loaded) {
        STATE.currentStep = 3;
        updateUI();
    }
}

async function handleFinishAction() {
    try {
        const statusResp = await fetch('/api/download/status');
        const statusData = await statusResp.json();
        const alreadyDownloaded = statusData.status === 'completed' && (statusData.downloaded_files || 0) > 0;

        if (alreadyDownloaded) {
            await openDownloadedFolderIfAvailable();
            goToCourseSelection();
            return;
        }

        const shouldDownload = confirm('You forgot to download. Do you want to download now? Click Cancel to go back to Course Selection.');
        if (!shouldDownload) {
            goToCourseSelection();
            return;
        }

        const started = await startDownload();
        if (!started) return;

        const finalStatus = await waitForDownloadToFinish();
        if (finalStatus && finalStatus.status === 'completed' && (finalStatus.downloaded_files || 0) > 0) {
            await openDownloadedFolderIfAvailable();
            goToCourseSelection();
        } else if (finalStatus && finalStatus.error_message) {
            showDownloadMessage(`Download failed: ${finalStatus.error_message}`, 'error');
        }
    } catch (error) {
        console.error('Finish action error:', error);
        showDownloadMessage(`Finish action failed: ${error.message}`, 'error');
    }
}

async function waitForDownloadToFinish() {
    for (let i = 0; i < 240; i++) {
        await new Promise(resolve => setTimeout(resolve, 500));
        try {
            const response = await fetch('/api/download/status');
            const progress = await response.json();
            updateProgressUI(progress);
            if (['completed', 'failed', 'cancelled'].includes(progress.status)) {
                return progress;
            }
        } catch (error) {
            console.error('Wait download status error:', error);
        }
    }
    return null;
}

async function openDownloadedFolderIfAvailable() {
    try {
        await fetch('/api/download/open-folder', { method: 'POST' });
    } catch (error) {
        console.error('Open folder error:', error);
    }
}

function goToCourseSelection() {
    STATE.currentStep = 2;
    updateUI();
    loadCourses();
}

function displayUnits(units) {
    const container = document.getElementById('units-list');
    
    if (!units || units.length === 0) {
        container.innerHTML = '<p>No units available</p>';
        return;
    }
    
    let html = '';
    
    units.forEach(unit => {
        html += `<div class="unit-group" style="margin-bottom: 15px; background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px;">`;
        html += `<h4 style="margin-top: 0; margin-bottom: 10px; font-size: 0.95rem; color: var(--color-primary-light);">${escapeHtml(unit.name)}</h4>`;
        
        if (!unit.classes || unit.classes.length === 0) {
            html += `<p style="font-size: 0.85rem; color: var(--color-text-muted); margin: 0;">No topics available</p>`;
        } else {
            unit.classes.forEach(cls => {
                const val = `${escapeHtml(unit.id)}|${escapeHtml(cls.id)}|${escapeHtml(unit.name)}|${escapeHtml(cls.name)}`;
                html += `
                    <label class="checkbox-item" style="margin-left: 10px;">
                        <input type="checkbox" name="unit" value="${val}" onchange="updateSelectionSummary()">
                        <span class="checkbox-label" style="font-size: 0.85rem;">ðŸ“„ ${escapeHtml(cls.name)}</span>
                    </label>
                `;
            });
        }
        
        html += `</div>`;
    });
    
    container.innerHTML = html;
    
    // Set up resource checkboxes too
    document.querySelectorAll('input[name="resource"]').forEach(el => {
        el.onchange = updateSelectionSummary;
    });
    
    updateSelectionSummary();
}

function updateSelectionSummary() {
    const unitsCount = document.querySelectorAll('input[name="unit"]:checked').length;
    const resourcesCount = document.querySelectorAll('input[name="resource"]:checked').length;
    
    STATE.selectedUnits = Array.from(document.querySelectorAll('input[name="unit"]:checked')).map(el => el.value);
    STATE.selectedResources = Array.from(document.querySelectorAll('input[name="resource"]:checked')).map(el => el.value);
    
    const summary = document.getElementById('selection-summary');
    if (unitsCount > 0 && resourcesCount > 0) {
        summary.style.display = 'block';
        document.getElementById('units-count').textContent = unitsCount;
        document.getElementById('resources-count').textContent = resourcesCount;
        
        document.getElementById('next-btn').disabled = false;
    } else {
        summary.style.display = 'none';
        document.getElementById('next-btn').disabled = true;
    }
}

/* ============================================
   DOWNLOAD
   ============================================ */

async function startDownload() {
    if (window.location.hostname.includes('vercel.app')) {
        return startVercelZipDownload();
    }

    STATE.isDownloading = true;
    document.getElementById('start-download-btn').style.display = 'none';
    document.getElementById('cancel-download-btn').style.display = 'block';
    
    try {
        const response = await fetch('/api/download/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                course_code: STATE.selectedCourse.id || STATE.selectedCourse.code,
                classes: STATE.selectedUnits,
                resources: STATE.selectedResources
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to start download');
        }
        
        // Start polling for progress
        statusCheckInterval = setInterval(checkDownloadProgress, 500);
        return true;
        
    } catch (error) {
        console.error('Download start error:', error);
        showDownloadMessage(`âŒ ${error.message}`, 'error');
        STATE.isDownloading = false;
        document.getElementById('cancel-download-btn').style.display = 'none';
        document.getElementById('start-download-btn').style.display = 'block';
        return false;
    }
}

async function startVercelZipDownload() {
    try {
        const response = await fetch('/api/download/zip', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                course_code: STATE.selectedCourse.id || STATE.selectedCourse.code,
                classes: STATE.selectedUnits,
                resources: STATE.selectedResources
            })
        });

        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.error || 'ZIP download failed');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'pesu_resources.zip';
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        showDownloadMessage('ZIP download started successfully.', 'success');
        return true;
    } catch (error) {
        showDownloadMessage(`Download failed: ${error.message}`, 'error');
        return false;
    }
}

async function checkDownloadProgress() {
    try {
        const response = await fetch('/api/download/status');
        const progress = await response.json();
        
        // Update progress UI
        updateProgressUI(progress);
        
        // Stop polling if download is done
        if (progress.status === 'completed' || progress.status === 'failed' || progress.status === 'cancelled') {
            clearInterval(statusCheckInterval);
            STATE.isDownloading = false;
            document.getElementById('cancel-download-btn').style.display = 'none';
            document.getElementById('start-download-btn').style.display = 'block';
        }
        
    } catch (error) {
        console.error('Progress check error:', error);
    }
}

function updateProgressUI(progress) {
    // Update status
    const statusMap = {
        'idle': 'â¸ï¸ Idle',
        'starting': 'ðŸš€ Starting...',
        'downloading': 'â¬‡ï¸ Downloading',
        'completed': 'âœ… Completed',
        'failed': 'âŒ Failed',
        'cancelled': 'ðŸ›‘ Cancelled'
    };
    
    document.getElementById('download-status').textContent = statusMap[progress.status] || progress.status;
    
    // Update file counts
    document.getElementById('downloaded-count').textContent = progress.downloaded_files;
    document.getElementById('total-count').textContent = progress.total_files;
    
    // Update progress bar
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    progressFill.style.width = progress.progress + '%';
    progressText.textContent = progress.progress + '%';
    
    // Update current file
    const currentFileInfo = document.getElementById('current-file-info');
    if (progress.current_file) {
        document.getElementById('current-file-name').textContent = progress.current_file;
        currentFileInfo.style.display = 'block';
    }
    
    // Update elapsed time
    if (progress.start_time) {
        document.getElementById('elapsed-info').style.display = 'flex';
        const elapsed = Math.floor((Date.now() - new Date(progress.start_time)) / 1000);
        document.getElementById('elapsed-time').textContent = formatTime(elapsed);
    }
    
    // Show messages
    if (progress.success_message) {
        showDownloadMessage(progress.success_message, 'success');
    }
    if (progress.error_message) {
        showDownloadMessage(progress.error_message, 'error');
    }
}

async function cancelDownload() {
    try {
        const response = await fetch('/api/download/cancel', { method: 'POST' });
        const data = await response.json();
        
        if (response.ok) {
            clearInterval(statusCheckInterval);
            STATE.isDownloading = false;
            showDownloadMessage('ðŸ›‘ Download cancelled', 'info');
        }
    } catch (error) {
        console.error('Cancel error:', error);
    }
}

function showDownloadMessage(message, type) {
    const messageEl = document.getElementById('download-message');
    messageEl.textContent = message;
    messageEl.className = `status-message ${type}`;
}

function showViewMessage(message, type) {
    const messageEl = document.getElementById('view-message');
    if (!messageEl) return;
    messageEl.textContent = message;
    messageEl.className = `status-message ${type}`;
}

async function viewResources() {
    const resultBox = document.getElementById('view-results');
    if (!STATE.selectedCourse) {
        showViewMessage('Please select a course first.', 'error');
        return;
    }
    if (!STATE.selectedUnits.length || !STATE.selectedResources.length) {
        showViewMessage('Please select at least one unit and one resource first.', 'error');
        return;
    }

    if (resultBox) {
        resultBox.innerHTML = '<p>Loading view links...</p>';
    }
    showViewMessage('', 'info');

    try {
        const response = await fetch('/api/resources/view', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                course_code: STATE.selectedCourse.id || STATE.selectedCourse.code,
                classes: STATE.selectedUnits,
                resources: STATE.selectedResources
            })
        });
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Failed to load view links');
        }

        renderViewResults(data.items || []);
        showViewMessage(`Found ${data.total_items || 0} viewable items.`, 'success');
    } catch (error) {
        if (resultBox) resultBox.innerHTML = '';
        showViewMessage(`View failed: ${error.message}`, 'error');
    }
}

function renderViewResults(items) {
    const resultBox = document.getElementById('view-results');
    if (!resultBox) return;

    if (!items.length) {
        resultBox.innerHTML = '<p>No viewable files found for selected filters.</p>';
        return;
    }

    const rows = items.map((item, idx) => {
        const label = `${item.unit_name} - ${item.class_name} (${item.resource_name})`;
        return `
            <li style="margin: 6px 0;">
                <a href="${escapeHtml(item.view_url)}" target="_blank" rel="noopener noreferrer">
                    Open ${idx + 1}: ${escapeHtml(label)}
                </a>
            </li>
        `;
    }).join('');

    resultBox.innerHTML = `
        <div style="max-height: 260px; overflow:auto; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; padding: 10px;">
            <ul style="margin:0; padding-left: 18px;">${rows}</ul>
        </div>
    `;
}

/* ============================================
   UI UPDATES
   ============================================ */

function updateUI() {
    // Update step indicators
    for (let i = 1; i <= STATE.totalSteps; i++) {
        const stepEl = document.getElementById(`step-${i}`);
        const panelEl = document.getElementById(`panel-${i}`);
        
        if (stepEl) {
            if (i < STATE.currentStep) {
                stepEl.classList.add('active');
            } else if (i === STATE.currentStep) {
                stepEl.classList.add('active');
            } else {
                stepEl.classList.remove('active');
            }
        }
        
        if (panelEl) {
            if (i === STATE.currentStep) {
                panelEl.classList.add('active');
            } else {
                panelEl.classList.remove('active');
            }
        }
    }
    
    // Update navigation buttons
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    
    if (prevBtn) {
        prevBtn.style.display = STATE.currentStep > 1 ? 'inline-flex' : 'none';
    }
    
    if (nextBtn) {
        nextBtn.textContent = STATE.currentStep === STATE.totalSteps ? 'âœ… Finish' : 'â†’ Next';
    }
}

function showStatusMessage(elementId, message, type) {
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = message;
        el.className = `status-message ${type}`;
    }
}

/* ============================================
   UTILITY FUNCTIONS
   ============================================ */

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }
    return `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

/* ============================================
   HEALTH CHECK
   ============================================ */

async function checkAppHealth() {
    try {
        const response = await fetch('/api/health');
        if (response.ok) {
            console.log('âœ… App is healthy');
            return true;
        }
    } catch (error) {
        console.error('âŒ Health check failed:', error);
        return false;
    }
}

// Check health on load
window.addEventListener('load', checkAppHealth);

console.log('ðŸ“¦ App.js loaded');

