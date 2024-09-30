import win32process
import psutil
import win32gui
import win32api
import keyboard as kb
import time

class Hook:
    def __init__(self, process_name):
        self.process_name = process_name.lower()  # Ensure the process name is in lowercase
        self.hwnd = None
        self.hdc = None
        self.hooked = False

    def find_window_by_process_name(self):
        def callback(hwnd, pid):
            try:
                tid, proc_id = win32process.GetWindowThreadProcessId(hwnd)
                if proc_id == pid:
                    window_text = win32gui.GetWindowText(hwnd)
                    new_window_text = window_text.replace('\n', ' ')
                    if win32gui.IsWindowVisible(hwnd):
                        print(f"║ ⇒ Found window '{new_window_text}' (PID: {pid}, HWND: {hwnd})")
                        self.hwnd = hwnd
                        return False  # Stop enumeration when the window is found
                    else:
                        print(f"║ ⇒ Window '{new_window_text}' is not visible. Skipping...")
            except win32gui.error as e:
                print(f"[-] Error while processing window handle: {e}")
            return True

        # Find the process by its name, using case-insensitive comparison
        process_found = False
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] and proc.info['name'].lower() == self.process_name:
                process_found = True
                print(f"╠ Process '{self.process_name}' found with PID: {proc.info['pid']}. Enumerating windows...")
                win32gui.EnumWindows(callback, proc.info['pid'])
                if self.hwnd:
                    break
        
        if not process_found:
            raise ValueError(f"╠ Process '{self.process_name}' not found. Ensure it is running.")

    def hook(self):
        if self.hooked: return
        self.find_window_by_process_name()
        if not self.hwnd:
            raise ValueError(f"[-] No visible window found for process '{self.process_name}'")
        
        self.hdc = win32gui.GetWindowDC(self.hwnd)
        self.hooked = True

    def unhook(self):
        if not self.hooked: return
        win32gui.ReleaseDC(self.hwnd, self.hdc)
        self.hooked = False
        self.hwnd = None
        self.hdc = None

    def draw_rectangle(self, x, y, width, height, color=(255, 0, 0)):
        if not self.hooked:
            raise RuntimeError("Hook not established. Call hook() first.")
        
        x1, y1 = x, y
        x2, y2 = x + width, y + height

        brush_color = win32api.RGB(*color)
        brush = win32gui.CreateSolidBrush(brush_color)
        win32gui.SelectObject(self.hdc, brush)
        win32gui.Rectangle(self.hdc, x1, y1, x2, y2)
        win32gui.DeleteObject(brush)

if __name__ == "__main__":
    hook = Hook("firefox.exe")  # Ensure process name matches exactly as seen in Task Manager
    try:
        hook.hook()
        while not kb.is_pressed("suppr"):
            hook.draw_rectangle(50, 50, 200, 100, color=(255, 0, 0))
            time.sleep(0.5)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        hook.unhook()
