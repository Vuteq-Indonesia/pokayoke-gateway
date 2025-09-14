import threading
import time

from helper.db_connection import api_check_postgres
from helper.mc_connection import PLCConnector
from helper.rmq_listener import RMQClient


def main():
    print("🚀 Starting Server...")

    # 1. Cek koneksi database
    print("🔍 Mengecek koneksi database...")
    if api_check_postgres():
        print("✅ Database OK")
    else:
        print("❌ Database gagal diakses, server tetap jalan tapi harap dicek!")

    # 2. Koneksi ke PLC
    print("🔌 Koneksi ke PLC...")
    plc = PLCConnector(ip="192.168.63.254", port=5040)
    if plc.connect():
        print("✅ PLC Connected")
    else:
        print("❌ Gagal konek PLC, akan coba auto-reconnect di background")

    # 3. Koneksi ke RabbitMQ
    rmq = RMQClient(
        broker_ip="10.10.10.10",
        broker_port=6572,
        queues_string="junbiki_inventory_lamp_test",
        username="junbiki",
        password="junbiki",
        plc_connector=plc
    )

    # Jalankan listener RMQ di thread terpisah
    def run_rmq():
        rmq.listen()

    rmq_thread = threading.Thread(target=run_rmq, daemon=True)
    rmq_thread.start()

    print("👂 Server siap menerima pesan dari RMQ...")

    # Loop utama (misalnya untuk monitoring)
    try:
        while True:
            time.sleep(5)
            # bisa tambahkan health check disini kalau perlu
    except KeyboardInterrupt:
        print("\n🛑 Server dihentikan manual.")


if __name__ == "__main__":
    main()
