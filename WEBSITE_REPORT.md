# SS Joachim and Anne Catholic School Website Report

## 1. Current website

The project is a multi-page school website with a public-facing site, an administrator dashboard, an admission application flow, a gallery, news/events, contact messaging, and applicant status tracking.

## 2. Technology used

- HTML, CSS, and vanilla JavaScript for the frontend.
- Bootstrap 5 for layout and responsive components.
- Font Awesome for icons.
- AOS for scroll animations.
- Python Flask for the backend and API routes.
- Firebase Admin SDK and Firestore for application data storage.
- Web Push notifications using VAPID and `pywebpush`.
- Service workers and manifests for progressive web app support.
- Gunicorn for production serving.

## 3. Current features

### Public website

- Home page with hero carousel, school highlights, counters, and latest posts.
- About page with school information, leadership, mission, vision, and dynamic images.
- Academics pages for curriculum, facilities, staff, anthem, rules, discipline, and JSS subjects.
- Admissions information and online admission form.
- Contact form and embedded school location map.
- Dynamic gallery with category filters and lightbox viewing.
- News, blog, and events listing with individual post pages.
- Applicant dashboard for checking application status.
- Responsive navigation and mobile layouts.
- PWA service-worker support.

### Admin dashboard

- Admin login and session protection.
- Global academic year and term settings.
- Editable About page content.
- Editable academic content.
- Priest, hero, About, prefect, and gallery image management.
- Gallery upload and deletion.
- News/blog/event publishing, editing, scheduling, and deletion.
- Contact message management.
- Admission application management and status updates.
- Notification count and browser push subscription support.
- PDF export support for administrative data.
- Save controls are now shown for every dashboard section.

## 4. Simple application architecture

- Visitors use a normal HTML website and do not see database, Firebase, or storage messages.
- Firestore works quietly behind the site as the database for admissions, messages, news, gallery records, and editable content.
- Uploaded images and admission documents are saved in `images/uploads`; their paths are stored with the related records.
- The admin dashboard is the only place for managing content and applications.
- If a backend service is temporarily unavailable, the public pages show a simple retry message rather than technical details.

## 5. Items to verify before handover

1. Change the default administrator password from `admin123`.
2. Confirm the Firebase service-account credential is not committed or publicly exposed.
3. Configure a strong production `SECRET_KEY`.
4. Add persistent disk or external file storage if deploying on a platform with ephemeral filesystems.
5. Add upload file-size, extension, and MIME-type validation.
6. Test contact messages on the deployed server.
7. Test admission submissions, document uploads, and applicant tracking.
8. Test gallery uploads and deletion from the dashboard.
9. Test news creation, editing, scheduling, and deletion.
10. Confirm the external portal and map links belong to the school.
11. Replace placeholder social-media links with the school’s real profiles.
12. Confirm all owner-provided names, photographs, dates, contact details, fees, and academic content.

## 6. Environment setup

Use a local `.env` file for development and Render Environment Variables for production. Never commit `.env`, Firebase credentials, or the VAPID private key.

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Long random value used to sign Flask sessions. |
| `ADMIN_USERNAME` | Administrator login name. |
| `ADMIN_PASSWORD` | Strong administrator login password. Use a different production password. |
| `SITE_URL` | Public site URL used for canonical links, sitemap, and robots output. |
| `FIREBASE_CREDENTIAL_PATH` | Local path to the Firebase service-account JSON file. |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Complete Firebase service-account JSON for Render. Prefer this over a file upload. |
| `FIREBASE_PROJECT_ID` | Firebase project identifier for documentation and deployment configuration. |
| `UPLOAD_FOLDER` | Optional local upload directory; defaults to `images/uploads`. |
| `VAPID_PUBLIC_KEY` | Public Web Push key sent to browsers during subscription. |
| `VAPID_PRIVATE_KEY` | Server-only Web Push signing key. Never expose it in HTML or JavaScript. |
| `VAPID_SUBJECT` | Administrator contact identity, for example `mailto:admin@example.com`. |

### Local setup

Copy `.env.example` to `.env`, fill in the values, place `firebase-service-account.json` in the project root, and ensure `images/uploads` is writable. Generate push keys with `python generate_vapid.py`, then put both printed keys in `.env`. Start with `python app.py` and check `http://127.0.0.1:7000/api/health`.

The configured `ADMIN_USERNAME` and `ADMIN_PASSWORD` are synchronized to the administrator record when the server starts. The admin session survives normal server restarts as long as `SECRET_KEY` stays unchanged. The administrator must use the dashboard's Logout button to end the session.

After a successful admin login, the session is kept for up to 10 years and is not automatically cleared by normal page navigation, refreshes, or push-notification setup. Changing `SECRET_KEY` invalidates old sessions because it protects the login cookie; keep it unchanged during ordinary restarts.

### Render setup

Add these variables in Render's Environment tab. Use your own production values; do not reuse the local password.

```text
SECRET_KEY=<long-random-production-secret>
ADMIN_USERNAME=<production-admin-username>
ADMIN_PASSWORD=<strong-production-password>
SITE_URL=https://your-render-domain.onrender.com
FIREBASE_SERVICE_ACCOUNT_JSON=<complete Firebase service-account JSON>
FIREBASE_PROJECT_ID=<Firebase project ID>
VAPID_PUBLIC_KEY=<generated VAPID public key>
VAPID_PRIVATE_KEY=<generated VAPID private key>
VAPID_SUBJECT=mailto:<monitored-school-email>
```

Do not set `FIREBASE_CREDENTIAL_PATH` on Render when using `FIREBASE_SERVICE_ACCOUNT_JSON`. Keep the existing `gunicorn app:app` start command. After deployment, check `/api/health`; Firestore must be connected and `push_notifications` must be `true` before relying on admissions or notifications. Uploaded files use the local filesystem, so use a persistent disk or external storage before deploying where files can be lost on restart.

### Push test

Push requires HTTPS in production, a supported browser, notification permission, valid VAPID keys, and an active service worker. Log into the admin dashboard once to register the admin browser. Look up an application in the applicant dashboard to register that applicant browser. Submit a contact/admission form to test admin notifications, then change an admission status to test applicant notifications.

## 7. Recommended next features

### High priority

- Persistent disk or external file storage for uploads on production hosts with ephemeral filesystems.
- Admin password change and password reset.
- Role-based admin accounts, such as editor, admissions officer, and super administrator.
- Firestore audit log showing who changed content and when.
- Strong server-side validation and rate limiting for public forms.
- Email notifications for new contact messages and admission applications.
- Automated backup/export of Firestore content.

### Useful for the school

- Timetable and academic calendar.
- School fees/payment status integration.
- Downloadable prospectus and school policy documents.
- Staff directory with department and contact information.
- Parent announcements and notification subscriptions.
- Search engine metadata editor and social sharing previews.
- Event registration and RSVP forms.
- FAQ page.
- Testimonials and alumni section.

### Long-term improvements

- Convert repeated static page sections into reusable templates.
- Add automated image compression and thumbnail generation.
- Add analytics and privacy-conscious visitor reporting.
- Add accessibility checks for keyboard navigation, contrast, labels, and alt text.
- Add automated tests for API routes and frontend forms.
- Add a staging environment before production deployment.

## 8. Handover recommendation

The website has a strong functional foundation and is suitable for an owner review. Before public launch, the most important tasks are securing the administrator account, making uploads persistent, validating forms/uploads, and completing a live deployment test of all admin workflows.
