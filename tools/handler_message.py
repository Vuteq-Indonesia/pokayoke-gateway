import json
from tools.register import PLC_REGISTERS


def handle_command(data, plc_connector, ui=None):
    """Handle pesan dari RMQ untuk mengontrol PLC"""
    def log(msg: str):
        if ui:
            ui.write_log(msg)
        else:
            print(msg)

    try:
        parsed = json.loads(data)

        command = parsed.get("pattern")  # pattern dari NestJS (turn_on / turn_off)
        payload = parsed.get("data", {})  # isi emit (address, dll)

        address = payload.get("address")
        type_ = payload.get("type")

        if not command or not address:
            log(f"⚠️ Data tidak lengkap: {parsed}")
            return True

        # --- cari group berdasarkan prefix address ---
        group = None
        for key in sorted(PLC_REGISTERS.keys(), key=len, reverse=True):
            if address.startswith(key):
                group = key
                break

        if not group:
            log(f"⚠️ Address {address} tidak dikenal di PLC_REGISTERS")
            return True

        register_list = PLC_REGISTERS[group]
        target = next((item for item in register_list if item["code"] == address), None)

        if not target:
            log(f"⚠️ Address {address} tidak ditemukan di group {group}")
            return True

        reg_device = target["reg"]
        off_device = target["lamp"]
        index = int(address, 16)

        if command == "turn_on":
            log(f"🔆 TURN ON {address} → {reg_device} = {index}")
            plc_connector.reset_and_write(reg_device, off_device, index, mode="on")

        elif command == "turn_off":
            log(f"🌑 TURN OFF {address} → {reg_device} = {index}")
            plc_connector.reset_and_write(reg_device, off_device, index, mode="off")

        else:
            log(f"❓ Unknown command: {command}")

        return True

    except Exception as e:
        log(f"❌ Failed to handle message: {e}")
        return False
