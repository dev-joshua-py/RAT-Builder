# 🔐 RAT Builder – Security Research & Education

⚠️ **IMPORTANT DISCLAIMER**  
This tool is intended **SOLELY** for educational and authorized security testing purposes.  
Unauthorized access to computer systems is illegal. The author does not condone malicious use.  
By using this software, you agree that you are responsible for your actions and that you will only use it in environments where you have explicit permission.

---

## 📖 Overview

This project demonstrates how Remote Access Tools (RATs) are built and how they communicate with command‑and‑control (C2) servers. It is designed for:

- **Security researchers** studying malware behavior and C2 communication patterns.
- **Defenders** learning to detect and analyze malicious traffic.
- **Educators** teaching cybersecurity concepts in a controlled environment.

The builder generates a Python‑based RAT client that uses **Telegram** as its C2 channel – a technique commonly used by real malware. Understanding this helps defenders build better detection and prevention mechanisms.

---

## 🚫 What this is NOT

- A tool for hacking or gaining unauthorized access.
- A ready‑to‑deploy weapon (you must configure and build it yourself).
- A stealth or evasion toolkit (no anti‑virus bypass, no obfuscation, no persistence beyond standard Windows services).

---

## 🛠️ Prerequisites

Before you begin, make sure you have:

- **Windows 10/11** (the generated client is Windows‑only).
- **Python 3.11 or higher** – download from [python.org](https://www.python.org/downloads/).  
  During installation, **check** the box that says “Add Python to PATH”.
- **Git** (optional) – if you want to clone the repository. Otherwise you can download the ZIP.

Verify your installation by opening a Command Prompt and typing:
```cmd
python --version
pip --version
