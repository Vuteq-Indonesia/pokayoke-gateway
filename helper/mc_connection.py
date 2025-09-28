import threading
import time

import docker
import pymcprotocol
import requests

from tools.register import PLC_REGISTERS


class PLCConnector:
    def __init__(self, ip="192.168.63.254", port=5040, timeout=5):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.mc = pymcprotocol.Type3E()
        self.connected = False
        self.listener_thread = None
        self.stop_listener = False

    def connect(self):
        """Coba koneksi ke PLC (sekali saja)"""
        try:
            self.mc.setaccessopt(commtype="binary")
            self.mc.timeout = self.timeout

            print(f"🔄 Mencoba koneksi ke PLC {self.ip}:{self.port} ...")
            self.mc.connect(self.ip, self.port)

            self.connected = True
            print("✅ Terhubung ke PLC!")

            # Reset register setelah connect
            self.reset_registers()

            # Jalankan listener D10
            if not self.listener_thread or not self.listener_thread.is_alive():
                self.stop_listener = False
                self.listener_thread = threading.Thread(
                    target=self.listen_d10, daemon=True
                )
                self.listener_thread.start()

            return True

        except Exception as e:
            self.connected = False
            print(f"❌ Gagal konek PLC {self.ip}:{self.port}: {e}")
            return False
    def auto_connect(self):
        while True:
            if not self.connected:
                if self.connect():
                    print("🔗 PLC siap dipakai")
            time.sleep(3)
    def listen_d10(self):
        """Listener cek D10, jika 1 maka reboot"""
        print("👂 Listener D10 aktif...")
        while not self.stop_listener:
            try:
                values = self.batch_read("D10", 1)
                if values and values[0] == 1:
                    print("⚡ D10 terdeteksi = 1 → Reboot sistem...")
                    # sys.exit(1)
                    client = docker.from_env()

                    # ambil container berdasarkan name
                    container = client.containers.get("pokayoke-gateway")
                    container.restart()
                    break  # stop loop setelah reboot dipanggil
            except Exception as e:
                print(f"⚠️ Listener error: {e}")
            time.sleep(2)  # cek tiap 2 detik
    def stop_listening(self):
        """Stop listener secara manual"""
        self.stop_listener = True
        if self.listener_thread:
            self.listener_thread.join(timeout=1)
            print("🛑 Listener D10 berhenti.")
    def reset_registers(self):
        """Booting animation lalu reset semua register ke 0"""
        already_reset = set()

        # 🔹 Booting animation
        try:
            self.batch_write("D5", [5])
            self.batch_write("D6", [6])
            self.batch_write("D1", [1])
            print("🚀 Booting... (D5=5, D6=6, D1=1)")
        except Exception as e:
            print(f"⚠️ Gagal set animasi booting: {e}")

        # Tunggu 5 detik
        time.sleep(5)

        # Reset nilai animasi ke 0
        try:
            self.batch_write("D5", [0])
            self.batch_write("D6", [0])
            self.batch_write("D1", [0])
            print("🔄 Booting selesai, D5/D6/D1 direset ke 0")
        except Exception as e:
            print(f"⚠️ Gagal reset animasi booting: {e}")

        # 🔹 Reset semua register dari PLC_REGISTERS
        for group, items in PLC_REGISTERS.items():
            for regmap in items:
                for key in ["reg", "button", "lamp"]:
                    device = regmap.get(key)
                    if device and device not in already_reset:
                        try:
                            self.batch_write(device, [0])
                            already_reset.add(device)
                        except Exception as e:
                            print(f"⚠️ Gagal reset {device}: {e}")
        # 🔹 Reset D10 terakhir
        try:
            self.batch_write("D10", [0])
            print("✅ D10 direset ke 0")
            # 🔹 Post ke API setelah D10 reset
            try:
                resp = requests.post("http://103.103.23.26:1000/v1/lamp/init-check", timeout=5)
                print(f"🌐 API response {resp.status_code}: {resp.text}")
            except Exception as e:
                print(f"⚠️ Gagal call API init-check: {e}")
        except Exception as e:
            print(f"⚠️ Gagal reset D10: {e}")

        print("♻️ Semua register direset ke 0")
    def batch_write(self, device, values):
        if device is None:
            print("⚠️ Device kosong, skip write")
            return False
        if not self.connected:
            print("⚠️ PLC belum terkoneksi!")
            return False
        try:
            self.mc.batchwrite_wordunits(headdevice=device, values=values)
            print(f"✍️ Write {values} ke {device} sukses")
            return True
        except (OSError, TimeoutError) as e:
            # error komunikasi
            self.connected = False
            print(f"❌ Koneksi hilang saat write {device}: {e}")
            return False
        except Exception as e:
            # error logic (misal device/format salah)
            print(f"⚠️ Error write ke {device}: {e}")
            return False
    def batch_read(self, device, size):
        """Baca data dari PLC"""
        if not self.connected:
            print("⚠️ PLC belum terkoneksi!")
            return None
        try:
            values = self.mc.batchread_wordunits(headdevice=device, readsize=size)
            print(f"📖 Read {device} ({size}): {values}")
            return values
        except Exception as e:
            self.connected = False  # tandai lost connection
            print(f"❌ Gagal read {device}: {e}")
            return None
    def reset_and_write(self, reg_device, off_device, index, mode="on"):
        """Helper untuk reset dan tulis ke register/lampu"""
        try:
            if mode == "on":
                self.batch_write(reg_device, [0])
                self.batch_write(off_device, [0])
                self.batch_write(reg_device, [index])
            elif mode == "off":
                self.batch_write(off_device, [0])
                self.batch_write(reg_device, [0])
                self.batch_write(off_device, [index])
            else:
                print(f"⚠️ Mode {mode} tidak dikenal")
                return False
            return True
        except Exception as e:
            print(f"❌ Gagal reset_and_write {reg_device}/{off_device}: {e}")
            return False
