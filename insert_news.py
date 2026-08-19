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



POSTS = [
    {
        "category": "news",
        "title": "Primary School Graduation 2026 - A Resounding Success",
        "content": "We are delighted to announce that our primary school graduation ceremony was a resounding success! Congratulations to all our graduating pupils on this wonderful milestone. We are incredibly proud of their hard work, dedication, and achievements throughout their primary school journey. We wish them continued success as they transition to the next stage of their education.",
    },
    {
        "category": "news",
        "title": "Summer Coaching Begins 10th of August",
        "content": "Our summer coaching programme will commence on the 10th of August. Students are encouraged to take part in this enriching programme designed to reinforce their learning, keep them engaged, and prepare them for the upcoming academic session. Please contact the school office for more details on how to register.",
    },
    {
        "category": "news",
        "title": "School Resumes in September",
        "content": "SS. Joachim and Anne Catholic School will resume the new academic session in September. All students and parents are kindly reminded to prepare for the new term and ensure all requirements are met before resumption. We look forward to welcoming everyone back for another exciting and productive term.",
    },
    {
        "category": "news",
        "title": "Students Begin Their Long Vacation",
        "content": "Our students have officially entered their long vacation! We wish all our students a safe, restful, and enjoyable holiday. We encourage them to relax, spend quality time with family, and use the break to pursue their hobbies and interests. We look forward to seeing them energized and ready for the new session in September.",
    },
]


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
