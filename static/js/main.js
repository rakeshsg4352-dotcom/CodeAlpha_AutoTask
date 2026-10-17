/**
 * AutoTask - Frontend JavaScript Controller
 * Handles responsive sidebar, AJAX task execution, dynamic DOM updates,
 * file drag-and-drop, and toast notifications.
 */

document.addEventListener('DOMContentLoaded', () => {
    initSidebar();
    initToasts();
    initFileUploads();
    initAjaxForms();
});

// ==============================================================================
// 1. SIDEBAR TOGGLE FOR RESPONSIVE NAVIGATION
// ==============================================================================

function initSidebar() {
    const toggleBtn = document.getElementById('mobileMenuToggle');
    const sidebar = document.querySelector('.sidebar');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            sidebar.classList.toggle('open');
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 992 && sidebar.classList.contains('open')) {
                if (!sidebar.contains(e.target) && e.target !== toggleBtn) {
                    sidebar.classList.remove('open');
                }
            }
        });
    }
}

// ==============================================================================
// 2. CSRF TOKEN HELPER
// ==============================================================================

function getCsrfToken() {
    const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (input) return input.value;

    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue || '';
}

// ==============================================================================
// 3. TOAST NOTIFICATIONS
// ==============================================================================

function initToasts() {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
}

function showToast(message, type = 'info') {
    const container = document.querySelector('.toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // Icon based on type
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'danger') icon = '⚠️';

    toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(50px)';
        setTimeout(() => toast.remove(), 300);
    }, 4500);
}

function escapeHtml(string) {
    const div = document.createElement('div');
    div.innerText = string;
    return div.innerHTML;
}

// ==============================================================================
// 4. FILE UPLOAD & DROPZONE HANDLING
// ==============================================================================

function initFileUploads() {
    const dropzone = document.getElementById('uploadDropzone');
    const fileInput = document.getElementById('id_file') || document.querySelector('input[type="file"]');
    const nameDisplay = document.getElementById('selectedFileName');

    if (!dropzone || !fileInput) return;

    dropzone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            updateFileLabel(fileInput.files[0].name);
        }
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            updateFileLabel(files[0].name);
        }
    });

    function updateFileLabel(name) {
        if (nameDisplay) {
            nameDisplay.style.display = 'inline-block';
            nameDisplay.textContent = `Selected: ${name}`;
        }
    }
}

// ==============================================================================
// 5. AJAX TASK SUBMISSIONS
// ==============================================================================

