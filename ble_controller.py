import asyncio
import threading
from bleak import BleakScanner, BleakClient


class BleController:
    DEVICE_NAME = "StellaController"
    COMMAND_UUID = "12345678-1234-5678-1234-56789abcdef1"
    DATA_UUID    = "12345678-1234-5678-1234-56789abcdef2"

    def __init__(self):
        self._reps = 0
        self._task_complete = False
        self._lock = threading.Lock()
        self._connected = False
        self._client = None
        self._loop = asyncio.new_event_loop()
        t = threading.Thread(target=self._run_loop, daemon=True)
        t.start()

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._connect_loop())

    async def _connect_loop(self):
        while True:
            try:
                print("[BLE] Scanning for StellaController...")
                device = await BleakScanner.find_device_by_name(self.DEVICE_NAME, timeout=10.0)
                if device is None:
                    print("[BLE] Device not found. Retrying in 3s...")
                    await asyncio.sleep(3)
                    continue
                print(f"[BLE] Found: {device.name} | {device.address}")
                async with BleakClient(device) as client:
                    self._client = client
                    self._connected = True
                    print("[BLE] Connected.")
                    await client.start_notify(self.DATA_UUID, self._notification_handler)
                    while client.is_connected:
                        await asyncio.sleep(0.1)
                    self._connected = False
                    self._client = None
                    print("[BLE] Disconnected. Retrying...")
            except Exception as e:
                self._connected = False
                self._client = None
                print(f"[BLE] Error: {e}. Retrying in 3s...")
                await asyncio.sleep(3)

    def _notification_handler(self, sender, data):
        try:
            text = data.decode("utf-8", errors="ignore")
        except Exception:
            text = str(data)
        if text.startswith("REP_OK"):
            with self._lock:
                self._reps += 1
        elif text.startswith("TASK_SUCCESS"):
            with self._lock:
                self._task_complete = True

    def send_command(self, cmd: str):
        if not self._connected or self._client is None:
            return
        async def _write():
            try:
                await self._client.write_gatt_char(self.COMMAND_UUID, cmd.encode("utf-8"))
            except Exception as e:
                print(f"[BLE] send_command failed: {e}")
        asyncio.run_coroutine_threadsafe(_write(), self._loop)

    def get_and_clear_reps(self) -> int:
        with self._lock:
            count = self._reps
            self._reps = 0
            return count

    def get_and_clear_task_complete(self) -> bool:
        with self._lock:
            done = self._task_complete
            self._task_complete = False
            return done

    def is_connected(self) -> bool:
        return self._connected
