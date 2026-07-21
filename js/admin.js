// Admin Frontend Logic

// Handle Login
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const spinner = document.getElementById('loginSpinner');
        const alertBox = document.getElementById('alertBox');
        
        spinner.classList.remove('d-none');
        
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                window.location.href = '/admin-dashboard';
            } else {
                alertBox.textContent = data.message || 'Login failed';
                alertBox.classList.remove('d-none');
            }
        } catch (error) {
            alertBox.textContent = 'Server error. Please try again.';
            alertBox.classList.remove('d-none');
        } finally {
            spinner.classList.add('d-none');
        }
    });
}

// Handle Logout
async function logout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
        window.location.href = '/admin';
    } catch (e) {
        console.error('Error logging out', e);
    }
}

// Show status message
function showStatus(message, isError = false) {
    const statusBox = document.getElementById('statusMessage');
    if (!statusBox) return;
    
    statusBox.textContent = message;
    statusBox.className = `alert alert-${isError ? 'danger' : 'success'} mb-4`;
    statusBox.classList.remove('d-none');
    
    setTimeout(() => {
        statusBox.classList.add('d-none');
    }, 3000);
}

// Load Dashboard Data
async function loadDashboardData() {
    try {
        const response = await fetch('/api/content');
        if (response.status === 401) {
            window.location.href = 'admin.html';
            return;
        }
        
        const resData = await response.json();
        if (resData.success) {
            const data = resData.data;
            
            // Populate text fields
            const fields = ['academic_year', 'current_term', 'about_intro', 'about_mission', 'about_vision', 'priest_description', 'headboy_name', 'headgirl_name'];
            fields.forEach(f => {
                if (document.getElementById(f)) document.getElementById(f).value = data[f] || '';
            });
            
            // Populate image previews
            const images = ['priest_image', 'hero_bg', 'about_image', 'headboy_image', 'headgirl_image'];
            images.forEach(img => {
                if (data[img] && document.getElementById('preview_' + img)) {
                    document.getElementById('preview_' + img).src = data[img];
                }
            });
            
            // Populate Gallery Grid
            const galleryGrid = document.getElementById('admin_gallery_grid');
            if (galleryGrid && data.gallery) {
                galleryGrid.innerHTML = '';
                if(data.gallery.length === 0) {
                    galleryGrid.innerHTML = '<div class="col-12 text-muted text-center py-3">No images in gallery yet.</div>';
                }
                data.gallery.forEach(item => {
                    galleryGrid.innerHTML += `
                        <div class="col-md-3">
                            <div class="position-relative border rounded p-2 bg-white shadow-sm h-100">
                                <img src="${item.image_path}" class="img-fluid rounded mb-2" style="height: 120px; width: 100%; object-fit: cover;">
                                <span class="badge bg-primary position-absolute top-0 start-0 m-3">${item.category}</span>
                                <h6 class="small fw-bold text-truncate">${item.title || 'Untitled'}</h6>
                                <button class="btn btn-sm btn-danger w-100 mt-2" onclick="deleteGalleryItem(${item.id})">Delete</button>
                            </div>
                        </div>
                    `;
                });
            }
        }
    } catch (error) {
        console.error('Error loading data', error);
    }
}

// Save All Settings
async function saveAllSettings() {
    const data = {
        academic_year: document.getElementById('academic_year')?.value,
        current_term: document.getElementById('current_term')?.value,
        about_intro: document.getElementById('about_intro')?.value,
        about_mission: document.getElementById('about_mission')?.value,
        about_vision: document.getElementById('about_vision')?.value,
        priest_description: document.getElementById('priest_description')?.value,
        headboy_name: document.getElementById('headboy_name')?.value,
        headgirl_name: document.getElementById('headgirl_name')?.value
    };
    
    try {
        const response = await fetch('/api/content', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        if (response.ok && result.success) {
            showStatus('Settings saved successfully!');
        } else {
            showStatus(result.message || 'Failed to save settings', true);
        }
    } catch (error) {
        showStatus('Server error', true);
    }
}

// Upload Gallery Image
async function uploadGalleryImage() {
    const input = document.getElementById('gallery_upload_input');
    const category = document.getElementById('gallery_category').value;
    const title = document.getElementById('gallery_title').value;
    
    if (!input.files || input.files.length === 0) {
        showStatus('Please select an image first', true);
        return;
    }
    
    const file = input.files[0];
    const formData = new FormData();
    formData.append('image', file);
    formData.append('key', 'gallery');
    formData.append('category', category);
    formData.append('title', title);
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();
        
        if (response.ok && result.success) {
            showStatus('Gallery image added successfully!');
            input.value = '';
            document.getElementById('gallery_title').value = '';
            loadDashboardData(); // Reload gallery
        } else {
            showStatus(result.message || 'Failed to add gallery image', true);
        }
    } catch (error) {
        showStatus('Server error during upload', true);
    }
}

