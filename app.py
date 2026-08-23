import os
import json
import time
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory, session, redirect, Response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from firestore_placeholder import get_placeholder_store

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY') or 'local-development-only-change-me'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
SITE_URL = os.getenv('SITE_URL', 'https://ssja.onrender.com').rstrip('/')

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / 'images' / 'uploads'
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

from dotenv import load_dotenv

load_dotenv()

FIREBASE_CREDENTIAL_PATH = os.environ.get(
    'FIREBASE_CREDENTIAL_PATH',
    str(BASE_DIR / 'great-worship-firebase-adminsdk-cyj0x-110600c06e.json')
)

_firestore_client = None

try:
    import firebase_admin
    from firebase_admin import credentials, firestore as fs
except ImportError:
    firebase_admin = None
    credentials = None
    fs = None


def initialize_firebase():
    global _firestore_client
    if firebase_admin is None or not os.path.exists(FIREBASE_CREDENTIAL_PATH):
        return False
    try:
        if not firebase_admin._apps:
            firebase_admin.initialize_app(credentials.Certificate(FIREBASE_CREDENTIAL_PATH))
        _firestore_client = fs.client()
        return True
    except Exception as exc:
        print(f"Firebase initialization failed: {exc}")
        return False


STORE = get_placeholder_store()
initialize_firebase()

@app.after_request
def no_stale_pages(response):
    # HTML and API responses must always reflect the latest admin edits.
    if request.path.startswith('/api/') or request.path.endswith(('.html', '/')):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY', '')
VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY', '')
VAPID_CLAIMS = {"sub": os.getenv('VAPID_SUBJECT', "mailto:admin@sjacs.edu.ng")}

PAGES = {
    'index', 'about', 'academics', 'education-facilities', 'education-staff',
    'education-anthem', 'disciplinary-measures', 'school-rules-regulations',
    'admissions', 'admission-form', 'jss-subjects', 'gallery', 'contact', 'admin',
    'admin-dashboard', 'news'
}


def get_store():
    return STORE


def save_store():
    if _firestore_client is not None:
        try:
            _firestore_client.collection('site_data').document('store').set(STORE)
        except Exception as exc:
            print(f"Failed to sync store to Firestore: {exc}")


def get_next_id(items):
    return max((item.get('id', 0) for item in items), default=0) + 1


def send_push_notification(title, body, url='/admin-dashboard'):
    if not VAPID_PUBLIC_KEY or not VAPID_PRIVATE_KEY:
        return
    try:
        from pywebpush import webpush
        for subscription_json in get_store().get('push_subscriptions', []):
            try:
                webpush(
                    subscription_info=json.loads(subscription_json),
                    data=json.dumps({"title": title, "body": body, "url": url}),
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims=VAPID_CLAIMS,
                )
            except Exception as exc:
                print(f"Push failed for subscription: {exc}")
    except ImportError:
        print("pywebpush not installed. Skipping push notifications.")


@app.route('/')
def index_page():
    return send_from_directory(BASE_DIR, 'index.html')


@app.route('/<page>')
def page_route(page):
    if page == 'admin-dashboard' and not session.get('admin_logged_in'):
        return redirect('/admin')
    if page in PAGES:
        return send_from_directory(BASE_DIR, f'{page}.html')
    if page.endswith(('.py', '.db', '.md')) or page.startswith('.'):
        return 'Forbidden', 403
    return send_from_directory(BASE_DIR, page)


@app.route('/<path:filename>')
def static_route(filename):
    if filename == 'admin-dashboard.html' and not session.get('admin_logged_in'):
        return redirect('/admin')
    if filename.endswith(('.py', '.db', '.md')) or filename.startswith('.'):
        return 'Forbidden', 403
    return send_from_directory(BASE_DIR, filename)


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    admin = next((a for a in get_store().get('admins', []) if a.get('username') == data.get('username')), None)
    if admin and check_password_hash(admin['password_hash'], data.get('password', '')):
        session['admin_logged_in'] = True
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Invalid username or password"}), 401


