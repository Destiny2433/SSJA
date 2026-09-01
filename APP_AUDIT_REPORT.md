# Application Audit Report

## Completed improvements

- Fixed the Python syntax and indentation errors that prevented the server from importing.
- Kept the public site available if Firebase is unavailable, while clearly marking this as temporary in-memory storage.
- Added Google Search Console verification to every HTML page.
- Improved the applicant-status page with clear instructions, automatic uppercasing of application numbers, better status colours, and safe text rendering for applicant information.
- Added a configured local administrator username and strong password in `.env` (credentials are intentionally not repeated in this report).

## Applicant status flow

1. An applicant submits the admission form and receives an application number in the format `SJACS-YYYY-00001`.
2. The applicant visits `/admission-dashboard` or `/applicant-dashboard.html` and enters the application number plus the parent/guardian email used on the form.
3. The page securely calls the status endpoint and shows the name, class, submission date, and current decision only when both details match.
4. An administrator can update the application status from the admin dashboard.

## Visitor checks

The live public pages for Home, About, Academics, Admissions, Admission Form, News, Gallery, Contact, and JSS Subjects returned HTTP 200 during the audit.

## Deployment action required

The live health endpoint currently reports Firebase as unavailable and uses fallback storage. In that mode, form submissions and administrator changes can be lost when the server restarts. Set the Firebase credential and the following variables in the production host's environment before relying on the admin system:

- `SECRET_KEY`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `FIREBASE_CREDENTIAL_PATH` (or the host-specific Firebase credential configuration)

Do not commit `.env` or the Firebase service-account JSON file to a public repository.

## Remaining verification

The local Python launcher/virtual environment was unavailable during testing, so a full local server run could not be completed in this workspace. After restoring Python, run `python app.py`, submit a test application, and confirm that its status can be updated from the admin dashboard.
