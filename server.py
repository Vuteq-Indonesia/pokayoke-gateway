import threading
import time
import tkinter as tk
import customtkinter as ctk
from tkinter.scrolledtext import ScrolledText

from helper.db_connection import api_check_postgres
from helper.mc_connection import PLCConnector
from helper.rmq_listener import RMQClient


class LogUI:
    def __init__(self):
        # Setup dasar
        ctk.set_appearance_mode("dark")  # "light" atau "dark"
        ctk.set_default_color_theme("blue")  # tema: "blue", "green", "dark-blue"

        self.root = ctk.CTk()
        self.root.title("Server Monitor")
        self.root.geometry("800x500")

        # Frame utama
        frame = ctk.CTkFrame(self.root, corner_radius=15)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Judul
        self.label = ctk.CTkLabel(frame, text="Vuteq Digital Light Picking System (Gateway)", font=("Consolas", 20, "bold"))
        self.label.pack(pady=(10, 5))

        # Area log
        self.log_area = ScrolledText(frame, wrap="word", font=("Consolas", 12), bg="#1E1E1E", fg="#FFFFFF")
        self.log_area.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_area.config(state="disabled")

        # Tombol stop
        self.stop_btn = ctk.CTkButton(frame, text="🛑 Stop Server", command=self.stop_server, fg_color="red")
        self.stop_btn.pack(pady=10)

        self.running = True

    def write_log(self, message: str):
        """Tambahkan log ke UI"""
        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, f"{time.strftime('%H:%M:%S')} | {message}\n")
        self.log_area.see(tk.END)  # auto-scroll
        self.log_area.config(state="disabled")

    def stop_server(self):
        self.running = False
        self.write_log("🛑 Server dihentikan manual.")
        self.root.quit()

    def run(self, main_fn):
        # Jalankan main di thread terpisah
        threading.Thread(target=main_fn, args=(self,), daemon=True).start()
        self.root.mainloop()


# Modifikasi main agar bisa kirim log ke UI
def main(ui: LogUI):
    ui.write_log("🚀 Starting Server...")

    # 1. Cek koneksi database
    ui.write_log("🔍 Mengecek koneksi database...")
    if api_check_postgres():
        ui.write_log("✅ Database OK")
    else:
        ui.write_log("❌ Database gagal diakses, server tetap jalan tapi harap dicek!")

    # 2. Koneksi ke PLC
    ui.write_log("🔌 Koneksi ke PLC...")
    plc = PLCConnector(ip="192.168.63.254", port=5040, ui=ui)

    plc_thread = threading.Thread(target=plc.auto_connect, daemon=True)
    plc_thread.start()

    if plc.connect():
        ui.write_log("✅ PLC Connected")
    else:
        ui.write_log("❌ Gagal konek PLC, auto-reconnect jalan di background")

    # 3. Koneksi ke RabbitMQ
    rmq = RMQClient(
        broker_ip="10.10.10.10",
        broker_port=5672,
        queues_string="junbiki_inventory_lamp_test",
        username="ansei",
        password="ansei",
        plc_connector=plc,
        ui=ui
    )

    rmq_thread = threading.Thread(target=rmq.listen, daemon=True)
    rmq_thread.start()

    ui.write_log("👂 Server siap menerima pesan dari RMQ...")

    try:
        while ui.running:
            time.sleep(5)
            if not plc.connected:
                ui.write_log("⚠️ PLC belum terkoneksi, auto_connect masih mencoba...")
    except Exception as e:
        ui.write_log(f"💥 Error: {e}")


if __name__ == "__main__":
    ui = LogUI()
    ui.run(main)
