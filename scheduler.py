import os
import time
import datetime
import subprocess
from dotenv import load_dotenv

def get_scheduled_time():
    load_dotenv(override=True) # Always reload to catch .env changes
    return os.getenv('SCHEDULED_TIME', '18:00')

def run_bot():
    print(f"[{datetime.datetime.now()}] Launching Tactical Bot Sync...")
    try:
        # Run main.py as a subprocess
        subprocess.run(["python", "main.py"], check=True)
        print(f"[{datetime.datetime.now()}] Sync completed successfully.")
    except Exception as e:
        print(f"[{datetime.datetime.now()}] Error during bot execution: {e}")

def main():
    print("--- TACTICAL BOT SCHEDULER STARTED ---")
    
    while True:
        target_time_str = get_scheduled_time()
        now = datetime.datetime.now()
        
        # Parse target time (e.g., "18:00")
        target_h, target_m = map(int, target_time_str.split(':'))
        target_time = now.replace(hour=target_h, minute=target_m, second=0, microsecond=0)
        
        # If the time has already passed today, target tomorrow
        if target_time <= now:
            target_time += datetime.timedelta(days=1)
            
        wait_seconds = (target_time - now).total_seconds()
        
        print(f"Next Sync Scheduled: {target_time} (Waiting {wait_seconds/3600:.2f} hours)")
        
        # Sleep until target time
        # We sleep in 60s chunks so the process remains responsive to interrupts
        while datetime.datetime.now() < target_time:
            time.sleep(60)
            
        # Time to run!
        run_bot()

if __name__ == "__main__":
    main()
