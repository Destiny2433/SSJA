// Admin Frontend Logic
// Preloader Logic
document.addEventListener('DOMContentLoaded', () => {
    const preloader = document.createElement('div');
    preloader.id = 'preloader';
    preloader.innerHTML = `
        <div class="loader-container">
            <div class="loader-circle">
                <img src="images/logo.png" alt="School Logo" class="loader-logo">
            </div>
            <div class="loader-arcs">
                <div class="arc arc1"></div>
                <div class="arc arc2"></div>
                <div class="arc arc3"></div>
            </div>
        </div>
        <div class="loader-text">Loading SS. Joachim and Anne Catholic School...</div>
    `;
    document.body.prepend(preloader);
    const anthem = document.getElementById('school_anthem');
    if (anthem) {
        anthem.insertAdjacentHTML('beforebegin', '<input id="anthem_title" class="form-control mb-2" placeholder="Anthem title"><textarea id="anthem_verse1" class="form-control mb-2" rows="2" placeholder="Verse 1"></textarea><textarea id="anthem_chorus" class="form-control mb-2" rows="2" placeholder="Chorus / refrain"></textarea><textarea id="anthem_verse2" class="form-control mb-2" rows="2" placeholder="Verse 2"></textarea><textarea id="anthem_verse3" class="form-control" rows="2" placeholder="Verse 3 (optional)"></textarea>');
        anthem.classList.add('d-none');
    }
});

window.addEventListener('load', () => {
    const preloader = document.getElementById('preloader');
    if (preloader) {
        preloader.classList.add('hidden');
        setTimeout(() => {
            preloader.remove();
        }, 500); // Wait for transition
    }
});

// Give every dashboard section a clearly visible save action.
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.dashboard-body .admin-card .card-header').forEach(header => {
        if (header.querySelector('.section-save-btn')) return;
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'btn btn-sm btn-primary section-save-btn';
        button.innerHTML = '<i class="fas fa-save me-1"></i> Save Section';
        button.addEventListener('click', () => {
            if (typeof saveAllSettings === 'function') saveAllSettings();
        });
        header.classList.add('section-header');
        header.appendChild(button);
    });
});

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
            const fields = ['academic_year', 'current_term', 'about_intro', 'about_mission', 'about_vision', 'priest_description', 'headboy_name', 'headgirl_name', 'school_rules', 'education_facilities', 'disciplinary_measures', 'school_anthem', 'jss_subjects'];
            fields.forEach(f => {
                if (document.getElementById(f)) document.getElementById(f).value = data[f] || '';
            });
            if (data.school_anthem) {
                String(data.school_anthem).split('\n---\n').forEach((part, index) => {
                    const field = document.getElementById(['anthem_title', 'anthem_verse1', 'anthem_chorus', 'anthem_verse2', 'anthem_verse3'][index]);
                    if (field) field.value = part;
                });
            }
            
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
        headgirl_name: document.getElementById('headgirl_name')?.value,
        school_rules: document.getElementById('school_rules')?.value,
        education_facilities: document.getElementById('education_facilities')?.value,
        disciplinary_measures: document.getElementById('disciplinary_measures')?.value,
        school_anthem: ['anthem_title','anthem_verse1','anthem_chorus','anthem_verse2','anthem_verse3'].map(id => document.getElementById(id)?.value || '').filter(Boolean).join('\n---\n'),
        jss_subjects: document.getElementById('jss_subjects')?.value
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

        container.innerHTML = msgs.map(m => {
            const emailHtml = m.email ? `<span class="text-muted small ms-2"><${m.email}></span>` : '';
            const newBadge = !m.is_read ? '<span class="badge bg-success ms-2">New</span>' : '';
            const readBtn = !m.is_read ? `<button class="btn btn-sm btn-outline-secondary rounded-pill" onclick="markMessageRead(${m.id})">Mark as Read</button>` : '';
            return `
            <div class="border rounded p-3 mb-3 ${m.is_read ? 'bg-white' : 'bg-light border-start border-success border-4'}">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong>${m.name || 'Unknown'}</strong>
                        ${emailHtml}
                        ${newBadge}
                    </div>
                    <small class="text-muted">${m.submitted_at || ''}</small>
                </div>
                <div class="fw-semibold mt-1">${m.subject || 'No subject'}</div>
                <div class="text-muted mt-1 small">${m.message || ''}</div>
                <div class="d-flex gap-2 mt-2">
                    ${readBtn}
                    <button class="btn btn-sm btn-outline-danger rounded-pill delete-msg-btn" onclick="deleteMessage(${m.id})"><i class="fas fa-trash-alt me-1"></i> Delete</button>
                </div>
            </div>`;
        }).join('');
    } catch(e) {
        container.innerHTML = '<p class="text-danger">Error loading messages.</p>';
    }
}

