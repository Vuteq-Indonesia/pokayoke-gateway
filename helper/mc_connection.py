import time
import pymcprotocol
from tools.register import PLC_REGISTERS


class PLCConnector:
    def __init__(self, ip="192.168.63.254", port=5040, timeout=5, ui=None):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.mc = pymcprotocol.Type3E()
        self.connected = False
        self.ui = ui  # <<<< tambahan

    def log(self, message: str):
        """Kirim log ke UI kalau ada, kalau tidak fallback ke print"""
        if self.ui:
            self.ui.write_log(message)
        else:
            print(message)

    def connect(self):
        """Coba koneksi ke PLC (sekali saja)"""
        try:
            self.mc.setaccessopt(commtype="binary")
            self.mc.timeout = self.timeout

            self.log(f"🔄 Mencoba koneksi ke PLC {self.ip}:{self.port} ...")
            self.mc.connect(self.ip, self.port)

            self.connected = True
            self.log("✅ Terhubung ke PLC!")

            # Reset register setelah connect
            self.reset_registers()
            return True

        except Exception as e:
            self.connected = False
            self.log(f"❌ Gagal konek PLC {self.ip}:{self.port}: {e}")
            return False

    def auto_connect(self):
        """Loop auto-reconnect dengan delay 3 detik"""
        while True:
            if not self.connected:
                if self.connect():
                    self.log("🔗 PLC siap dipakai")
            time.sleep(3)

    def reset_registers(self):
        """Reset semua register ke 0"""
        already_reset = set()
        for group, items in PLC_REGISTERS.items():
            for regmap in items:
                for key in ["reg", "button", "lamp"]:
                    device = regmap[key]
                    if device not in already_reset:
                        try:
                            self.batch_write(device, [0])
                            already_reset.add(device)
                        except Exception as e:
                            self.log(f"⚠️ Gagal reset {device}: {e}")
        self.log("♻️ Semua register direset ke 0")

    def batch_write(self, device, values):
        """Tulis data ke PLC"""
        if device is None:
            self.log("⚠️ Device kosong, skip write")
            return False
        if not self.connected:
            self.log("⚠️ PLC belum terkoneksi!")
            return False
        try:
            self.mc.batchwrite_wordunits(headdevice=device, values=values)
            self.log(f"✍️ Write {values} ke {device} sukses")
            return True
        except (OSError, TimeoutError) as e:
            # error komunikasi
            self.connected = False
            self.log(f"❌ Koneksi ke PLC hilang saat write {device}: {e}")
            return False
        except Exception as e:
            # error logic (misalnya device None, format salah)
            self.log(f"⚠️ Error write ke {device}: {e}")
            return False

    def batch_read(self, device, size):
        """Baca data dari PLC"""
        if not self.connected:
            self.log("⚠️ PLC belum terkoneksi!")
            return None
        try:
            values = self.mc.batchread_wordunits(headdevice=device, readsize=size)
            self.log(f"📖 Read {device} ({size}): {values}")
            return values
        except Exception as e:
            self.connected = False  # tandai lost connection
            self.log(f"❌ Gagal read {device}: {e}")
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
                self.log(f"⚠️ Mode {mode} tidak dikenal")
                return False
            return True
        except Exception as e:
            self.log(f"❌ Gagal reset_and_write {reg_device}/{off_device}: {e}")
            return False
