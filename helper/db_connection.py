import pg8000
from pg8000.exceptions import InterfaceError, DatabaseError


def api_check_postgres():
    try:
        conn = pg8000.connect(
            user="it_user",
            password="VuteqIt2025",
            database="junbiki_db",
            host="10.10.10.35",
            port=5432,
        )
        cur = conn.cursor()
        cur.execute("SELECT NOW();")
        now = cur.fetchone()[0]

        cur.close()
        conn.close()

        return True

    except (InterfaceError, DatabaseError) as e:
        print(f"❌ Database connection failed: {e}")
        return False
