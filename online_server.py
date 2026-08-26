import os
import sys
import time
import subprocess
import threading
import re
import webbrowser
import uvicorn
from web_app import app

try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

PORT = 8000

def run_uvicorn():
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")

def run_tunnel():
    time.sleep(1.5)
    print("\n" + "=" * 68)
    print("  🌐 INTERNETGA ULANISH (GLOBAL HTTPS HAVOLA) YARATILMOQDA...")
    print("=" * 68)

    cmd = [
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ServerAliveInterval=30",
        "-p", "443",
        f"-R0:localhost:{PORT}",
        "a.pinggy.io"
    ]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        
        opened = False
        for line in iter(proc.stdout.readline, ''):
            # Print pinggy output
            sys.stdout.write(line)
            sys.stdout.flush()

            # Search for https://...pinggy.link
            match = re.search(r'(https://[a-zA-Z0-9-]+\.a\.free\.pinggy\.link|https://[a-zA-Z0-9-]+\.a\.pinggy\.link)', line)
            if match and not opened:
                public_url = match.group(1)
                opened = True
                print("\n" + "★" * 68)
                print(f"  🎉 SIZNING GLOBAL INTERNET HAVOLANGIZ TAYYOR!")
                print(f"  👉 ASOSIY ILOVA:       {public_url}")
                print(f"  👉 VITAL MONITOR:      {public_url}/monitor")
                print("★" * 68)
                print("  (Ushbu havolani xohlagan telefonga yuboring va oching!)\n")
                try:
                    webbrowser.open(public_url)
                except:
                    pass

    except Exception as e:
        print(f"\n❌ Tunnel xatoligi: {e}")

if __name__ == "__main__":
    print("=" * 68)
    print("  🏥 BEMOR SIMULYATORI VA VITAL MONITOR — INTERNET SERVERI")
    print("=" * 68)
    
    # Start web app in background thread
    t_web = threading.Thread(target=uvicorn_thread := run_uvicorn, daemon=True)
    t_web.start()

    # Start tunnel
    run_tunnel()
