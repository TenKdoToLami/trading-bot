import os
import argparse
from dotenv import load_dotenv
from src.execution.alpaca import AlpacaClient

# Load configuration
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, "config", ".env")
load_dotenv(dotenv_path=env_path)

def main():
    parser = argparse.ArgumentParser(description='Tactical Bot CLI Utility')
    # Use choices for main commands but we'll handle aliases in the logic
    parser.add_argument('command', help='Command to execute (cash, bal, open, price, pos, liquidate)')
    parser.add_argument('--ticker', type=str, help='Ticker for price command')
    
    args = parser.parse_args()
    alpaca = AlpacaClient()
    
    cmd = args.command.lower()

    if cmd == 'cash':
        print(f"Current Cash: ${alpaca.get_cash():.2f}")
    
    elif cmd in ['equity', 'bal', 'val', 'balance']:
        print(f"Total Equity: ${alpaca.get_equity():.2f}")
        
    elif cmd in ['open', 'status', 'clock']:
        status = "OPEN" if alpaca.is_market_open() else "CLOSED"
        print(f"Market Status: {status}")
        
    elif cmd in ['price', 'vix', 'sig', 'quote']:
        ticker = args.ticker or alpaca.signal_ticker
        print(f"Latest Price ({ticker}): ${alpaca.get_price(ticker):.2f}")
        
    elif cmd in ['positions', 'pos', 'holdings']:
        pos = alpaca.get_positions()
        if not pos:
            print("No managed positions found.")
        else:
            for ticker, qty in pos.items():
                print(f"{ticker}: {qty} shares")

    elif cmd == 'liquidate':
        confirm = input("Are you sure you want to LIQUIDATE all managed assets? (y/N): ")
        if confirm.lower() == 'y':
            alpaca.liquidate_managed_assets()
            print("Liquidation complete.")
        else:
            print("Aborted.")
    else:
        print(f"Unknown command: {cmd}")
        print("Try: cash, bal, open, vix, pos, liquidate")

if __name__ == "__main__":
    main()