@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('admin_logged_in', None)
    return jsonify({"success": True})


@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    if not session.get('admin_logged_in'):
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    subscription = request.get_json().get('subscription')
    subscriptions = get_store().setdefault('push_subscriptions', [])
    sub_json = json.dumps(subscription, sort_keys=True)
    if sub_json not in subscriptions:
        subscriptions.append(sub_json)
        save_store()
    return jsonify({"success": True, "message": "Subscribed to push notifications"})


@app.route('/api/vapid-public-key', methods=['GET'])
def get_vapid_key():
    return jsonify({"publicKey": VAPID_PUBLIC_KEY})


@app.route('/post/<int:post_id>')
def post_detail_page(post_id):
    return send_from_directory(BASE_DIR, 'post-detail.html')


@app.errorhandler(404)
def page_not_found(error):
    app.logger.info('404 %s %s', request.method, request.path)
    return send_from_directory(BASE_DIR, '404.html'), 404


@app.route('/robots.txt')
def robots_txt():
    return Response(
        f'User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /admin-dashboard\nDisallow: /api/\nSitemap: {SITE_URL}/sitemap.xml\n',
        mimetype='text/plain',
    )


@app.route('/sitemap.xml')
def sitemap_xml():
    public_pages = ['/', '/about', '/academics', '/admissions', '/admission-form', '/news', '/gallery', '/contact']
    urls = ''.join(f'<url><loc>{SITE_URL}{page}</loc></url>' for page in public_pages)
    return Response(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>',
        mimetype='application/xml',
    )


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "success": True,
        "firebase": _firestore_client is not None,
        "storage": "firestore" if _firestore_client is not None else "local-fallback",
    })


# --- Content ---
@app.route('/api/content', methods=['GET'])
def get_all_content():
    store = get_store()
    content = {row['key']: row['value'] for row in store.get('content', [])}
    content['gallery'] = [
        {
            "id": r["id"],
            "category": r["category"],
            "image_path": r["image_path"],
            "title": r.get("title") or "",
            "description": r.get("description") or "",
        }
        for r in store.get('gallery', [])
    ]
    return jsonify({"success": True, "data": content})


@app.route('/api/content', methods=['POST'])
def update_content():
    if not session.get('admin_logged_in'):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    store = get_store()
    existing = {row['key']: row for row in store.get('content', [])}
    for key, value in data.items():
        if key == 'gallery':
            continue
        if key in existing:
            existing[key]['value'] = str(value)
        else:
            existing[key] = {'key': key, 'value': str(value)}
    store['content'] = list(existing.values())
    save_store()
    return jsonify({"success": True})


@app.route('/api/upload', methods=['POST'])
def upload_file():
    if not session.get('admin_logged_in'):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    if 'image' not in request.files:
        return jsonify({"success": False, "message": "No file"}), 400

    file = request.files['image']
    key = request.form.get('key')

    if not file.filename or not key:
        return jsonify({"success": False, "message": "Missing file or key"}), 400

    filename = f"{int(time.time())}_{secure_filename(file.filename)}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    relative_path = f"images/uploads/{filename}"
    store = get_store()

    if key == 'gallery':
        category = request.form.get('category', 'all')
        title = request.form.get('title', '')
        store.setdefault('gallery', []).append({
            "id": get_next_id(store['gallery']),
            "category": category,
            "image_path": relative_path,
            "title": title,
            "description": "",
        })
    else:
        existing = {row['key']: row for row in store.get('content', [])}
        if key in existing:
            existing[key]['value'] = relative_path
        else:
            existing[key] = {'key': key, 'value': relative_path}
        store['content'] = list(existing.values())

    save_store()

    return jsonify({"success": True, "path": relative_path})


