### Not included in the mid-term report.
import pandas as pd
import uuid
import os
import numpy as np
from untrade.client import Client

# Risk and transaction settings
RISK_TOLERANCE = 0.02  # 2% risk per trade
RISK_FREE_RATE = 0.01  # annualized risk-free rate for Sharpe Ratio
TARGET_PROFIT_PERCENTAGE = 0.05  # Target profit percentage (5%)

def process_data(df):
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df[(df['datetime']>='2020-01-01') & (df['datetime']<='2023-12-31')].copy()

    # Adding Indicators
    # 1.EMA
    df['ema_20'] = df['close'].ewm(span=20, adjust=False).mean()
    # 2.RSI
    delta = df['close'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean() #14 day window
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain/loss
    df['rsi'] = 100-(100/(1+rs))
    # 3.MACD
    ema_short = df['close'].ewm(span=12, adjust=False).mean()
    ema_long = df['close'].ewm(span=26, adjust=False).mean()
    macd = ema_short - ema_long
    signal = macd.ewm(span=9, adjust=False).mean()
    df['macd'] = macd
    df['signal_line'] = signal
    # Lows
    df['monthly_low'] = df['close'].rolling(window=21*24*60).min()
    df['yearly_low'] = df['close'].rolling(window=252*24*60).min()

    return df

def strat(data):
    df = data.copy()
    df['signals'] = 0
    df['trade_type'] = ''
    df = df.reset_index(drop=True)
    pos = 0  # Position indicator (0 means no position, 1 means a position is held)
    entry_price = 0  # Price at which a position was entered
    # bal = 1000 # Starting with 1000$

    for i in range(1, len(df)):
        curr_price = df.loc[i, 'close']
        
        # Buy Condition
        if pos == 0:
            if (
                df.loc[i, 'rsi'] < 30 and
                df.loc[i, 'macd'] > df.loc[i, 'signal_line'] and
                curr_price > df.loc[i, 'ema_20']
            ):
                # Enter a buy position
                df.loc[i, 'signals'] = 1
                df.loc[i, 'trade_type'] = 'buy'
                pos = 1
                entry_price = curr_price
                #print(f"Buy at {curr_price:.2f} on index {i}")
    
        # Sell Condition
        elif pos == 1:
            # Calculate the target price based on the profit target percentage
            profit_target_price = entry_price * (1 + TARGET_PROFIT_PERCENTAGE)
            
            if curr_price >= profit_target_price:
                # Exit the position
                df.loc[i, 'signals'] = -1
                df.loc[i, 'trade_type'] = 'close'
                pos = 0  # Reset position indicator after selling
                #print(f"Sell at {curr_price:.2f} on index {i}")


    return df


def perform_backtest_large_csv(csv_file_path):
     client = Client()
     file_id = str(uuid.uuid4())
     chunk_size = 90 * 1024 * 1024
     total_size = os.path.getsize(csv_file_path)
     total_chunks = (total_size + chunk_size - 1) // chunk_size
     chunk_number = 0
     if total_size <= chunk_size:
         total_chunks = 1
         # Normal Backtest
         result = client.backtest(
             file_path=csv_file_path,
             leverage=1,
             jupyter_id="nagajas",
             # result_type="Q",
         )
         for value in result:
             print(value)

         return result

     with open(csv_file_path, "rb") as f:
         while True:
             chunk_data = f.read(chunk_size)
             if not chunk_data:
                 break
             chunk_file_path = f"/tmp/{file_id}_chunk_{chunk_number}.csv"
             with open(chunk_file_path, "wb") as chunk_file:
                 chunk_file.write(chunk_data)

             # Large CSV Backtest
             result = client.backtest(
                 file_path=chunk_file_path,
                 leverage=1,
                 jupyter_id="nagajas",
                 file_id=file_id,
                 chunk_number=chunk_number,
                 total_chunks=total_chunks,
                 # result_type="Q",
             )

             for value in result:
                 print(value)

             os.remove(chunk_file_path)

             chunk_number += 1

     return result
            
def main():
    
    data = pd.read_csv("ETH_DATA/ETHUSDT_3m.csv") # File copied from InterIIT docs
    processed_data = process_data(data)
    
    result_data = strat(processed_data)
    
    csv_file_path = "ETHresults_4.csv"
    
    result_data.to_csv(csv_file_path, index=False)
    
    backtest_result = perform_backtest_large_csv(csv_file_path)
    # backtest_result = perform_backtest(csv_file_path)
    
    #print(backtest_result)
    #for value in backtest_result:
    #    print(value)


if __name__ == "__main__":
    main()