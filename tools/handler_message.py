import json

from tools.register import PLC_REGISTERS


def handle_command(data,plc_connector):
    try:
        parsed = json.loads(data)

        command = parsed.get("pattern")  # pattern dari NestJS (turn_on / turn_off)
        payload = parsed.get("data", {}) # isi emit (address, dll)

        address = payload.get("address")
        type = payload.get("type")

        if not command or not address:
            print("⚠️ Data tidak lengkap:", parsed)
            return True

        # --- proses sama kayak sebelumnya ---
        group = None
        # urutkan key dari yang paling panjang → supaya "AA" atau "AB" dicek dulu sebelum "A"
        for key in sorted(PLC_REGISTERS.keys(), key=len, reverse=True):
            if address.startswith(key):
                group = key
                break

        if not group:
            print(f"⚠️ Address {address} tidak dikenal di PLC_REGISTERS")
            return True

        register_list = PLC_REGISTERS[group]
        target = next((item for item in register_list if item["code"] == address), None)

        if not target:
            print(f"⚠️ Address {address} tidak ditemukan di group {group}")
            return True

        reg_device = target["reg"]
        off_device = target["lamp"]
        index = int(address,16)

        if command == "turn_on":
            print(f"🔆 TURN ON {address} → {reg_device} = {index}")
            plc_connector.reset_and_write(reg_device, off_device, index, mode="on")

        elif command == "turn_off":
            print(f"🌑 TURN OFF {address} → {reg_device} = {index}")
            plc_connector.reset_and_write(reg_device, off_device, index, mode="off")

        else:
            print("❓ Unknown command:", command)

        return True
    except Exception as e:
        print("❌ Failed to handle message:", e)
        return False