async function markMessageRead(id) {
    await fetch('/api/messages/' + id + '/read', {method: 'POST'});
    loadMessages();
    fetchNotificationCount();
}

async function deleteMessage(id) {
    if(!confirm("Are you sure you want to delete this message?")) return;
    try {
        const response = await fetch('/api/messages/' + id, { method: 'DELETE' });
        const result = await response.json();
        if(response.ok && result.success) {
            showStatus('Message deleted successfully');
            loadMessages();
            fetchNotificationCount();
        } else {
            showStatus('Failed to delete message', true);
        }
    } catch(e) {
        showStatus('Error deleting message', true);
    }
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
                    <div class="row mt-2 small text-muted g-2">
                    <div class="col-sm-4"><b>Application No:</b> ${a.application_number || a.id}</div>
                    <div class="col-sm-4"><b>Status:</b> <select class="form-select form-select-sm d-inline-block w-auto" onchange="updateAdmissionStatus(${a.id}, this.value)">${['Submitted','Under Review','Accepted','Rejected','Waitlisted','Shortlisted'].map(s => `<option ${s === (a.status || 'Submitted') ? 'selected' : ''}>${s}</option>`).join('')}</select></div>
                    <div class="col-sm-4"><b>Session/Term:</b> ${a.session_term || '-'}</div>
                    <div class="col-sm-4"><b>Nationality:</b> ${a.nationality || '-'}</div>
                    <div class="col-sm-4"><b>Previous School:</b> ${a.previous_school || '-'}</div>
                    <div class="col-sm-4"><b>Class:</b> ${a.class_applying || '-'}</div>
                    <div class="col-sm-4"><b>DOB:</b> ${a.date_of_birth || '-'}</div>
                    <div class="col-sm-4"><b>Gender:</b> ${a.gender || '-'}</div>
                    <div class="col-sm-4"><b>Parent/Guardian:</b> ${a.parent_name || '-'}</div>
                    <div class="col-sm-4"><b>Relationship:</b> ${a.parent_relationship || '-'}</div>
                    <div class="col-sm-4"><b>Occupation:</b> ${a.parent_occupation || '-'}</div>
                    <div class="col-sm-4"><b>Phone:</b> ${a.parent_phone || '-'}</div>
                    <div class="col-sm-4"><b>Email:</b> ${a.parent_email || '-'}</div>
                    <div class="col-sm-12"><b>Student Home Address:</b> ${a.student_home_address || a.address || '-'}</div>
                    <div class="col-sm-12"><b>Parent Home Address:</b> ${a.parent_home_address || '-'}</div>
                    <div class="col-sm-4"><b>Emergency Contact:</b> ${a.emergency_contact_name || '-'}</div>
                    <div class="col-sm-4"><b>Emergency Phone:</b> ${a.emergency_contact_phone || '-'}</div>
                    <div class="col-sm-4"><b>Emergency Relationship:</b> ${a.emergency_contact_relationship || '-'}</div>
                    <div class="col-sm-4"><b>Blood Group:</b> ${a.blood_group || '-'}</div>
                    <div class="col-sm-8"><b>Medical Conditions/Allergies:</b> ${a.allergies_medical_conditions || '-'}</div>
                    <div class="col-sm-12"><b>Parent Signature:</b> ${a.parent_signature || '-'} <b class="ms-3">Date:</b> ${a.signature_date || '-'}</div>
                    <div class="col-sm-12"><b>Uploaded Documents:</b> ${[a.passport_photo_path, a.birth_certificate_path, a.previous_school_report_path].filter(Boolean).map(path => `<a class="me-3" href="${path}" target="_blank" rel="noopener">View document</a>`).join('') || '-'}</div>
                </div>
<div class="d-flex gap-2 mt-2">
                    ${!a.is_read ? `<button class="btn btn-sm btn-outline-secondary rounded-pill" onclick="markAdmissionRead(${a.id})">Mark as Read</button>` : ''}
                    ${a.status === 'Accepted' ? `<a class="btn btn-sm btn-outline-success rounded-pill" href="/admission-letter/${a.id}" target="_blank"><i class="fas fa-file-signature me-1"></i> Admission Letter</a>` : ''}
                    <button class="btn btn-sm btn-outline-primary rounded-pill" onclick="downloadAdmissionPDF(${a.id})"><i class="fas fa-file-pdf me-1"></i> Download PDF</button>
                </div>
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

async function updateAdmissionStatus(id, status) {
    const response = await fetch('/api/admissions/' + id + '/status', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({status})
    });
    if (response.ok) showStatus('Application status updated');
    else showStatus('Failed to update application status', true);
}

