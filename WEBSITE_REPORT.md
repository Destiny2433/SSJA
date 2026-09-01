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

## 4. Important implementation notes

- Firestore is now the only application data store; SQLite has been removed.
- The application keeps a working in-memory copy of the Firestore document and synchronizes changes back to Firestore.
- Default gallery items are seeded when the Firestore gallery is empty.
- Uploaded files are currently written to the server filesystem while their paths are stored in Firestore.

## 5. Items to verify before handover

1. Change the default administrator password from `admin123`.
2. Confirm the Firebase service-account credential is not committed or publicly exposed.
3. Configure a strong production `SECRET_KEY`.
4. Move uploads to Firebase Storage or another persistent storage service.
5. Add upload file-size, extension, and MIME-type validation.
6. Test contact messages on the deployed server.
7. Test admission submissions, document uploads, and applicant tracking.
8. Test gallery uploads and deletion from the dashboard.
9. Test news creation, editing, scheduling, and deletion.
10. Confirm the external portal and map links belong to the school.
11. Replace placeholder social-media links with the school’s real profiles.
12. Confirm all owner-provided names, photographs, dates, contact details, fees, and academic content.

## 6. Recommended next features

### High priority

- Firebase Storage integration for permanent media files.
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

## 7. Handover recommendation

The website has a strong functional foundation and is suitable for an owner review. Before public launch, the most important tasks are securing the administrator account, making uploads persistent, validating forms/uploads, and completing a live deployment test of all admin workflows.
