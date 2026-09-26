import os
import json
import time
import uuid
import copy
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote

from flask import Flask, request, jsonify, send_from_directory, session, redirect, Response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

from firestore_placeholder import DEFAULT_GALLERY, get_placeholder_store

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'local-development-secret-change-me')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=3650)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
SITE_URL = os.getenv('SITE_URL', 'https://ssja.onrender.com').rstrip('/')
if SITE_URL.endswith('/index.html'):
    SITE_URL = SITE_URL[:-10]

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = Path(os.getenv('UPLOAD_FOLDER', str(BASE_DIR / 'images' / 'uploads')))
if not UPLOAD_FOLDER.is_absolute():
    UPLOAD_FOLDER = BASE_DIR / UPLOAD_FOLDER
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
FIREBASE_CREDENTIAL_PATH = os.environ.get(
    'FIREBASE_CREDENTIAL_PATH',
    str(BASE_DIR / 'firebase-service-account.json')
)
if not os.path.isabs(FIREBASE_CREDENTIAL_PATH):
    FIREBASE_CREDENTIAL_PATH = str((BASE_DIR / FIREBASE_CREDENTIAL_PATH).resolve())

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
    if firebase_admin is None:
        app.logger.error('firebase-admin is not installed; Firestore is unavailable.')
        return False
    try:
        service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON', '').strip()
        if service_account_json:
            credential = credentials.Certificate(json.loads(service_account_json))
        elif os.path.exists(FIREBASE_CREDENTIAL_PATH):
            credential = credentials.Certificate(FIREBASE_CREDENTIAL_PATH)
        else:
            app.logger.error('Firestore credentials are missing. Set FIREBASE_SERVICE_ACCOUNT_JSON or FIREBASE_CREDENTIAL_PATH.')
            return False

        if not firebase_admin._apps:
            options = {}
            firebase_admin.initialize_app(credential, options)
        _firestore_client = fs.client()
        # Hydrate the in-memory working copy from Firestore.
        snapshot = _firestore_client.collection('site_data').document('store').get()
        persisted = snapshot.to_dict() if snapshot.exists else {}
        STORE.clear()
        STORE.update(normalize_store(persisted))
        # Create/migrate one canonical document. This prevents local and Render
        # workers from silently using different incomplete store shapes.
        _firestore_client.collection('site_data').document('store').set(dict(STORE))
        return True
    except Exception as exc:
        _firestore_client = None
        app.logger.error('Firestore initialization failed; persistent storage is unavailable: %s', exc)
        return False


STORE = get_placeholder_store()


def normalize_store(data):
    """Keep every worker on the same document shape after a deploy or migration."""
    defaults = get_placeholder_store()
    normalized = copy.deepcopy(defaults)
    normalized.update(data or {})
    for key, default in defaults.items():
        if normalized.get(key) is None:
            normalized[key] = copy.deepcopy(default)
    return normalized


def sync_configured_admin(store):
    """Keep the configured deployment admin usable after credential changes."""
    username = os.getenv('ADMIN_USERNAME', '').strip()
    password = os.getenv('ADMIN_PASSWORD', '')
    if not username or not password:
        return
    admins = store.setdefault('admins', [])
    admin = next((item for item in admins if item.get('username') == username), None)
    if admin is None:
        admins.append({
            'id': max((item.get('id', 0) for item in admins), default=0) + 1,
            'username': username,
            'password_hash': generate_password_hash(password),
        })
        return
    if not check_password_hash(admin.get('password_hash', ''), password):
        admin['password_hash'] = generate_password_hash(password)


initialize_firebase()

@app.after_request
def no_stale_pages(response):
    # HTML and API responses must always reflect the latest admin edits.
    if request.path.startswith('/api/') or request.path.endswith(('.html', '/')):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response


@app.errorhandler(RuntimeError)
def persistent_storage_error(error):
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'message': 'This service is temporarily unavailable. Please try again shortly.'
        }), 503
    return 'This service is temporarily unavailable. Please try again shortly.', 503

VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY', '')
VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY', '')
VAPID_CLAIMS = {"sub": os.getenv('VAPID_SUBJECT', "mailto:okonudestiny4@gmail.com")}

