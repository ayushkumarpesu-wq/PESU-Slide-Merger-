import sys

def fix_app_js():
    with open("static/app.js", "r", encoding="utf-8") as f:
        content = f.read()

    missing_code = """
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
        const response = await fetch(`/api/courses/${STATE.selectedCourse.code}`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to load course details');
        }
        
        // Pass unit_objects instead of units to get the nested classes
        displayUnits(data.unit_objects);
        
    } catch (error) {
        console.error('Course details error:', error);
        container.innerHTML = `
            <p style="color: var(--color-danger);">❌ ${error.message}</p>
        `;
    }
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
                        <span class="checkbox-label" style="font-size: 0.85rem;">📄 ${escapeHtml(cls.name)}</span>
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
    STATE.isDownloading = true;
    document.getElementById('start-download-btn').style.display = 'none';
    document.getElementById('cancel-download-btn').style.display = 'block';
    
    try {
        const response = await fetch('/api/download/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                course_code: STATE.selectedCourse.code,
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
        
    } catch (error) {
        console.error('Download start error:', error);
        showDownloadMessage(`❌ ${error.message}`, 'error');
        STATE.isDownloading = false;
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
"""

    # Find where to insert
    target_str = "function updateProgressUI(progress) {"
    
    # Also clean up the loose updateProgressUI signature from line 361 if it's right after goToPage
    content = content.replace("function updateProgressUI(progress) {", missing_code + "\nfunction updateProgressUI(progress) {")
    
    # Write back
    with open("static/app.js", "w", encoding="utf-8") as f:
        f.write(content)
        
    print("Fixed app.js")

if __name__ == "__main__":
    fix_app_js()
