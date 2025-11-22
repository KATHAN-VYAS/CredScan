# CredCrawler: Targeted Dark Web Credential Monitor

**CredCrawler** is a modular, Python-based web crawler designed to detect leaked credentials on `.onion` (Tor) websites. It features automated spidering (link discovery), secure credential hashing, and real-time email alerts.

> **⚠️ Educational Use Only:** This tool is designed for academic research and authorized security testing. Do not use this tool to access illegal content or crawl sites without permission.

---

## 🌟 Features

* **Tor Integration:** Routes all traffic through the Tor network using SOCKS5h (preventing DNS leaks).
* **Smart Spidering:** Automatically discovers and follows new links (BFS approach) to map out related pages.
* **Credential Detection:** Uses Regex to identify `email:password` patterns in raw HTML.
* **Secure Storage:** Hashes found passwords using **SHA-256** before saving to disk (never stores plaintext).
* **Real-Time Alerts:** Sends an immediate email notification via Gmail SMTP when leaks are detected.

---

## 🛠️ Prerequisites

1.  **OS:** Linux (Kali Recommended) or macOS/Windows.
2.  **Python:** Version 3.8+.
3.  **Tor Service:** A running Tor background daemon.
4.  **Gmail Account:** You need a Google Account with **2-Step Verification enabled** and an **App Password**.

---

## 📥 Installation

1.  **Clone the repository (or download files):**
    ```bash
    git clone [https://github.com/yourusername/credcrawler.git](https://github.com/yourusername/credcrawler.git)
    cd credcrawler
    ```

2.  **Install Dependencies:**
    ```bash
    pip3 install -r requirements.txt
    ```

3.  **Verify Tor Service:**
    Ensure Tor is running on your system (Default port: 9050).
    ```bash
    sudo service tor start
    sudo service tor status
    ```

---

## ⚙️ Configuration

### 1. Setup Email Alerts
Open `crawler.py` and update the **EMAIL CONFIG** section:
```python
SENDER_EMAIL = "your_email@gmail.com"
SENDER_PASSWORD = "abcdefghijklmnop"  # Your 16-char Google App Password (No spaces!)
RECEIVER_EMAIL = "your_email@gmail.com"
