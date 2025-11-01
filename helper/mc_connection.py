import asyncio
import threading
import time

import docker
import httpx
import pymcprotocol
import requests

from tools.register import PLC_REGISTERS


def int_to_button_name(value: int) -> str | None:
    """Konversi nilai integer PLC ke nama tombol (misal 225 -> E1, 3600 -> E10)."""
    if value <= 0:
        return None
    return hex(value)[2:].upper()  # contoh: 225 -> "E1"

async def send_lamp_disable(btn_code):
    if btn_code.startswith("E"):
        url = "http://103.103.23.26:1000/v1/lamp/disable"
        payload = {"lampId": btn_code}
        async with httpx.AsyncClient(timeout=3) as client:
            res = await client.post(url, json=payload)
            print(f"🌐 API {btn_code} -> {res.status_code}")

import threading
import time
import pymcprotocol

class PLCConnector:
    def __init__(self, ip="192.168.63.254", port=5040, timeout=5):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.mc = pymcprotocol.Type3E()
        self.connected = False
        self.listener_thread = None
        self.button_thread = None
        self.stop_listener = False
        self.auto_reconnect = True  # tambahan opsional
        self.auto_connect_running = False

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
            if not getattr(self, "listener_thread", None) or not self.listener_thread.is_alive():
                self.stop_listener = False
                self.listener_thread = threading.Thread(
                    target=self.listen_d10,
                    daemon=True
                )
                self.listener_thread.start()
                print("▶️ Listener D10 dimulai...")

            # Jalankan listener tombol (E, F, dll)
            if not getattr(self, "button_thread", None) or not self.button_thread.is_alive():
                self.stop_listener = False
                self.button_thread = threading.Thread(
                    target=self.listen_button,
                    daemon=True
                )
                self.button_thread.start()
                print("▶️ Listener tombol dimulai...")

            return True

        except Exception as e:
            self.connected = False
            print(f"❌ Gagal konek PLC {self.ip}:{self.port}: {e}")
            return False

    def disconnect(self):
        """Putuskan koneksi dan hentikan listener"""
        self.stop_listener = True
        self.connected = False
        try:
            self.mc.close()
            print("🔌 Koneksi ke PLC diputus.")
        except Exception as e:
            print(f"⚠️ Gagal menutup koneksi PLC: {e}")

    def auto_connect(self, interval=5):
        if self.auto_connect_running:
            return  # biar tidak dobel

        self.auto_connect_running = True
        while self.auto_reconnect:
            if not self.connected:
                print("⚠️ PLC belum terkoneksi, mencoba ulang...")
                self.connect()
            time.sleep(interval)

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
    def reset_button(self, reg_device):
        try:
            self.batch_write(reg_device, [0])
            return True
        except Exception as e:
            print(f"❌ Gagal reset_and_write {reg_device}: {e}")
            return False
    def listen_button(self):
        """Listener tombol: baca nilai dari PLC, konversi int->hex code, trigger lampu & API"""
        print("👂 Listener tombol (HEX konversi + API) aktif...")

        # kumpulkan semua address yang punya field "button"
        button_addrs = []
        for group, items in PLC_REGISTERS.items():
            for item in items:
                if item["button"] and item["button"] not in button_addrs:
                    button_addrs.append(item["button"])

        print(f"🔎 Memantau {len(button_addrs)} register tombol:", button_addrs)

        # simpan status terakhir tombol
        last_state = {addr: 0 for addr in button_addrs}

        while not self.stop_listener:
            try:
                values = self.batch_read(button_addrs, len(button_addrs))
                if not values:
                    continue

                for addr, val in zip(button_addrs, values):
                    prev = last_state.get(addr, 0)
                    last_state[addr] = val

                    # --- deteksi "baru ditekan" (rising edge) ---
                    if val != 0 and prev == 0:
                        btn_code = int_to_button_name(val)
                        if not btn_code:
                            continue

                        print(f"🔘 Tombol {btn_code} terdeteksi di {addr} (value={val})")

                        # cari item dengan code yang sama
                        found = None
                        for group, items in PLC_REGISTERS.items():
                            for item in items:
                                if item["code"].upper() == btn_code.upper():
                                    found = item
                                    break
                            if found:
                                break

                        # aksi 1: kirim API jika tombol E*
                        asyncio.create_task(send_lamp_disable(btn_code))

                        # reset tombol di PLC agar tidak terbaca lagi
                        self.reset_button(addr)

                    # --- tombol dilepas (val = 0) ---
                    elif val == 0 and prev != 0:
                        last_state[addr] = 0  # reset siap baca lagi

            except Exception as e:
                print(f"⚠️ Listener tombol error: {e}")

            time.sleep(0.1)

