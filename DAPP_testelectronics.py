import asyncio
from bleak import BleakScanner, BleakClient

DEVICE_NAME = "StellaController"

COMMAND_UUID = "12345678-1234-5678-1234-56789abcdef1"
DATA_UUID    = "12345678-1234-5678-1234-56789abcdef2"
#the controller is hte one with the dye

def notification_handler(sender, data):
    try:
        text = data.decode("utf-8", errors="ignore")
    except Exception:
        text = str(data)
    print(f"\n[NOTIFY] {text}")


async def user_input_loop(client):
    print("\nYou can now type commands.")
    print("Examples:")
    print("  GET_STATUS") 
    print("  SET_REPS:5")
    print("  CALIB_START")
    print("  CALIB_MAX")
    print("  START_GAME")
    print("  RESET_ALL")
    print("Type 'exit' to quit.\n")

    while True:
        cmd = await asyncio.to_thread(input, ">> ")

        cmd = cmd.strip()
        if not cmd:
            continue

        if cmd.lower() == "exit":
            print("Exiting command loop...")
            break

        try:
            await client.write_gatt_char(COMMAND_UUID, cmd.encode("utf-8"))
            print(f"[SENT] {cmd}")
        except Exception as e:
            print(f"[ERROR] Failed to send command: {e}")
            break


async def main():
    print(f"Scanning for BLE device: {DEVICE_NAME} ...")
    device = await BleakScanner.find_device_by_name(DEVICE_NAME, timeout=10.0)

    if device is None:
        print("Device not found.")
        return

    print(f"Found: {device.name} | {device.address}")

    async with BleakClient(device) as client:
        connected = client.is_connected
        print(f"Connected: {connected}")

        if not connected:
            print("Failed to connect.")
            return

        # 开启 notify
        await client.start_notify(DATA_UUID, notification_handler)
        print("Notify enabled on DATA characteristic.")

        # 先主动e问一次状态
        await client.write_gatt_char(COMMAND_UUID, b"GET_STATUS")
        print("[SENT] GET_STATUS")

        # 进入交互输入循环
        await user_input_loop(client)

        # 退出前关闭 notify
        try:
            await client.stop_notify(DATA_UUID)
        except Exception:
            pass

    print("Disconnected.")


if __name__ == "__main__":
    asyncio.run(main())
