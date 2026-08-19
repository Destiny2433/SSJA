import os
from dotenv import load_dotenv

load_dotenv()

FIREBASE_CREDENTIAL_PATH = os.environ.get(
    'FIREBASE_CREDENTIAL_PATH',
    'destiny-c7cd4-firebase-adminsdk-ad232-3fdac99d15.json'
)

_firestore_client = None

try:
    import firebase_admin
    from firebase_admin import credentials, firestore as fs
except ImportError:
    firebase_admin = None
    credentials = None
    fs = None


cur.execute('SELECT id, title, category, length(content) AS len FROM posts ORDER BY id DESC')
rows = cur.fetchall()
print('count', len(rows))
for r in rows:
    print(r['id'], '|', r['category'], '|', r['len'], '|', r['title'])
conn.close()
