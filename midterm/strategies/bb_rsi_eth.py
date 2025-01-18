import pandas as pd
from untrade.client import Client
import uuid
from pprint import pprint
import os

def process_data(data):
    data['SMA_20'] = data['close'].rolling(window=20).mean()  # 20-period simple moving average
    data['stddev'] = data['close'].rolling(window=20).std()   # 20-period standard deviation

    K = 2
    data['upper_band'] = data['SMA_20'] + (K * data['stddev'])
    data['lower_band'] = data['SMA_20'] - (K * data['stddev'])
    data.drop(['stddev'], axis=1, inplace=True)
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data["rsi"] = 100 - (100 / (1 + rs))

    data["Signal"] = 0
    data.loc[(data["rsi"] < 30) | (data['close'] < data['lower_band']) , "Signal"] = -1
    data.loc[(data["rsi"] > 70) | (data['close'] > data['upper_band']) , "Signal"] = 1
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

def perform_backtest(csv_file_path):
    client = Client()

    result = client.backtest(
        jupyter_id="haricharan",
        file_path=csv_file_path,
        leverage=1,
    )


    return result

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
     data = pd.read_csv("ETH_DATA/ETHUSDT_1d.csv")

     processed_data = process_data(data)

     result_data = strat(processed_data)

     csv_file_path = "ETHresults_2.csv"

     result_data.to_csv(csv_file_path, index=False)

     backtest_result = perform_backtest_large_csv(csv_file_path)
     # backtest_result = perform_backtest(csv_file_path)

     # No need to use following code if you are using perform_backtest_large_csv
     #print(backtest_result)
     #for value in backtest_result:
     #    print(value)


if __name__ == "__main__":
    main()