# TODO - PostgreSQL migration (SS JOACIM)

## Plan
- [ ] Gather current DB usage in app.py (already inspected)
- [ ] Create PostgreSQL config (env vars with defaults) in app.py
- [ ] Replace sqlite3 usage with psycopg2 usage
- [ ] Implement DB schema creation (CREATE TABLE IF NOT EXISTS) for PostgreSQL
- [ ] Replace all SQL calls with PostgreSQL equivalents
- [ ] Ensure UPSERT / conflict handling matches PostgreSQL
- [x] Add dependency guidance (pip install psycopg2-binary)
- [x] Run a quick start test (python app.py) and validate login/content APIs



