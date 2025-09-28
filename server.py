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

    # Jalankan auto_connect di thread terpisah
    plc_thread = threading.Thread(target=plc.auto_connect, daemon=True)
    plc_thread.start()

    # Coba connect sekali (biar cepat tahu status awal)
    if plc.connect():
        print("✅ PLC Connected")
    else:
        print("❌ Gagal konek PLC, auto-reconnect jalan di background")

    # 3. Koneksi ke RabbitMQ
    rmq = RMQClient(
        broker_ip="103.103.23.26",
        broker_port=5672,  # default AMQP port
        queues_string="junbiki_inventory_lamp_test",
        username="ansei",
        password="ansei",
        plc_connector=plc
    )

    # Jalankan listener RMQ di thread terpisah
    rmq_thread = threading.Thread(target=rmq.listen, daemon=True)
    rmq_thread.start()

    print("👂 Server siap menerima pesan dari RMQ...")

    # Loop utama (misalnya untuk monitoring / health check)
    try:
        while True:
            time.sleep(5)
            # Contoh: bisa tambahkan log kesehatan koneksi
            if not plc.connected:
                print("⚠️ PLC belum terkoneksi, auto_connect masih mencoba...")
    except KeyboardInterrupt:
        print("\n🛑 Server dihentikan manual.")


if __name__ == "__main__":
    main()