function initAjaxForms() {
    // A. Move JPG Form
    const moveJpgForm = document.getElementById('moveJpgForm');
    if (moveJpgForm) {
        moveJpgForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = moveJpgForm.querySelector('button[type="submit"]');
            const resultBox = document.getElementById('moveResultBox');
            const loader = document.getElementById('moveLoader');

            setLoading(submitBtn, loader, true, 'Moving JPG Images...');

            const formData = new FormData(moveJpgForm);

            try {
                const response = await fetch(moveJpgForm.action, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json'
                    },
                    body: formData
                });

                const data = await response.json();
                setLoading(submitBtn, loader, false);

                if (data.success) {
                    showToast(data.message, 'success');
                    if (resultBox) {
                        resultBox.style.display = 'block';
                        resultBox.className = 'card alert-success';
                        
                        let filesListHtml = '';
                        if (data.moved_files && data.moved_files.length > 0) {
                            filesListHtml = `
                                <div style="margin-top: 14px; max-height: 200px; overflow-y: auto; background: #fff; padding: 12px; border-radius: 6px; border: 1px solid var(--border);">
                                    <strong style="display: block; margin-bottom: 6px; color: var(--text-main);">Moved Files:</strong>
                                    <ul style="padding-left: 20px; font-size: 13px; color: var(--text-muted);">
                                        ${data.moved_files.map(f => `<li>${escapeHtml(f.original)} &rarr; <strong>${escapeHtml(f.destination_name)}</strong></li>`).join('')}
                                    </ul>
                                </div>
                            `;
                        }

                        resultBox.innerHTML = `
                            <div style="display: flex; align-items: center; justify-content: space-between;">
                                <h4 style="font-weight: 700; color: var(--success-text);">Task Completed Successfully!</h4>
                                <a href="/history/${data.task_id}/" class="btn btn-sm btn-secondary">View Task #${data.task_id}</a>
                            </div>
                            <p style="margin-top: 8px;"><strong>${data.moved_count}</strong> images moved into <code>${escapeHtml(data.dest_folder)}</code>.</p>
                            ${filesListHtml}
                        `;
                    }
                } else {
                    showToast(data.error || 'Execution failed', 'danger');
                    if (resultBox) {
                        resultBox.style.display = 'block';
                        resultBox.className = 'card alert-danger';
                        resultBox.innerHTML = `<strong>Error:</strong> ${escapeHtml(data.error)}`;
                    }
                }
            } catch (err) {
                setLoading(submitBtn, loader, false);
                showToast('Network error or server unavailable', 'danger');
            }
        });
    }

    // B. Extract Emails Form
    const extractEmailsForm = document.getElementById('extractEmailsForm');
    if (extractEmailsForm) {
        extractEmailsForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = extractEmailsForm.querySelector('button[type="submit"]');
            const resultBox = document.getElementById('extractResultBox');
            const loader = document.getElementById('extractLoader');

            setLoading(submitBtn, loader, true, 'Extracting Email Addresses...');

            const formData = new FormData(extractEmailsForm);

            try {
                const response = await fetch(extractEmailsForm.action, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json'
                    },
                    body: formData
                });

                const data = await response.json();
                setLoading(submitBtn, loader, false);

                if (data.success) {
                    showToast(data.message, 'success');
                    if (resultBox) {
                        resultBox.style.display = 'block';
                        resultBox.className = 'card';

                        let tableRows = data.emails.map((email, idx) => `
                            <tr>
                                <td style="width: 50px; color: var(--text-muted);">${idx + 1}</td>
                                <td><code>${escapeHtml(email)}</code></td>
                                <td style="text-align: right;">
                                    <button class="btn btn-sm btn-outline" onclick="copyToClipboard('${escapeHtml(email)}')">Copy</button>
                                </td>
                            </tr>
                        `).join('');

                        resultBox.innerHTML = `
                            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; flex-wrap: wrap; gap: 10px;">
                                <div>
                                    <h4 style="font-weight: 700; color: var(--text-main);">Extracted ${data.unique_count} Unique Emails</h4>
                                    <span style="font-size: 12px; color: var(--text-muted);">Total found: ${data.total_found} (Duplicates removed)</span>
                                </div>
                                <div style="display: flex; gap: 8px;">
                                    <a href="${data.download_url}" class="btn btn-sm btn-success">📥 Download Output (.txt)</a>
                                    <a href="/history/${data.task_id}/" class="btn btn-sm btn-secondary">Task Details</a>
                                </div>
                            </div>
                            <div class="table-responsive" style="max-height: 280px; overflow-y: auto; border: 1px solid var(--border); border-radius: var(--radius-sm);">
                                <table class="table">
                                    <thead>
                                        <tr>
                                            <th>#</th>
                                            <th>Email Address</th>
                                            <th style="text-align: right;">Action</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${tableRows}
                                    </tbody>
                                </table>
                            </div>
                        `;
                    }
                } else {
                    showToast(data.error || 'Extraction failed', 'danger');
                    if (resultBox) {
                        resultBox.style.display = 'block';
                        resultBox.className = 'card alert-danger';
                        resultBox.innerHTML = `<strong>Error:</strong> ${escapeHtml(data.error)}`;
                    }
                }
            } catch (err) {
                setLoading(submitBtn, loader, false);
                showToast('Network error or server unavailable', 'danger');
            }
        });
    }

    // C. Scrape Webpage Title Form
    const scrapeTitleForm = document.getElementById('scrapeTitleForm');
    if (scrapeTitleForm) {
        scrapeTitleForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = scrapeTitleForm.querySelector('button[type="submit"]');
            const resultBox = document.getElementById('scrapeResultBox');
            const loader = document.getElementById('scrapeLoader');

            setLoading(submitBtn, loader, true, 'Connecting and Scraping Title...');

            const formData = new FormData(scrapeTitleForm);

            try {
                const response = await fetch(scrapeTitleForm.action, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json'
                    },
                    body: formData
                });

                const data = await response.json();
                setLoading(submitBtn, loader, false);

                if (data.success) {
                    showToast(data.message, 'success');
                    if (resultBox) {
                        resultBox.style.display = 'block';
                        resultBox.className = 'card';
                        resultBox.innerHTML = `
                            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; flex-wrap: wrap; gap: 10px;">
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <span class="badge badge-success">HTTP ${data.http_status} OK</span>
                                    <span style="font-size: 13px; color: var(--text-muted);">Public Webpage Scraped</span>
                                </div>
                                <div style="display: flex; gap: 8px;">
                                    <a href="${data.download_url}" class="btn btn-sm btn-success">📥 Download Title (.txt)</a>
                                    <a href="/history/${data.task_id}/" class="btn btn-sm btn-secondary">Task Details</a>
                                </div>
                            </div>
                            <div style="background: var(--bg-muted); padding: 18px; border-radius: var(--radius-md); border-left: 4px solid var(--purple);">
                                <span style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: var(--purple); letter-spacing: 0.5px;">Webpage &lt;title&gt;</span>
                                <h3 style="font-size: 18px; font-weight: 700; color: var(--text-main); margin-top: 6px;">${escapeHtml(data.title)}</h3>
                                <p style="font-size: 12.5px; color: var(--text-muted); margin-top: 8px;"><strong>URL:</strong> <code>${escapeHtml(data.final_url)}</code></p>
                            </div>
                        `;
                    }
                } else {
                    showToast(data.error || 'Scraping failed', 'danger');
                    if (resultBox) {
                        resultBox.style.display = 'block';
                        resultBox.className = 'card alert-danger';
                        resultBox.innerHTML = `<strong>Error:</strong> ${escapeHtml(data.error)}`;
                    }
                }
            } catch (err) {
                setLoading(submitBtn, loader, false);
                showToast('Network error or server unavailable', 'danger');
            }
        });
    }
}

// Helpers
function setLoading(button, loaderElement, isLoading, text = 'Processing...') {
    if (isLoading) {
        if (button) {
            button.disabled = true;
            button.dataset.origText = button.innerHTML;
            button.innerHTML = `<span class="spinner"></span> <span>${text}</span>`;
        }
        if (loaderElement) loaderElement.style.display = 'block';
    } else {
        if (button) {
            button.disabled = false;
            button.innerHTML = button.dataset.origText || 'Execute Automation';
        }
        if (loaderElement) loaderElement.style.display = 'none';
    }
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Unable to copy', 'danger');
    });
}