// Delete Gallery Item
async function deleteGalleryItem(id) {
    if(!confirm("Are you sure you want to delete this image?")) return;
    
    try {
        const response = await fetch('/api/gallery/' + id, { method: 'DELETE' });
        const result = await response.json();
        if(response.ok && result.success) {
            showStatus('Image deleted');
            loadDashboardData();
        }
    } catch(e) {
        showStatus('Failed to delete', true);
    }
}

// Upload Image (General)
async function uploadImage(inputElement, key) {
    if (!inputElement.files || inputElement.files.length === 0) return;
    
    const file = inputElement.files[0];
    const formData = new FormData();
    formData.append('image', file);
    formData.append('key', key);
    
    const wrapper = inputElement.closest('.image-upload-wrapper');
    const progress = wrapper.querySelector('.upload-progress');
    const preview = wrapper.querySelector('img');
    
    progress.classList.remove('d-none');
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            // Update preview
            preview.src = result.path + '?t=' + new Date().getTime(); // cache busting
            showStatus('Image uploaded successfully!');
        } else {
            showStatus(result.message || 'Failed to upload image', true);
        }
    } catch (error) {
        showStatus('Server error during upload', true);
    } finally {
        progress.classList.add('d-none');
        inputElement.value = ''; // Reset input
    }
}

// ============================================================
// Messages & Admissions Inboxes
// ============================================================

async function loadMessages() {
    const container = document.getElementById('messages_list');
    if (!container) return;
    try {
        const res = await fetch('/api/messages');
        const data = await res.json();
        if (!data.success) { container.innerHTML = '<p class="text-danger">Failed to load messages.</p>'; return; }
        const msgs = data.data;
        if (msgs.length === 0) {
            container.innerHTML = '<p class="text-muted text-center py-3">No messages yet.</p>';
            return;
        }
        const unread = msgs.filter(m => !m.is_read).length;
        const badge = document.getElementById('msg_unread_badge');
        if (badge) { badge.textContent = unread; badge.style.display = unread > 0 ? 'inline-block' : 'none'; }

        container.innerHTML = msgs.map(m => `
            <div class="border rounded p-3 mb-3 ${m.is_read ? 'bg-white' : 'bg-light border-start border-success border-4'}">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong>${m.name || 'Unknown'}</strong>
                        <span class="text-muted small ms-2">&lt;${m.email || ''}&gt;</span>
                        ${!m.is_read ? '<span class="badge bg-success ms-2">New</span>' : ''}
                    </div>
                    <small class="text-muted">${m.submitted_at || ''}</small>
                </div>
                <div class="fw-semibold mt-1">${m.subject || 'No subject'}</div>
                <div class="text-muted mt-1 small">${m.message || ''}</div>
                ${!m.is_read ? `<button class="btn btn-sm btn-outline-secondary mt-2 rounded-pill" onclick="markMessageRead(${m.id})">Mark as Read</button>` : ''}
            </div>
        `).join('');
    } catch(e) {
        container.innerHTML = '<p class="text-danger">Error loading messages.</p>';
    }
}

async function markMessageRead(id) {
    await fetch('/api/messages/' + id + '/read', {method: 'POST'});
    loadMessages();
    fetchNotificationCount();
}