PAGES = {
    'index', 'about', 'academics', 'education-facilities', 'education-staff',
    'education-anthem', 'disciplinary-measures', 'school-rules-regulations',
    'admissions', 'admission-form', 'jss-subjects', 'ss-subjects', 'gallery', 'contact', 'admin',
    'admin-dashboard', 'news'
}


def get_store():
    if _firestore_client is None:
        raise RuntimeError('Persistent Firestore storage is unavailable')
    # Render can run multiple workers. Refresh before every read so each
    # worker reflects the canonical Firestore document.
    snapshot = _firestore_client.collection('site_data').document('store').get()
    if snapshot.exists:
        persisted = snapshot.to_dict() or {}
        STORE.clear()
        STORE.update(normalize_store(persisted))
        sync_configured_admin(STORE)
    else:
        STORE.clear()
        STORE.update(normalize_store({}))
    return STORE


def save_store():
    if _firestore_client is None:
        raise RuntimeError('Persistent Firestore storage is unavailable')
    _firestore_client.collection('site_data').document('store').set(normalize_store(STORE))


def upload_to_local_storage(file, filename):
    """Save editor-managed images in the workspace uploads directory."""
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    destination = UPLOAD_FOLDER / filename
    file.stream.seek(0)
    file.save(destination)
    return f'/images/uploads/{filename}'


def validate_uploaded_file(file, allowed_extensions, allowed_mimetypes):
    if not file or not file.filename:
        return 'No file selected'
    extension = Path(file.filename).suffix.lower()
    if extension not in allowed_extensions:
        return 'Unsupported file type'
    if (file.mimetype or '').lower() not in allowed_mimetypes:
        return 'Unsupported file MIME type'
    file.stream.seek(0, os.SEEK_END)
    size = file.stream.tell()
    file.stream.seek(0)
    if size == 0:
        return 'The uploaded file is empty'
    if size > 10 * 1024 * 1024:
        return 'The uploaded file is too large'
    return None


def valid_email(value):
    return bool(re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', str(value or '').strip()))


def get_next_id(items):
    return max((item.get('id', 0) for item in items), default=0) + 1


def send_push_notification(title, body, url='/admin-dashboard'):
    if not VAPID_PUBLIC_KEY or not VAPID_PRIVATE_KEY:
        return
    try:
        from pywebpush import webpush
        subscriptions = get_store().get('push_subscriptions', [])
        for subscription_json in subscriptions:
            try:
                webpush(
                    subscription_info=json.loads(subscription_json),
                    data=json.dumps({"title": title, "body": body, "url": url}),
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims=VAPID_CLAIMS,
                )
            except Exception as exc:
                app.logger.warning('Push delivery failed: %s', exc)
    except Exception as exc:
        app.logger.warning('Push notifications unavailable: %s', exc)


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
    if admin and check_password_hash(admin.get('password_hash', ''), str(data.get('password', ''))):
        session['admin_logged_in'] = True
        session.permanent = True
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
    subscription = (request.get_json() or {}).get('subscription')
    if not isinstance(subscription, dict) or not subscription.get('endpoint'):
        return jsonify({"success": False, "message": "A valid push subscription is required"}), 400
    subscriptions = get_store().setdefault('push_subscriptions', [])
    sub_json = json.dumps(subscription, sort_keys=True)
    if sub_json not in subscriptions:
        subscriptions.append(sub_json)
        save_store()
    return jsonify({"success": True, "message": "Subscribed to push notifications"})


@app.route('/api/applicant-subscribe', methods=['POST'])
def applicant_subscribe():
    data = request.get_json() or {}
    number = str(data.get('application_number', '')).strip().upper()
    subscription = data.get('subscription')
    if not number or not isinstance(subscription, dict) or not subscription.get('endpoint'):
        return jsonify({"success": False, "message": "Application number and subscription are required"}), 400
    if not any(a.get('application_number') == number for a in get_store().get('admissions', [])):
        return jsonify({"success": False, "message": "Application not found"}), 404
    subscriptions = get_store().setdefault('applicant_push_subscriptions', {})
    subscriptions.setdefault(number, [])
    encoded = json.dumps(subscription, sort_keys=True)
    if encoded not in subscriptions[number]:
        subscriptions[number].append(encoded)
        save_store()
    return jsonify({"success": True})


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
        f'User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /admin-dashboard\nDisallow: /api/\nSitemap: {SITE_URL}/sitemap.xml\nSitemap: {SITE_URL}/image-sitemap.xml\n',
        mimetype='text/plain',
    )


