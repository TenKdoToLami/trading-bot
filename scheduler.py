import os
import time
import datetime
import subprocess
import logging
import sys
from dotenv import load_dotenv

# Setup Logger to match main.py
script_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(script_dir, "logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "sync.log")),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("scheduler")

def get_scheduled_time():
    load_dotenv(override=True)
    return os.getenv('SCHEDULED_TIME', '18:00')

def run_bot():
    logger.info("Launching Tactical Bot Sync Subprocess...")
    try:
        # Run main.py using the same interpreter as the scheduler (venv)
        subprocess.run([sys.executable, "main.py"], check=True)
    except Exception as e:
        logger.error(f"Error during bot execution: {e}")

def main():
    logger.info("--- TACTICAL BOT SCHEDULER STARTED ---")
    
    while True:
        target_time_str = get_scheduled_time()
        now = datetime.datetime.now()
        
        try:
            target_h, target_m = map(int, target_time_str.split(':'))
            target_time = now.replace(hour=target_h, minute=target_m, second=0, microsecond=0)
        except:
            logger.error(f"Invalid SCHEDULED_TIME format: {target_time_str}. Defaulting to 18:00")
            target_time = now.replace(hour=18, minute=0, second=0, microsecond=0)
        
        if target_time <= now:
            target_time += datetime.timedelta(days=1)
            
        wait_seconds = (target_time - now).total_seconds()
        logger.info(f"Next Sync Scheduled: {target_time} (Waiting {wait_seconds/3600:.2f} hours)")
        
        while datetime.datetime.now() < target_time:
            time.sleep(60)
            
        run_bot()

if __name__ == "__main__":
    main()
