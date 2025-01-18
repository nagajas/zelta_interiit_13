import uuid
import pandas as pd
import numpy as np
from untrade.client import Client
import os

def process_data(data):
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data[(data['datetime']>='2020-01-01') & (data['datetime']<='2023-12-31')].copy()
    # Calculate indicators
    data["ema_20"] = data["close"].ewm(span=20, adjust=False).mean()
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data["rsi"] = 100 - (100 / (1 + rs))
    ema_short = data['close'].ewm(span=24, adjust=False).mean()
    ema_long = data['close'].ewm(span=52, adjust=False).mean()
    data["macd"] = ema_short - ema_long
    data["signal_line"] = data["macd"].ewm(span=18, adjust=False).mean()

    # Generate buy/sell signals
    data["Signal"] = 0
    data.loc[(data["rsi"] < 30) & (data["macd"] > data["signal_line"]) & (data["close"] > data["ema_20"]), "Signal"] = -1
    data.loc[(data["rsi"] > 70) & (data["macd"] < data["signal_line"]) & (data["close"] < data["ema_20"]), "Signal"] = 1

    #data["Signal"] = 0
    #data.loc[(data["rsi"] < 30) & (data["macd"] > data["signal_line"]) , "Signal"] = 1
    #data.loc[(data["rsi"] > 70) & (data["macd"] < data["signal_line"]) , "Signal"] = -1
    return data


def strat(data):
    signal = []
    trade_type = []
    prev = 0
    lastexec = 0
    for value in data["Signal"]:
        if value == prev:
            signal.append(0)
            trade_type.append('')
        else:
            if value==1:
                if lastexec==-1:
                    trade_type.append('close')
                else:
                    trade_type.append('long')
                signal.append(1)
                lastexec=1
            elif value==-1:
                if lastexec==1:
                    trade_type.append('close')
                else:
                    trade_type.append('short')
                signal.append(-1)
                #trade_type.append('short')
                lastexec=-1
            else:
                signal.append(0)
                trade_type.append('')
            
        prev = value
        
    data["signals"] = signal
    data['trade_type'] = trade_type
    return data


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
             jupyter_id="test",
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
                 jupyter_id="test",
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
     data = pd.read_csv("BTC_DATA/BTC_2019_2023_30m.csv")

     processed_data = process_data(data)

     result_data = strat(processed_data)

     csv_file_path = "BTCresults_1.csv"

     result_data.to_csv(csv_file_path, index=False)

     backtest_result = perform_backtest_large_csv(csv_file_path)
     # backtest_result = perform_backtest(csv_file_path)

     # No need to use following code if you are using perform_backtest_large_csv
     #print(backtest_result)
     #for value in backtest_result:
     #    print(value)


if __name__ == "__main__":
    main()