import threading
import time
import os
from dotenv import load_dotenv

from helper.db_connection import api_check_postgres
from helper.mc_connection import PLCConnector
from helper.rmq_listener import RMQClient


def main():
    print("🚀 Starting Server...")

    # === 1. Load environment variables ===
    load_dotenv()

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "postgres")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

    PLC_IP = os.getenv("PLC_IP", "192.168.63.254")
    PLC_PORT = int(os.getenv("PLC_PORT", "5040"))

    RMQ_HOST = os.getenv("RMQ_HOST", "103.103.23.26")
    RMQ_PORT = int(os.getenv("RMQ_PORT", "5672"))
    RMQ_QUEUE = os.getenv("RMQ_QUEUE", "junbiki_inventory_lamp_test")
    RMQ_USER = os.getenv("RMQ_USER", "ansei")
    RMQ_PASS = os.getenv("RMQ_PASS", "ansei")

    # === 2. Cek koneksi database ===
    print("🔍 Mengecek koneksi database...")
    if api_check_postgres():
        print("✅ Database OK")
    else:
        print("❌ Database gagal diakses, server tetap jalan tapi harap dicek!")

    # === 3. Koneksi ke PLC ===
    print(f"🔌 Koneksi ke PLC {PLC_IP}:{PLC_PORT} ...")
    plc = PLCConnector(ip=PLC_IP, port=PLC_PORT)

    # Jalankan auto_connect di thread terpisah
    plc_thread = threading.Thread(target=plc.auto_connect, daemon=True)
    plc_thread.start()

    # Coba connect sekali (biar cepat tahu status awal)
    if plc.connect():
        print("✅ PLC Connected")
    else:
        print("❌ Gagal konek PLC, auto-reconnect jalan di background")

    # === 4. Koneksi ke RabbitMQ ===
    rmq = RMQClient(
        broker_ip=RMQ_HOST,
        broker_port=RMQ_PORT,
        queues_string=RMQ_QUEUE,
        username=RMQ_USER,
        password=RMQ_PASS,
        plc_connector=plc
    )

    # Jalankan listener RMQ di thread terpisah
    rmq_thread = threading.Thread(target=rmq.listen, daemon=True)
    rmq_thread.start()

    print("👂 Server siap menerima pesan dari RMQ...")

    # === 5. Loop utama (monitoring / health check) ===
    try:
        while True:
            time.sleep(5)
            if not plc.connected:
                print("⚠️ PLC belum terkoneksi, auto_connect masih mencoba...")
    except KeyboardInterrupt:
        print("\n🛑 Server dihentikan manual.")


if __name__ == "__main__":
    main()