@app.route('/api/admission-documents', methods=['POST'])
def upload_admission_document():
    file = request.files.get('file')
    document_type = request.form.get('document_type', 'document')
    allowed_types = {'birth_certificate', 'previous_school_report', 'passport_photograph'}
    if not file or not file.filename:
        return jsonify({"success": False, "message": "No document selected"}), 400
    if document_type not in allowed_types:
        return jsonify({"success": False, "message": "Invalid document type"}), 400

    filename = f"admission_{document_type}_{uuid.uuid4().hex[:12]}_{secure_filename(file.filename)}"
    file.save(UPLOAD_FOLDER / filename)
    return jsonify({"success": True, "path": f"images/uploads/{filename}"})


@app.route('/api/gallery/<int:item_id>', methods=['DELETE'])
def delete_gallery_item(item_id):
    if not session.get('admin_logged_in'):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    gallery = get_store().get('gallery', [])
    updated = [item for item in gallery if item.get('id') != item_id]
    get_store()['gallery'] = updated
    save_store()
    return jsonify({"success": True})


# --- Contact Form ---
@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.get_json() or {}
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

    store = get_store()
    messages = store.setdefault('messages', [])
    messages.append({
        "id": get_next_id(messages),
        "name": data.get('name'),
        "email": data.get('email'),
        "subject": data.get('subject'),
        "message": data.get('message'),
        "is_read": 0,
        "submitted_at": timestamp,
    })

    send_push_notification(
        title="📩 New Contact Message",
        body=f"From {data.get('name', 'Someone')}: {data.get('subject', 'No subject')}",
        url="/admin-dashboard",
    )

    save_store()

    return jsonify({"success": True, "message": "Message received!"})


@app.route('/api/messages', methods=['GET'])
def get_messages():
    if not session.get('admin_logged_in'):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    messages = sorted(get_store().get('messages', []), key=lambda x: x.get('id', 0), reverse=True)
    return jsonify({"success": True, "data": messages})


@app.route('/api/messages/<int:msg_id>/read', methods=['POST'])
def mark_message_read(msg_id):
    if not session.get('admin_logged_in'):
        return jsonify({"success": False}), 401

    store = get_store()
    for message in store.get('messages', []):
        if message.get('id') == msg_id:
            message['is_read'] = 1
            break
    save_store()
    return jsonify({"success": True})


@app.route('/api/messages/<int:msg_id>', methods=['DELETE'])
def delete_message(msg_id):
    if not session.get('admin_logged_in'):
        return jsonify({"success": False}), 401

    store = get_store()
    store['messages'] = [m for m in store.get('messages', []) if m.get('id') != msg_id]
    save_store()
    return jsonify({"success": True})


# --- Admission Form ---
@app.route('/api/admissions', methods=['POST'])
def submit_admission():
    data = request.get_json() or {}
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

    store = get_store()
    admissions = store.setdefault('admissions', [])
    application_id = get_next_id(admissions)
    application_number = f"SJACS-{time.strftime('%Y')}-{application_id:05d}"
    admissions.append({
        "id": application_id,
        "application_number": application_number,
        "status": "Submitted",
        "student_name": data.get('student_name'),
        "date_of_birth": data.get('date_of_birth'),
        "gender": data.get('gender'),
        "class_applying": data.get('class_applying'),
        "parent_name": data.get('parent_name'),
        "parent_phone": data.get('parent_phone'),
        "parent_email": data.get('parent_email'),
        "address": data.get('address'),
        "is_read": 0,
        "submitted_at": timestamp,
        "session_term": data.get('session_term'),
        "nationality": data.get('nationality'),
        "student_home_address": data.get('student_home_address'),
        "previous_school": data.get('previous_school'),
        "parent_relationship": data.get('parent_relationship'),
        "parent_occupation": data.get('parent_occupation'),
        "parent_home_address": data.get('parent_home_address'),
        "emergency_contact_name": data.get('emergency_contact_name'),
        "emergency_contact_phone": data.get('emergency_contact_phone'),
        "emergency_contact_relationship": data.get('emergency_contact_relationship'),
        "blood_group": data.get('blood_group'),
        "allergies_medical_conditions": data.get('allergies_medical_conditions'),
        "parent_signature": data.get('parent_signature'),
        "signature_date": data.get('signature_date'),
        "passport_photo_path": data.get('passport_photo_path'),
        "birth_certificate_path": data.get('birth_certificate_path', ''),
        "previous_school_report_path": data.get('previous_school_report_path', ''),
    })

    send_push_notification(
        title="🎓 New Admission Application",
        body=f"{data.get('student_name', 'A student')} applied for {data.get('class_applying', 'a class')}",
        url="/admin-dashboard",
    )

    save_store()

    return jsonify({
        "success": True,
        "message": "Application submitted successfully!",
        "application_number": application_number,
    })


