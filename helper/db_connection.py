import os
from dotenv import load_dotenv
import pg8000
from pg8000.exceptions import InterfaceError, DatabaseError


def api_check_postgres():
    """Cek koneksi ke PostgreSQL berdasarkan konfigurasi di .env"""
    # Load environment variables
    load_dotenv()

    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "postgres")
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", 5432))

    try:
        conn = pg8000.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            host=DB_HOST,
            port=DB_PORT,
        )
        cur = conn.cursor()
        cur.execute("SELECT NOW();")
        now = cur.fetchone()[0]

        cur.close()
        conn.close()

        print(f"✅ Database connected: {DB_NAME} ({now})")
        return True

    except (InterfaceError, DatabaseError) as e:
        print(f"❌ Database connection failed: {e}")
        return False