// ============================================================
// News / Blog / Events Manager
// ============================================================

const postCatLabels = { news: 'News', blog: 'Blog', event: 'Event' };

async function loadPosts() {
    const container = document.getElementById('posts_list');
    if (!container) return;
    try {
        const res = await fetch('/api/posts');
        const data = await res.json();
        if (!data.success) { container.innerHTML = '<p class="text-danger">Failed to load posts.</p>'; return; }
        const posts = data.data || [];
        if (posts.length === 0) {
            container.innerHTML = '<p class="text-muted text-center py-3">No posts published yet.</p>';
            return;
        }
        container.innerHTML = posts.map(p => {
            const thumb = p.image_path
                ? `<img src="${p.image_path}" style="width:70px;height:50px;object-fit:cover;border-radius:6px;">`
                : `<div style="width:70px;height:50px;background:#f1f3f5;border-radius:6px;display:flex;align-items:center;justify-content:center;color:#adb5bd;"><i class="fas fa-newspaper"></i></div>`;
            return `
            <div class="border rounded p-3 mb-3 bg-white d-flex gap-3 align-items-start">
                ${thumb}
                <div class="flex-grow-1">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <strong>${p.title || 'Untitled'}</strong>
                            <span class="badge bg-danger ms-2">${postCatLabels[p.category] || 'News'}</span>
                            ${p.featured ? '<span class="badge bg-warning text-dark ms-1">Featured</span>' : ''}
                            ${p.status === 'draft' ? '<span class="badge bg-secondary ms-1">Draft</span>' : ''}
                        </div>
                        <small class="text-muted">${p.date || ''}</small>
                    </div>
                    <div class="text-muted mt-1 small">${(p.content || '').substring(0, 120)}${(p.content || '').length > 120 ? '…' : ''}</div>
                </div>
                <div class="d-flex gap-2">
                    <button class="btn btn-sm btn-outline-primary rounded-pill" onclick="editPost(${p.id})"><i class="fas fa-pen me-1"></i> Edit</button>
                    <button class="btn btn-sm btn-outline-danger rounded-pill" onclick="deletePost(${p.id})"><i class="fas fa-trash-alt me-1"></i> Delete</button>
                </div>
            </div>`;
        }).join('');
    } catch(e) {
        container.innerHTML = '<p class="text-danger">Error loading posts.</p>';
    }
}

async function publishPost() {
    const title = document.getElementById('post_title').value.trim();
    const category = document.getElementById('post_category').value;
    const content = document.getElementById('post_content').value.trim();
    const imageInput = document.getElementById('post_image_input');
    const author = document.getElementById('post_author')?.value.trim();
    const status = document.getElementById('post_status')?.value || 'published';
    const scheduled_for = document.getElementById('post_scheduled_for')?.value || '';
    const featured = document.getElementById('post_featured')?.checked || false;

    if (!title || !content) {
        showStatus('Please provide both a title and content.', true);
        return;
    }

    let image_path = '';
    if (imageInput && imageInput.files && imageInput.files.length > 0) {
        const formData = new FormData();
        formData.append('image', imageInput.files[0]);
        formData.append('key', 'post_temp');
        try {
            const uploadRes = await fetch('/api/upload', { method: 'POST', body: formData });
            const uploadResult = await uploadRes.json();
            if (uploadResult.success) image_path = uploadResult.path;
        } catch(e) {
            console.warn('Post image upload failed', e);
        }
    }

    try {
        const res = await fetch('/api/posts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, category, content, image_path, author, status, scheduled_for, featured })
        });
        const result = await res.json();
        if (res.ok && result.success) {
            showStatus('Post published successfully!');
            document.getElementById('post_title').value = '';
            document.getElementById('post_content').value = '';
            if (imageInput) imageInput.value = '';
            loadPosts();
        } else {
            showStatus(result.message || 'Failed to publish post', true);
        }
    } catch(e) {
        showStatus('Server error during publish', true);
    }
}

