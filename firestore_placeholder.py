from copy import deepcopy
from pathlib import Path

from werkzeug.security import generate_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

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


PLACEHOLDER_POSTS = [
    {
        "id": 1,
        "title": "Back-to-School Preparation Begins for the New Academic Session",
        "category": "news",
        "content": "SS Joachim and Anne Catholic School is preparing for the new academic session with a renewed focus on excellence, discipline, and joyful learning. Parents are encouraged to complete all required documentation and ensure their children are ready for the term ahead.",
        "image_path": "images/logo.png",
        "date": "2026-08-16",
    },
    {
        "id": 2,
        "title": "Inter-House Sports Competition Returns This Term",
        "category": "event",
        "content": "We are excited to welcome students, parents, and the wider school community to the Inter-House Sports Competition. This event celebrates teamwork, fitness, and school spirit in a vibrant, family-friendly atmosphere.",
        "image_path": "images/sprot.jpeg",
        "date": "2026-08-20",
    },
    {
        "id": 3,
        "title": "Learning in Action: Classroom Innovation and Student Growth",
        "category": "news",
        "content": "Across the school, teachers are guiding students through engaging, practical lessons that connect classroom learning with real-world experiences. Our focus remains on curiosity, creativity, and confidence.",
        "image_path": "images/EXCURSION.jpeg",
        "date": "2026-08-24",
    },
    {
        "id": 4,
        "title": "Open Day and Parent Engagement Forum",
        "category": "event",
        "content": "Parents are invited to an upcoming Open Day and engagement forum designed to strengthen communication between home and school. The event will showcase student progress, school activities, and future opportunities for partnership.",
        "image_path": "images/hero-bg.jpg",
        "date": "2026-09-02",
    },
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




def get_placeholder_store():
    admin_hash = generate_password_hash("admin123")
    store = {
        "admins": [
            {
                "id": 1,
                "username": "admin",
                "password_hash": admin_hash,
            }
        ],
        "content": [],
        "gallery": [],
        "messages": [],
        "admissions": [],
        "posts": deepcopy(PLACEHOLDER_POSTS),
        "push_subscriptions": [],
    }
    return deepcopy(store)
