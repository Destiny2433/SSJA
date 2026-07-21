import os
import json
import time

import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify, send_from_directory, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'joacim_super_secret_key'

UPLOAD_FOLDER = 'images/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- PostgreSQL Config (full switch) ---
# Use env vars if available; otherwise defaults from your prompt.
DB_HOST = os.getenv('DB_HOST', 'dpg-d98ddbvavr4c739booh0-a.oregon-postgres.render.com')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_USER = os.getenv('DB_USER', 'ssja_database_systemdb_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'KBoFTl9aAXEWLpKcfN2hz9bzLGUUgyij')
DB_NAME = os.getenv('DB_NAME', 'ssja_database_systemdb')


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME,
        cursor_factory=RealDictCursor,
        sslmode='require',
    )


# VAPID Keys for Push Notifications
# These keys are auto-generated. Do NOT share the private key.
VAPID_PUBLIC_KEY = "BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkvMeAtA3LFgDzkrxZJjSgSnfckjBJuBkr3qBUYIHBQFLXYp5Nksh8U"
VAPID_PRIVATE_KEY = "uycSJxLNFTqGfzxvLT1i2mTPJqB3mcZs29_mS4h6E6g"
VAPID_CLAIMS = {"sub": "mailto:admin@sjacs.edu.ng"}


