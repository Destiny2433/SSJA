"""One-off script to insert the 4 requested news posts into the posts table."""
import time

from firestore_placeholder import get_placeholder_store

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






def main():
    conn = get_db_connection()
    cur = conn.cursor()
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

    inserted = []
    for post in POSTS:
        cur.execute(
            """
            INSERT INTO posts (title, category, content, image_path, date)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (post["title"], post["category"], post["content"], '', timestamp),
        )
        inserted.append(post["title"])
        print(f"Inserted: {post['title']}")

    conn.commit()
    cur.close()
    conn.close()

    print(f"\nSuccessfully inserted {len(inserted)} news posts.")


if __name__ == '__main__':
    main()
