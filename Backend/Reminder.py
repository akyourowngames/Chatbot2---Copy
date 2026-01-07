import json
import datetime
import threading
import pyttsx3
import os
import time

# Use dynamic path construction
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
REMINDER_FILE = os.path.join(project_root, "Data", "reminderdata.json")

def load_reminders():
    if os.path.exists(REMINDER_FILE):
        with open(REMINDER_FILE, "r") as file:
            return json.load(file)
    return []

def save_reminders(reminders):
    # Ensure the directory exists
    os.makedirs(os.path.dirname(REMINDER_FILE), exist_ok=True)
    with open(REMINDER_FILE, "w") as file:
        json.dump(reminders, file, indent=4)

def set_reminder(reminder_text, reminder_time):
    reminders = load_reminders()
    reminder = {
        "text": reminder_text,
        "time": reminder_time.strftime("%Y-%m-%d %H:%M:%S")
    }
    reminders.append(reminder)
    save_reminders(reminders)
    return f"Reminder set for {reminder_time.strftime('%Y-%m-%d %H:%M:%S')}"

def check_reminders():
    while True:
        now = datetime.datetime.now()
        reminders = load_reminders()
        updated_reminders = []
        for reminder in reminders:
            reminder_time = datetime.datetime.strptime(reminder["time"], "%Y-%m-%d %H:%M:%S")
            if now >= reminder_time:
                notify_reminder(reminder["text"])
            else:
                updated_reminders.append(reminder)
        save_reminders(updated_reminders)
        time.sleep(60)  # Check every minute

def notify_reminder(reminder_text):
    engine = pyttsx3.init()
    engine.say(f"Reminder: {reminder_text}")
    engine.runAndWait()
    print(f"Reminder: {reminder_text}")

def start_reminder_checker():
    threading.Thread(target=check_reminders, daemon=True).start()

if __name__ == "__main__":
    start_reminder_checker()
    while True:
        user_input = input("Enter your reminder (e.g., 'Call John on 2025-01-20 at 15:30'): ")
        try:
            parts = user_input.split(" on ")
            if len(parts) == 1:
                parts = user_input.split(" at ")
            reminder_text = parts[0].replace("Set a reminder: ", "").strip()
            reminder_time_str = parts[1].strip()
            reminder_time = datetime.datetime.strptime(reminder_time_str, "%Y-%m-%d at %H:%M")
            if reminder_time > datetime.datetime.now():
                print(set_reminder(reminder_text, reminder_time))
            else:
                print("The specified time is in the past. Please provide a future time.")
        except Exception as e:
            print(f"Error: {e}. Please provide the reminder in the correct format.")