def init_postgres():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS admins (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS content (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS gallery (
            id SERIAL PRIMARY KEY,
            category TEXT NOT NULL,
            image_path TEXT NOT NULL,
            title TEXT,
            description TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            name TEXT,
            email TEXT,
            subject TEXT,
            message TEXT,
            is_read INTEGER DEFAULT 0,
            submitted_at TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS admissions (
            id SERIAL PRIMARY KEY,
            student_name TEXT,
            date_of_birth TEXT,
            gender TEXT,
            class_applying TEXT,
            parent_name TEXT,
            parent_phone TEXT,
            parent_email TEXT,
            address TEXT,
            is_read INTEGER DEFAULT 0,
            submitted_at TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS push_subscriptions (
            id SERIAL PRIMARY KEY,
            subscription_json TEXT UNIQUE NOT NULL
        )
        """
    )

    # Seed admin user if not present
    cur.execute("SELECT 1 FROM admins WHERE username = %s", ('admin',))
    if not cur.fetchone():
        hashed_pw = generate_password_hash('admin123')
        cur.execute(
            "INSERT INTO admins (username, password_hash) VALUES (%s, %s)",
            ('admin', hashed_pw),
        )

    conn.commit()
    cur.close()
    conn.close()


init_postgres()


def send_push_notification(title, body, url='/admin-dashboard'):
    """Send push notification to all subscribed admin devices."""
    try:
        from pywebpush import webpush

        conn = get_db_connection()
        subs = conn.cursor().execute(
            "SELECT subscription_json FROM push_subscriptions"
        )
        # Fetch rows with a separate cursor to avoid mixing execute/fetchall patterns
        cur = conn.cursor()
        cur.execute("SELECT subscription_json FROM push_subscriptions")
        rows = cur.fetchall()
        conn.close()

        for (subscription_json,) in rows:
            try:
                subscription_info = json.loads(subscription_json)
                webpush(
                    subscription_info=subscription_info,
                    data=json.dumps({"title": title, "body": body, "url": url}),
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims=VAPID_CLAIMS,
                )
            except Exception as e:
                print(f"Push failed for subscription: {e}")
    except ImportError:
        print("pywebpush not installed. Skipping push notifications.")


# --- Static File Routes ---
PAGES = [
    'index', 'about', 'academics', 'admissions', 'admission-form',
    'pay-fees', 'gallery', 'contact', 'admin', 'admin-dashboard'
]


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/<page>')
def serve_page(page):
    if page in PAGES:
        return send_from_directory('.', f'{page}.html')
    if page.endswith(('.py', '.db', '.md')) or page.startswith('.'):
        return "Forbidden", 403
    return send_from_directory('.', page)


@app.route('/<path:filename>')
def serve_static(filename):
    if filename.endswith(('.py', '.db', '.md')) or filename.startswith('.'):
        return "Forbidden", 403
    return send_from_directory('.', filename)


# --- Auth ---
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json() or {}
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM admins WHERE username = %s', (data.get('username'),))
        admin = cur.fetchone()
        conn.close()

        if admin and check_password_hash(admin['password_hash'], data.get('password', '')):
            session['admin_logged_in'] = True
            return jsonify({"success": True})

        return jsonify({"success": False, "message": "Invalid username or password"}), 401
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('admin_logged_in', None)
    return jsonify({"success": True})


# --- Push Subscriptions ---
@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    if not session.get('admin_logged_in'):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    sub_json = json.dumps(data.get('subscription'))

    conn = get_db_connection()
    cur = conn.cursor()
    # PostgreSQL equivalent of INSERT OR IGNORE
    cur.execute(
        """
        INSERT INTO push_subscriptions (subscription_json)
        VALUES (%s)
        ON CONFLICT (subscription_json) DO NOTHING
        """,
        (sub_json,),
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Subscribed to push notifications"})


@app.route('/api/vapid-public-key', methods=['GET'])
def get_vapid_key():
    return jsonify({"publicKey": VAPID_PUBLIC_KEY})


# --- Content ---
@app.route('/api/content', methods=['GET'])
def get_all_content():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute('SELECT * FROM content')
    rows = cur.fetchall()

    cur.execute('SELECT * FROM gallery ORDER BY id DESC')
    gallery_rows = cur.fetchall()

    conn.close()

    content = {row['key']: row['value'] for row in rows}
    content['gallery'] = [
        {
            "id": r["id"],
            "category": r["category"],
            "image_path": r["image_path"],
            "title": r.get("title") or "",
            "description": r.get("description") or "",
        }
        for r in gallery_rows
    ]

    return jsonify({"success": True, "data": content})


@app.route('/api/content', methods=['POST'])
def update_content():
    if not session.get('admin_logged_in'):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}

    conn = get_db_connection()
    cur = conn.cursor()

    for key, value in data.items():
        if key == 'gallery':
            continue

        cur.execute(
            """
            INSERT INTO content (key, value)
            VALUES (%s, %s)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
            """,
            (key, str(value)),
        )

    conn.commit()
    conn.close()

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

    conn = get_db_connection()
    cur = conn.cursor()

    if key == 'gallery':
        category = request.form.get('category', 'all')
        title = request.form.get('title', '')
        cur.execute(
            """
            INSERT INTO gallery (category, image_path, title, description)
            VALUES (%s, %s, %s, %s)
            """,
            (category, relative_path, title, ''),
        )
    else:
        cur.execute(
            """
            INSERT INTO content (key, value)
            VALUES (%s, %s)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
            """,
            (key, relative_path),
        )

    conn.commit()
    conn.close()

    return jsonify({"success": True, "path": relative_path})


@app.route('/api/gallery/<int:item_id>', methods=['DELETE'])
def delete_gallery_item(item_id):
    if not session.get('admin_logged_in'):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM gallery WHERE id = %s', (item_id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})


# --- Contact Form ---
@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.get_json() or {}
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO messages (name, email, subject, message, submitted_at) VALUES (%s, %s, %s, %s, %s)',
        (
            data.get('name'),
            data.get('email'),
            data.get('subject'),
            data.get('message'),
            timestamp,
        ),
    )
    conn.commit()
    conn.close()

    send_push_notification(
        title="📩 New Contact Message",
        body=f"From {data.get('name', 'Someone')}: {data.get('subject', 'No subject')}",
        url="/admin-dashboard",
    )

    return jsonify({"success": True, "message": "Message received!"})


@app.route('/api/messages', methods=['GET'])
def get_messages():
    if not session.get('admin_logged_in'):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM messages ORDER BY id DESC')
    rows = cur.fetchall()
    conn.close()

    return jsonify({"success": True, "data": [dict(r) for r in rows]})


@app.route('/api/messages/<int:msg_id>/read', methods=['POST'])
def mark_message_read(msg_id):
    if not session.get('admin_logged_in'):
        return jsonify({"success": False}), 401

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE messages SET is_read = 1 WHERE id = %s', (msg_id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})


# --- Admission Form ---
@app.route('/api/admissions', methods=['POST'])
def submit_admission():
    data = request.get_json() or {}
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO admissions
            (student_name, date_of_birth, gender, class_applying, parent_name, parent_phone, parent_email, address, submitted_at)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            data.get('student_name'),
            data.get('date_of_birth'),
            data.get('gender'),
            data.get('class_applying'),
            data.get('parent_name'),
            data.get('parent_phone'),
            data.get('parent_email'),
            data.get('address'),
            timestamp,
        ),
    )
    conn.commit()
    conn.close()

    send_push_notification(
        title="🎓 New Admission Application",
        body=f"{data.get('student_name', 'A student')} applied for {data.get('class_applying', 'a class')}",
        url="/admin-dashboard",
    )

    return jsonify({"success": True, "message": "Application submitted successfully!"})


@app.route('/api/admissions', methods=['GET'])
def get_admissions():
    if not session.get('admin_logged_in'):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM admissions ORDER BY id DESC')
    rows = cur.fetchall()
    conn.close()

    return jsonify({"success": True, "data": [dict(r) for r in rows]})


@app.route('/api/admissions/<int:app_id>/read', methods=['POST'])
def mark_admission_read(app_id):
    if not session.get('admin_logged_in'):
        return jsonify({"success": False}), 401

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE admissions SET is_read = 1 WHERE id = %s', (app_id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})


# --- Notification Count ---
@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    if not session.get('admin_logged_in'):
        return jsonify({"success": False}), 401

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute('SELECT COUNT(*) AS c FROM messages WHERE is_read = 0')
    unread_messages = cur.fetchone()['c']

    cur.execute('SELECT COUNT(*) AS c FROM admissions WHERE is_read = 0')
    unread_admissions = cur.fetchone()['c']

    conn.close()

    return jsonify(
        {
            "success": True,
            "unread_messages": unread_messages,
            "unread_admissions": unread_admissions,
            "total": unread_messages + unread_admissions,
        }
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