@app.route('/sitemap.xml')
def sitemap_xml():
    public_pages = ['/', '/about', '/academics', '/education-facilities', '/education-staff',
                    '/education-anthem', '/school-rules-regulations', '/disciplinary-measures',
                    '/admissions', '/admission-form', '/jss-subjects', '/ss-subjects', '/news', '/gallery', '/contact']
    urls = ''.join(f'<url><loc>{SITE_URL}{page}</loc><changefreq>weekly</changefreq><priority>{"1.0" if page == "/" else "0.7"}</priority></url>' for page in public_pages)
    return Response(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>',
        mimetype='application/xml',
    )


@app.route('/image-sitemap.xml')
def image_sitemap_xml():
    """Expose the school's stable public images to image crawlers."""
    public_images = [
        'images/logo.png',
        'images/school-building.png',
        'images/Interactive classroom with engaged students.png',
        'images/visit-to-sister-school.jpeg',
        'images/EXCURSION.jpeg',
        'images/sprot.jpeg',
    ]
    image_entries = ''.join(
        f'<url><loc>{SITE_URL}/</loc><image:image><image:loc>{SITE_URL}/{quote(path)}</image:loc></image:image></url>'
        for path in public_images
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
        f'{image_entries}</urlset>'
    )
    return Response(xml, mimetype='application/xml')


@app.route('/api/health', methods=['GET'])
def health_check():
    connected = _firestore_client is not None
    return jsonify({
        "success": connected,
        "status": "connected" if connected else "unavailable",
        "firebase": connected,
        "database": "Firestore" if connected else None,
        "storage": "Local uploads folder",
        "push_notifications": bool(VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY),
        "message": "Website services are ready." if connected else "Website services are temporarily unavailable."
    }), (200 if connected else 503)


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
    allowed = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
    validation_error = validate_uploaded_file(file, allowed, {'image/jpeg', 'image/png', 'image/webp', 'image/gif'})
    if validation_error:
        return jsonify({"success": False, "message": validation_error}), 400

    filename = f"{int(time.time())}_{uuid.uuid4().hex[:8]}_{secure_filename(file.filename)}"
    try:
        relative_path = upload_to_local_storage(file, filename)
    except OSError:
        app.logger.exception('Local image upload failed')
        return jsonify({"success": False, "message": "The image could not be saved"}), 500
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
    if document_type not in allowed_types:
        return jsonify({"success": False, "message": "Invalid document type"}), 400
    allowed = {'.jpg', '.jpeg', '.png', '.webp', '.pdf'}
    validation_error = validate_uploaded_file(file, allowed, {'image/jpeg', 'image/png', 'image/webp', 'application/pdf'})
    if validation_error:
        return jsonify({"success": False, "message": validation_error}), 400

    filename = f"admission_{document_type}_{uuid.uuid4().hex[:12]}_{secure_filename(file.filename)}"
    try:
        path = upload_to_local_storage(file, filename)
    except OSError:
        app.logger.exception('Local admission document upload failed')
        return jsonify({"success": False, "message": "The document could not be saved"}), 500
    return jsonify({"success": True, "path": path})


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
    if any(not str(data.get(field, '')).strip() for field in ('name', 'email', 'message')):
        return jsonify({"success": False, "message": "Name, email, and message are required"}), 400
    if not valid_email(data.get('email')):
        return jsonify({"success": False, "message": "Enter a valid email address"}), 400
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

    save_store()
    send_push_notification(
        title="New Contact Message",
        body=f"From {data.get('name', 'Someone')}: {data.get('subject', 'No subject')}",
        url="/admin-dashboard",
    )

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
    found = False
    for message in store.get('messages', []):
        if message.get('id') == msg_id:
            message['is_read'] = 1
            found = True
            break
    if not found:
        return jsonify({"success": False, "message": "Message not found"}), 404
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
    required = ('student_name', 'date_of_birth', 'gender', 'class_applying', 'parent_name', 'parent_phone', 'parent_email', 'student_home_address')
    if any(not str(data.get(field, '')).strip() for field in required):
        return jsonify({"success": False, "message": "Please complete all required admission fields"}), 400
    if not valid_email(data.get('parent_email')) or len(re.sub(r'\D', '', str(data.get('parent_phone', '')))) < 7:
        return jsonify({"success": False, "message": "Enter a valid parent email and phone number"}), 400
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

    save_store()
    send_push_notification(
        title="New Admission Application",
        body=f"{data.get('student_name', 'A student')} applied for {data.get('class_applying', 'a class')}",
        url="/admin-dashboard",
    )

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
    found = False
    for admission in store.get('admissions', []):
        if admission.get('id') == app_id:
            admission['is_read'] = 1
            found = True
            break
    if not found:
        return jsonify({"success": False, "message": "Application not found"}), 404
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
            for sub in get_store().get('applicant_push_subscriptions', {}).get(admission.get('application_number'), []):
                try:
                    from pywebpush import webpush
                    webpush(subscription_info=json.loads(sub), data=json.dumps({"title": "Application status updated", "body": f"Your application is now {status}.", "url": "/admission-dashboard"}), vapid_private_key=VAPID_PRIVATE_KEY, vapid_claims=VAPID_CLAIMS)
                except Exception as exc:
                    app.logger.warning('Applicant push failed: %s', exc)
            return jsonify({"success": True, "data": admission})
    return jsonify({"success": False, "message": "Application not found"}), 404