@app.route('/api/admissions', methods=['GET'])
def get_admissions():
    if not session.get('admin_logged_in'):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    admissions = sorted(get_store().get('admissions', []), key=lambda x: x.get('id', 0), reverse=True)
    return jsonify({"success": True, "data": admissions})


@app.route('/api/admissions/<int:app_id>/read', methods=['POST'])
def mark_admission_read(app_id):
    if not session.get('admin_logged_in'):
        return jsonify({"success": False}), 401

    store = get_store()
    for admission in store.get('admissions', []):
        if admission.get('id') == app_id:
            admission['is_read'] = 1
            break
    save_store()
    return jsonify({"success": True})


@app.route('/api/admissions/<int:app_id>/status', methods=['POST'])
def update_admission_status(app_id):
    if not session.get('admin_logged_in'):
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    status = (request.get_json() or {}).get('status')
    valid_statuses = {'Submitted', 'Under Review', 'Accepted', 'Rejected', 'Waitlisted', 'Shortlisted'}
    if status not in valid_statuses:
        return jsonify({"success": False, "message": "Invalid application status"}), 400
    for admission in get_store().get('admissions', []):
        if admission.get('id') == app_id:
            admission['status'] = status
            admission['status_updated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            save_store()
            return jsonify({"success": True, "data": admission})
    return jsonify({"success": False, "message": "Application not found"}), 404


@app.route('/api/applicant/<application_number>', methods=['GET'])
def applicant_dashboard(application_number):
    admission = next((item for item in get_store().get('admissions', [])
                      if item.get('application_number') == application_number), None)
    if not admission:
        return jsonify({"success": False, "message": "Application not found"}), 404
    return jsonify({"success": True, "data": {
        "application_number": admission.get('application_number'),
        "student_name": admission.get('student_name'),
        "class_applying": admission.get('class_applying'),
        "status": admission.get('status', 'Submitted'),
        "submitted_at": admission.get('submitted_at'),
    }})


@app.route('/admission-dashboard')
def admission_dashboard_page():
    return send_from_directory('.', 'applicant-dashboard.html')


@app.route('/admission-letter/<int:app_id>')
def admission_letter(app_id):
    if not session.get('admin_logged_in'):
        return redirect('/admin')
    admission = next((item for item in get_store().get('admissions', []) if item.get('id') == app_id), None)
    if not admission:
        return 'Application not found', 404
    if admission.get('status') != 'Accepted':
        return 'An admission letter is available only for accepted applications.', 409
    html = f'''<!doctype html><html><head><meta charset="utf-8"><title>Admission Letter - {admission.get('application_number')}</title><style>body{{font-family:Georgia,serif;max-width:760px;margin:50px auto;line-height:1.7;color:#172b4d}}.header{{text-align:center;border-bottom:3px solid #c99a2e;padding-bottom:20px}}.content{{padding:35px 10px}}.sign{{margin-top:60px}}@media print{{.print{{display:none}}}}</style></head><body><button class="print" onclick="window.print()">Print / Save as PDF</button><div class="header"><h1>SS. JOACHIM AND ANNE CATHOLIC SCHOOL</h1><p>412 Road, Gowon Estate, Lagos</p><h2>ADMISSION LETTER</h2></div><div class="content"><p>Date: {time.strftime('%d %B %Y')}</p><p>Dear Parent/Guardian,</p><p>We are pleased to offer <strong>{admission.get('student_name', '')}</strong> admission into <strong>{admission.get('class_applying', '')}</strong> for the coming academic session.</p><p>Application number: <strong>{admission.get('application_number', '')}</strong></p><p>Please contact the school office to complete registration and submit any outstanding requirements.</p><div class="sign"><p>Yours faithfully,</p><p><strong>School Administration</strong></p></div></div></body></html>'''
    return html


# --- News / Blog / Events ---
@app.route('/api/posts', methods=['GET'])
def get_posts():
    now = datetime.now().isoformat(timespec='minutes')
    posts = [p for p in get_store().get('posts', [])
             if p.get('status', 'published') == 'published'
             and (not p.get('scheduled_for') or p['scheduled_for'] <= now)]
    posts = sorted(posts, key=lambda x: x.get('id', 0), reverse=True)
    return jsonify({"success": True, "data": posts})


@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = next((p for p in get_store().get('posts', []) if p.get('id') == post_id), None)
    if not post:
        return jsonify({"success": False, "error": "Post not found"}), 404
    post.pop('views', None)
    post.pop('comments', None)
    return jsonify({"success": True, "data": post})


@app.route('/api/posts', methods=['POST'])
def create_post():
    if not session.get('admin_logged_in'):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    if not data.get('title'):
        return jsonify({"success": False, "message": "Title is required"}), 400
    if not data.get('content'):
        return jsonify({"success": False, "message": "Content is required"}), 400

    store = get_store()
    posts = store.setdefault('posts', [])
    new_post = {
        'id': get_next_id(posts),
        'title': data.get('title'),
        'category': data.get('category', 'news'),
        'content': data.get('content'),
        'image_path': data.get('image_path', ''),
        'date': data.get('date') or time.strftime('%Y-%m-%d %H:%M:%S'),
        'author': data.get('author', 'SS Joachim and Anne Catholic School'),
        'featured': bool(data.get('featured', False)),
        'status': data.get('status', 'published'),
        'scheduled_for': data.get('scheduled_for', ''),
    }
    posts.append(new_post)

    send_push_notification(
        title="📰 New Post Published",
        body=data.get('title', 'New post'),
        url="/admin-dashboard"
    )

    save_store()

    return jsonify({"success": True, "message": "Post created!", "data": new_post}), 201


@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    if not session.get('admin_logged_in'):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    for post in get_store().get('posts', []):
        if post.get('id') == post_id:
            for key in ('title', 'category', 'content', 'image_path', 'author', 'status', 'scheduled_for'):
                if key in data:
                    post[key] = data[key]
            if 'featured' in data:
                post['featured'] = bool(data['featured'])
            post.pop('views', None)
            post.pop('comments', None)
            save_store()
            return jsonify({"success": True, "message": "Post updated", "data": post})
    return jsonify({"success": False, "message": "Post not found"}), 404


@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    if not session.get('admin_logged_in'):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    store = get_store()
    posts = store.get('posts', [])
    new_posts = [p for p in posts if p.get('id') != post_id]
    if len(new_posts) == len(posts):
        return jsonify({"success": False, "message": "Post not found"}), 404
    store['posts'] = new_posts
    save_store()
    return jsonify({"success": True, "message": "Post deleted successfully"})


# --- Notification Count ---
@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    if not session.get('admin_logged_in'):
        return jsonify({"success": False}), 401

    store = get_store()
    unread_messages = sum(1 for m in store.get('messages', []) if m.get('is_read') == 0)
    unread_admissions = sum(1 for a in store.get('admissions', []) if a.get('is_read') == 0)

    return jsonify(
        {
            "success": True,
            "unread_messages": unread_messages,
            "unread_admissions": unread_admissions,
            "total": unread_messages + unread_admissions,
        }
    )


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
