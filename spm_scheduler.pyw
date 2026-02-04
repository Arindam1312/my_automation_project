import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import threading
import time
import subprocess
from datetime import datetime, timedelta
import traceback
import sys
import os
from win10toast import ToastNotifier

# ======================================================
JOB_SCRIPT = r"C:\Users\Arindam Mandal\Desktop\ANY MEARGER\My_Py\every_two_hours_report.py"
LOG_FILE = r"C:\Users\Arindam Mandal\Desktop\ANY MEARGER\My_Py\spm_scheduler.log"

running = False
scheduler_thread = None
icon = None
next_run_time = None
toaster = ToastNotifier()

# ======================================================
def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")

# ======================================================
def notify(title, msg):
    toaster.show_toast(title, msg, duration=5, threaded=True)

# ======================================================
def get_next_run_time():
    now = datetime.now().replace(second=0, microsecond=0)
    hour = now.hour
    minute = now.minute

    if hour % 2 == 0:
        next_hour = hour + 2 if minute > 0 else hour
    else:
        next_hour = hour + 1

    next_run = now.replace(hour=next_hour, minute=0)
    if next_run <= now:
        next_run += timedelta(hours=2)

    return next_run

# ======================================================
def run_job(manual=False):
    try:
        log("Job started" + (" (manual)" if manual else ""))
        subprocess.run(["python", JOB_SCRIPT], check=True)
        log("Job completed successfully")
        notify("SPM Scheduler", "Dashboard job completed successfully")
        update_icon("Running")
    except Exception as e:
        log("Job FAILED")
        log(traceback.format_exc())
        notify("SPM Scheduler ❌", "Job failed. Check logs.")
        update_icon("Error")

# ======================================================
def scheduler_loop():
    global running, next_run_time

    while running:
        next_run_time = get_next_run_time()
        log(f"Next run scheduled at {next_run_time}")

        while datetime.now() < next_run_time:
            if not running:
                return
            time.sleep(1)

        if running:
            run_job()
            time.sleep(60)

# ======================================================
def start_scheduler(icon_item=None, item=None):
    global running, scheduler_thread
    if running:
        return

    running = True
    log("Scheduler started")
    update_icon("Running")

    scheduler_thread = threading.Thread(
        target=scheduler_loop,
        daemon=True
    )
    scheduler_thread.start()

# ======================================================
def stop_scheduler(icon_item=None, item=None):
    global running
    running = False
    log("Scheduler stopped")
    update_icon("Stopped")

# ======================================================
def retry_now(icon_item=None, item=None):
    threading.Thread(target=run_job, args=(True,), daemon=True).start()

# ======================================================
def open_log(icon_item=None, item=None):
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, "w").close()
    os.startfile(LOG_FILE)

# ======================================================
def exit_app(icon_item=None, item=None):
    global running
    running = False
    log("Scheduler exited")
    icon.stop()
    sys.exit(0)

# ======================================================
def create_icon(color):
    img = Image.new("RGB", (64, 64), "white")
    d = ImageDraw.Draw(img)
    d.ellipse((8, 8, 56, 56), fill=color)
    return img

# ======================================================
def update_icon(status):
    global icon
    if status == "Running":
        icon.icon = create_icon("green")
    elif status == "Stopped":
        icon.icon = create_icon("red")
    else:  # Error
        icon.icon = create_icon("orange")

    icon.title = (
        f"SPM Scheduler\n"
        f"Status: {status}\n"
        f"Next: {next_run_time if next_run_time else 'N/A'}"
    )

# ======================================================
icon = pystray.Icon(
    "SPM Scheduler",
    create_icon("red"),
    "SPM Scheduler",
    menu=pystray.Menu(
        item("▶ Start", start_scheduler),
        item("⏹ Stop", stop_scheduler),
        item("🔁 Retry Now", retry_now),
        item("📄 View Logs", open_log),
        item("❌ Exit", exit_app),
    )
)

log("Tray application started")
start_scheduler()       
icon.run()