@app.route('/api/applicant/status', methods=['POST'])
def applicant_dashboard():
    data = request.get_json() or {}
    application_number = str(data.get('application_number', '')).strip().upper()
    parent_email = str(data.get('parent_email', '')).strip().casefold()
    if not application_number or not parent_email:
        return jsonify({"success": False, "message": "Application number and parent email are required"}), 400
    admission = next((item for item in get_store().get('admissions', [])
                      if item.get('application_number') == application_number
                      and str(item.get('parent_email', '')).strip().casefold() == parent_email), None)
    if not admission:
        # Do not reveal whether an application number exists to unauthenticated visitors.
        return jsonify({"success": False, "message": "No application matches those details"}), 404
    return jsonify({"success": True, "data": {
        "application_number": admission.get('application_number'),
        "student_name": admission.get('student_name'),
        "class_applying": admission.get('class_applying'),
        "status": admission.get('status', 'Submitted'),
        "submitted_at": admission.get('submitted_at'),
        "status_updated_at": admission.get('status_updated_at'),
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
    all_posts = get_store().get('posts', [])
    if session.get('admin_logged_in') and request.args.get('include') == 'all':
        posts = list(all_posts)
    else:
        posts = [p for p in all_posts
                 if p.get('status', 'published') == 'published'
                 and (not p.get('scheduled_for') or p['scheduled_for'] <= now)]
    posts = sorted(posts, key=lambda x: x.get('id', 0), reverse=True)
    return jsonify({"success": True, "data": posts})


@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    now = datetime.now().isoformat(timespec='minutes')
    post = next((p for p in get_store().get('posts', [])
                 if p.get('id') == post_id
                 and (session.get('admin_logged_in') or (
                     p.get('status', 'published') == 'published'
                     and (not p.get('scheduled_for') or p['scheduled_for'] <= now)
                 ))), None)
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
    if data.get('category', 'news') not in {'news', 'blog', 'event'}:
        return jsonify({"success": False, "message": "Invalid post category"}), 400
    if data.get('status', 'published') not in {'draft', 'published'}:
        return jsonify({"success": False, "message": "Invalid post status"}), 400

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
    if 'title' in data and not str(data['title']).strip():
        return jsonify({"success": False, "message": "Title is required"}), 400
    if 'content' in data and not str(data['content']).strip():
        return jsonify({"success": False, "message": "Content is required"}), 400
    if 'category' in data and data['category'] not in {'news', 'blog', 'event'}:
        return jsonify({"success": False, "message": "Invalid post category"}), 400
    if 'status' in data and data['status'] not in {'draft', 'published'}:
        return jsonify({"success": False, "message": "Invalid post status"}), 400
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
    port = int(os.getenv('PORT', 7000))
    app.run(host='0.0.0.0', port=port, debug=False)