async function editPost(id) {
    const response = await fetch('/api/posts');
    const result = await response.json();
    const post = (result.data || []).find(item => item.id === id);
    if (!post) return showStatus('Post not found', true);

    document.getElementById('post_title').value = post.title || '';
    document.getElementById('post_category').value = post.category || 'news';
    document.getElementById('post_content').value = post.content || '';
    document.getElementById('post_author').value = post.author || '';
    document.getElementById('post_status').value = post.status || 'published';
    document.getElementById('post_scheduled_for').value = post.scheduled_for || '';
    document.getElementById('post_featured').checked = Boolean(post.featured);

    const publishButton = document.querySelector('[onclick="publishPost()"]');
    publishButton.innerHTML = '<i class="fas fa-save me-2"></i> Save Post';
    publishButton.onclick = () => saveEditedPost(id, post.image_path || '');
    document.getElementById('post_title').scrollIntoView({ behavior: 'smooth', block: 'center' });
}

async function saveEditedPost(id, existingImagePath) {
    const imageInput = document.getElementById('post_image_input');
    if (imageInput?.files?.length) {
        const upload = new FormData(); upload.append('image', imageInput.files[0]); upload.append('key', 'post_temp');
        const uploaded = await fetch('/api/upload', {method: 'POST', body: upload}).then(r => r.json());
        if (uploaded.success) existingImagePath = uploaded.path;
    }
    const data = {
        title: document.getElementById('post_title').value.trim(),
        category: document.getElementById('post_category').value,
        content: document.getElementById('post_content').value.trim(),
        author: document.getElementById('post_author').value.trim(),
        status: document.getElementById('post_status').value,
        scheduled_for: document.getElementById('post_scheduled_for').value,
        featured: document.getElementById('post_featured').checked,
        image_path: existingImagePath
    };
    const response = await fetch('/api/posts/' + id, {
        method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)
    });
    const result = await response.json();
    if (response.ok && result.success) {
        showStatus('Post updated successfully');
        window.location.reload();
    } else {
        showStatus(result.message || 'Failed to update post', true);
    }
}

