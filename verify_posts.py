import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host='dpg-d98ddbvavr4c739booh0-a.oregon-postgres.render.com',
    port=5432,
    user='ssja_database_systemdb_user',
    password='KBoFTl9aAXEWLpKcfN2hz9bzLGUUgyij',
    dbname='ssja_database_systemdb',
    cursor_factory=RealDictCursor,
    sslmode='require',
)
cur = conn.cursor()
cur.execute('SELECT id, title, category, length(content) AS len FROM posts ORDER BY id DESC')
rows = cur.fetchall()
print('count', len(rows))
for r in rows:
    print(r['id'], '|', r['category'], '|', r['len'], '|', r['title'])
conn.close()