async function loadAdmissions() {
    const container = document.getElementById('admissions_list');
    if (!container) return;
    try {
        const res = await fetch('/api/admissions');
        const data = await res.json();
        if (!data.success) { container.innerHTML = '<p class="text-danger">Failed to load admissions.</p>'; return; }
        const apps = data.data;
        if (apps.length === 0) {
            container.innerHTML = '<p class="text-muted text-center py-3">No applications yet.</p>';
            return;
        }
        const unread = apps.filter(a => !a.is_read).length;
        const badge = document.getElementById('adm_unread_badge');
        if (badge) { badge.textContent = unread; badge.style.display = unread > 0 ? 'inline-block' : 'none'; }

        container.innerHTML = apps.map(a => `
            <div class="border rounded p-3 mb-3 ${a.is_read ? 'bg-white' : 'bg-light border-start border-warning border-4'}">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong>${a.student_name || 'Unknown'}</strong>
                        ${!a.is_read ? '<span class="badge bg-warning text-dark ms-2">New</span>' : ''}
                    </div>
                    <small class="text-muted">${a.submitted_at || ''}</small>
                </div>
                <div class="row mt-2 small text-muted">
                    <div class="col-sm-4"><b>Class:</b> ${a.class_applying || '-'}</div>
                    <div class="col-sm-4"><b>DOB:</b> ${a.date_of_birth || '-'}</div>
                    <div class="col-sm-4"><b>Gender:</b> ${a.gender || '-'}</div>
                    <div class="col-sm-4"><b>Parent:</b> ${a.parent_name || '-'}</div>
                    <div class="col-sm-4"><b>Phone:</b> ${a.parent_phone || '-'}</div>
                    <div class="col-sm-4"><b>Email:</b> ${a.parent_email || '-'}</div>
                    <div class="col-sm-12"><b>Address:</b> ${a.address || '-'}</div>
                </div>
                ${!a.is_read ? `<button class="btn btn-sm btn-outline-secondary mt-2 rounded-pill" onclick="markAdmissionRead(${a.id})">Mark as Read</button>` : ''}
            </div>
        `).join('');
    } catch(e) {
        container.innerHTML = '<p class="text-danger">Error loading admissions.</p>';
    }
}

async function markAdmissionRead(id) {
    await fetch('/api/admissions/' + id + '/read', {method: 'POST'});
    loadAdmissions();
    fetchNotificationCount();
}

// ============================================================
// Notification Badge (Bell Counter)
// ============================================================

async function fetchNotificationCount() {
    try {
        const res = await fetch('/api/notifications');
        const data = await res.json();
        if (!data.success) return;
        const badge = document.getElementById('notifBadge');
        if (badge) {
            if (data.total > 0) {
                badge.textContent = data.total;
                badge.classList.remove('d-none');
            } else {
                badge.classList.add('d-none');
            }
        }
    } catch(e) {}
}

async function loadNotifPanel() {
    const list = document.getElementById('notif_list');
    if (!list) return;
    try {
        const [msgRes, admRes] = await Promise.all([
            fetch('/api/messages'), fetch('/api/admissions')
        ]);
        const msgData = await msgRes.json();
        const admData = await admRes.json();
        const msgs = msgData.success ? msgData.data.filter(m => !m.is_read) : [];
        const apps = admData.success ? admData.data.filter(a => !a.is_read) : [];

        let html = '';
        msgs.forEach(m => {
            html += `<li class="list-group-item">
                <div class="d-flex gap-2 align-items-start">
                    <span class="text-success mt-1"><i class="fas fa-envelope"></i></span>
                    <div>
                        <div class="fw-semibold small">${m.name} sent a message</div>
                        <div class="text-muted" style="font-size:0.8rem;">${m.subject || ''}</div>
                        <div class="text-muted" style="font-size:0.75rem;">${m.submitted_at || ''}</div>
                    </div>
                </div></li>`;
        });
        apps.forEach(a => {
            html += `<li class="list-group-item">
                <div class="d-flex gap-2 align-items-start">
                    <span class="text-warning mt-1"><i class="fas fa-graduation-cap"></i></span>
                    <div>
                        <div class="fw-semibold small">${a.student_name} applied</div>
                        <div class="text-muted" style="font-size:0.8rem;">Class: ${a.class_applying || '-'}</div>
                        <div class="text-muted" style="font-size:0.75rem;">${a.submitted_at || ''}</div>
                    </div>
                </div></li>`;
        });
        list.innerHTML = html || '<li class="list-group-item text-center text-muted py-4">All caught up! No unread notifications.</li>';
    } catch(e) {
        list.innerHTML = '<li class="list-group-item text-danger">Failed to load notifications.</li>';
    }
}