async function deletePost(id) {
    if (!confirm('Are you sure you want to delete this post?')) return;
    try {
        const res = await fetch('/api/posts/' + id, { method: 'DELETE' });
        const result = await res.json();
        if (res.ok && result.success) {
            showStatus('Post deleted successfully');
            loadPosts();
        } else {
            showStatus('Failed to delete post', true);
        }
    } catch(e) {
        showStatus('Error deleting post', true);
    }
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

// ============================================================
// Admission Application PDF Export
// ============================================================

async function downloadAdmissionPDF(id) {
    try {
        const res = await fetch('/api/admissions');
        const data = await res.json();
        if (!data.success) { showStatus('Failed to load application', true); return; }
        const app = data.data.find(a => a.id === id);
        if (!app) { showStatus('Application not found', true); return; }

        const { jsPDF } = window.jspdf;
        const doc = new jsPDF('p', 'pt', 'a4');
        const pageWidth = doc.internal.pageSize.getWidth();   // 595
        const pageHeight = doc.internal.pageSize.getHeight(); // 842
        const M = 40;
        const contentW = pageWidth - (2 * M);
        let y = 0;

        const NAVY = [18, 52, 96];
        const GOLD = [178, 138, 28];
        const DARK = [33, 33, 33];
        const GRAY = [120, 120, 120];

        // ============ FORM HEADER (mirrors the admission form) ============
        // Top gold + navy bars
        doc.setFillColor(...GOLD);
        doc.rect(0, 0, pageWidth, 6, 'F');
        doc.setFillColor(...NAVY);
        doc.rect(0, 6, pageWidth, 4, 'F');

        // Centered school name
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(17);
        doc.setTextColor(...NAVY);
        doc.text('SS. JOACHIM AND ANNE CATHOLIC SCHOOL', pageWidth / 2, 44, {align: 'center'});

        // Subtitle
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(12);
        doc.setTextColor(60, 60, 60);
        doc.text('ADMISSION APPLICATION FORM', pageWidth / 2, 62, {align: 'center'});

        // School contact line
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(8);
        doc.setTextColor(...GRAY);
        doc.text('412 Road, Gowon Estate, Lagos  |  +234 805 476 9226  |  info@sjacs.edu.ng', pageWidth / 2, 76, {align: 'center'});

        // Double border under header
        doc.setDrawColor(...GOLD);
        doc.setLineWidth(2);
        doc.line(M, 86, pageWidth - M, 86);
        doc.setDrawColor(...NAVY);
        doc.setLineWidth(0.6);
        doc.line(M, 90, pageWidth - M, 90);

        y = 108;

        // Application meta row
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(9);
        doc.setTextColor(...DARK);
        doc.text(`Application No: ${app.id}`, M, y);
        doc.text(`Submitted: ${app.submitted_at || '-'}`, pageWidth - M, y, {align: 'right'});
        y += 18;
        doc.text('Session/Term:', M, y);
        doc.setFont('helvetica', 'normal');
        doc.text(`${app.session_term || '-'}`, M + 62, y);
        doc.setDrawColor(200, 200, 200);
        doc.line(M + 62, y + 4, M + 220, y + 4);
        y += 22;

        // ============ HELPER FUNCTIONS ============

        // Section heading (navy text with underline, like the form)
        const sectionTitle = (title, space = 8) => {
            y += space;
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(11);
            doc.setTextColor(...NAVY);
            doc.text(title, M, y);
            doc.setDrawColor(...GOLD);
            doc.setLineWidth(1);
            doc.line(M, y + 4, pageWidth - M, y + 4);
            y += 16;
        };

        // A labelled field with a bottom line (form control look)
        // cols: array of {label, value, w}
        const fieldRow = (cols) => {
            const gap = 14;
            const totalW = contentW - (gap * (cols.length - 1));
            let x = M;
            const labelY = y;
            const valY = y + 14;
            const lineY = y + 18;
            cols.forEach(c => {
                doc.setFont('helvetica', 'bold');
                doc.setFontSize(6.5);
                doc.setTextColor(...GRAY);
                doc.text(c.label.toUpperCase(), x, labelY);
                doc.setFont('helvetica', 'normal');
                doc.setFontSize(9.5);
                doc.setTextColor(...DARK);
                doc.text(c.value || '', x, valY);
                doc.setDrawColor(200, 200, 200);
                doc.setLineWidth(0.5);
                doc.line(x, lineY, x + c.w, lineY);
                x += c.w + gap;
            });
            y += 26;
        };

        // Full-width text field (for addresses / long text)
        const fullField = (label, value) => {
            fieldRow([{ label, value: value || '', w: contentW }]);
        };

        // ============ 1. SCHOOL INFORMATION ============
        sectionTitle('SCHOOL INFORMATION');
        fieldRow([
            { label: 'School Name', value: 'SS. Joachim and Anne Catholic School', w: contentW * 0.5 },
            { label: 'Session / Term', value: app.session_term || '', w: contentW * 0.5 }
        ]);

        // ============ 2. STUDENT INFORMATION ============
        sectionTitle('STUDENT INFORMATION', 6);

        // Passport photo box on the right, name on the left
        const photoW = 70;
        const photoH = 80;
        const photoX = pageWidth - M - photoW;
        const nameW = contentW - photoW - 20;

        // Name field
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(6.5);
        doc.setTextColor(...GRAY);
        doc.text('FULL NAME', M, y);
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(11);
        doc.setTextColor(...DARK);
        doc.text(app.student_name || '', M, y + 16);
        doc.setDrawColor(200, 200, 200);
        doc.line(M, y + 20, M + nameW, y + 20);

        // Passport photo box
        doc.setDrawColor(0, 0, 0);
        doc.setLineWidth(1);
        doc.rect(photoX, y, photoW, photoH);
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(7);
        doc.setTextColor(...GRAY);
        doc.text('PASSPORT', photoX + (photoW / 2), y + (photoH / 2) - 4, {align: 'center'});
        doc.text('PHOTO', photoX + (photoW / 2), y + (photoH / 2) + 6, {align: 'center'});
        y += photoH + 10;

        // DOB / Gender / Nationality
        const third = (contentW - 28) / 3;
        fieldRow([
            { label: 'Date of Birth', value: app.date_of_birth || '', w: third },
            { label: 'Gender', value: (app.gender || '').replace(/^./, ch => ch.toUpperCase()), w: third },
            { label: 'Nationality', value: app.nationality || '', w: third }
        ]);

        fullField('Home Address', app.student_home_address || app.address);
        const half = (contentW - 14) / 2;
        fieldRow([
            { label: 'Previous School Attended', value: app.previous_school || '', w: half },
            { label: 'Class Applying For', value: app.class_applying || '', w: half }
        ]);

        // ============ 3. PARENT / GUARDIAN INFORMATION ============
        sectionTitle('PARENT / GUARDIAN INFORMATION', 6);
        fieldRow([
            { label: 'Full Name', value: app.parent_name || '', w: half },
            { label: 'Relationship to Student', value: app.parent_relationship || '', w: half }
        ]);
        fieldRow([
            { label: 'Occupation', value: app.parent_occupation || '', w: half },
            { label: 'Phone Number', value: app.parent_phone || '', w: half }
        ]);
        fullField('Email Address', app.parent_email);
        fullField('Home Address (if different)', app.parent_home_address);

        // ============ 4. EMERGENCY CONTACT ============
        sectionTitle('EMERGENCY CONTACT', 6);
        fieldRow([
            { label: 'Contact Name', value: app.emergency_contact_name || '', w: third },
            { label: 'Phone Number', value: app.emergency_contact_phone || '', w: third },
            { label: 'Relationship', value: app.emergency_contact_relationship || '', w: third }
        ]);

        // ============ 5. MEDICAL INFORMATION ============
        sectionTitle('MEDICAL INFORMATION', 6);
        fieldRow([
            { label: 'Blood Group', value: app.blood_group || '', w: contentW * 0.3 }
        ]);
        fullField('Allergies / Medical Conditions', app.allergies_medical_conditions);

        // ============ 6. DECLARATION ============
        sectionTitle('DECLARATION', 6);
        // Declaration box
        doc.setDrawColor(...NAVY);
        doc.setLineWidth(0.8);
        const declText = doc.splitTextToSize(
            'I hereby declare that the information provided above is true and correct to the best of my knowledge. I agree to abide by the rules and regulations of the school.',
            contentW - 20
        );
        const declH = (declText.length * 13) + 30;
        doc.rect(M, y, contentW, declH);

        doc.setFont('helvetica', 'bold');
        doc.setFontSize(10);
        doc.setTextColor(...NAVY);
        doc.text('Declaration', M + 10, y + 18);

        doc.setFont('helvetica', 'normal');
        doc.setFontSize(9);
        doc.setTextColor(...DARK);
        doc.text(declText, M + 10, y + 36);
        y += declH + 12;

        // Signature and date
        fieldRow([
            { label: "Parent/Guardian Signature (Typed)", value: app.parent_signature || '', w: contentW * 0.6 },
            { label: 'Date', value: app.signature_date || '', w: contentW * 0.4 }
        ]);

        // ============ FOOTER ============
        doc.setDrawColor(...GOLD);
        doc.setLineWidth(1);
        doc.line(M, pageHeight - 40, pageWidth - M, pageHeight - 40);

        doc.setFont('helvetica', 'italic');
        doc.setFontSize(8);
        doc.setTextColor(...GRAY);
        doc.text('This is a computer-generated admission application form issued by SS. Joachim and Anne Catholic School.', pageWidth / 2, pageHeight - 24, {align: 'center'});

        const safeName = (app.student_name || 'student').replace(/[^a-z0-9]+/gi, '_');
        doc.save(`Admission_Application_${app.id}_${safeName}.pdf`);
    } catch (e) {
        console.error('PDF generation error', e);
        showStatus('Failed to generate PDF', true);
    }
}

