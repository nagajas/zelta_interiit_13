import sys
import os
import uuid
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from untrade.client import Client
# ALL your imports here


def process_data(data):
    """
    Process the input data and calculate Heikin-Ashi (HA) candlesticks.
    Adds necessary columns and handles missing or invalid data.

    Parameters:
    data (pandas.DataFrame): The input data to be processed.

    Returns:
    pandas.DataFrame: The processed dataframe with HA candles and cleaned data.
    """
    # Ensure numeric conversion for critical columns
    for col in ['open', 'high', 'low', 'close', 'volume']:
        data[col] = pd.to_numeric(data[col], errors='coerce')

    # Drop rows with missing critical data
    data.dropna(subset=['open', 'high', 'low', 'close'], inplace=True)

    # Sort data by datetime (if not already sorted)
    if 'datetime' in data.columns:
        data['datetime'] = pd.to_datetime(data['datetime'])
        data.sort_values('datetime', inplace=True)

    # Calculate Heikin-Ashi (HA) values
    ha_data = data.copy()
    ha_data['ha_close'] = (ha_data['open'] + ha_data['high'] + ha_data['low'] + ha_data['close']) / 4

    ha_data['ha_open'] = ha_data['open']  # Initialize the first HA open
    for i in range(1, len(ha_data)):
        ha_data.loc[ha_data.index[i], 'ha_open'] = (ha_data.loc[ha_data.index[i - 1], 'ha_open'] + ha_data.loc[ha_data.index[i - 1], 'ha_close']) / 2

    ha_data['ha_high'] = ha_data[['high', 'ha_open', 'ha_close']].max(axis=1)
    ha_data['ha_low'] = ha_data[['low', 'ha_open', 'ha_close']].min(axis=1)

    return ha_data


# -------STRATEGY LOGIC--------#
def strat(data):
    """
    Create a strategy using Heikin-Ashi (HA) candles.
    Adds 'signals' and 'trade_type' columns.

    Parameters:
    - data: DataFrame
        The input data containing HA candles.

    Returns:
    - DataFrame
        The modified input data with 'signals' and 'trade_type' columns.
    """
    short_window = 60  # Short SMA window
    long_window = 300  # Long SMA window

    # Use HA close for strategy calculations
    data['short_sma'] = data['ha_close'].rolling(window=short_window).mean()
    data['long_sma'] = data['ha_close'].rolling(window=long_window).mean()

    # Generate signals
    data['signals'] = 0  # Default: no signal
    data.loc[data['short_sma'] > data['long_sma'], 'signals'] = 1  # Buy signal
    data.loc[data['short_sma'] < data['long_sma'], 'signals'] = -1  # Sell signal

    # Generate trade types based on signals
    data['trade_type'] = 'hold'  # Default: hold
    data.loc[data['signals'] == 1, 'trade_type'] = 'buy'  # Buy signal
    data.loc[data['signals'] == -1, 'trade_type'] = 'sell'  # Sell signal

    return data


def perform_backtest(csv_file_path):
    client = Client()
    result = client.backtest(
        jupyter_id="Team44_Zelta_HPPS",  # the one you use to login to jupyter.untrade.io
        file_path=csv_file_path,
        leverage=1,  # Adjust leverage as needed
    )
    return result


# Following function can be used for every size of file, specially for large files(time consuming,depends on upload speed and file size)
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
            jupyter_id="test",  # result_type="Q",
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
                jupyter_id="kingab2004",
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
    data = pd.read_csv("data/BTC_DATA/BTC_2019_2023_30m.csv")

    processed_data = process_data(data)

    result_data = strat(processed_data)

    csv_file_path = "HA&KALMAN.csv"

    result_data.to_csv(csv_file_path, index=False)

    backtest_result = perform_backtest_large_csv(csv_file_path)
    # backtest_result = perform_backtest(csv_file_path)

    # No need to use the following code if you are using perform_backtest_large_csv
    print(backtest_result)
    for value in backtest_result:
        print(value)

import numpy as np
import matplotlib.pyplot as plt

'''def plot_results(data):
    """
    Plots the cumulative returns, strategy returns, drawdown, and Sharpe ratio.
    """
    # Calculate returns
    data['returns'] = data['ha_close'].pct_change()
    data['strategy_returns'] = data['signals'].shift(1) * data['returns']

    # Cumulative returns
    data['cumulative_strategy_returns'] = (1 + data['strategy_returns']).cumprod()
    data['cumulative_market_returns'] = (1 + data['returns']).cumprod()

    # Drawdown
    data['drawdown'] = data['cumulative_strategy_returns'] / data['cumulative_strategy_returns'].cummax() - 1

    # Sharpe ratio
    sharpe_ratio = data['strategy_returns'].mean() / data['strategy_returns'].std() * np.sqrt(252)

    # Adjust Sharpe ratio scale to be between 1 and 10
    sharpe_ratio_scaled = min(max(sharpe_ratio, 1), 10)

    # Plotting
    plt.figure(figsize=(14, 10))

    # Cumulative Returns
    plt.subplot(2, 2, 1)
    plt.plot(data['cumulative_strategy_returns'], label='Strategy Returns', color='blue')
    plt.plot(data['cumulative_market_returns'], label='Market Returns', color='green')
    plt.title('Heikin-Ashi Candles and Kalman Filters_Cumulative Returns')
    plt.legend()
    plt.grid()

    # Strategy Returns
    plt.subplot(2, 2, 2)
    plt.plot(data['strategy_returns'], label='Strategy Returns', color='purple')
    plt.title('Heikin-Ashi Candles and Kalman Filters_Strategy Returns')
    plt.legend()
    plt.grid()

    # Drawdown
    plt.subplot(2, 2, 3)
    plt.plot(data['drawdown'], label='Drawdown', color='red')
    plt.title('Heikin-Ashi Candles and Kalman Filters_Drawdown')
    plt.legend()
    plt.grid()

    

    plt.tight_layout()
    plt.show()
'''
if __name__ == "__main__":
    main()
    data = pd.read_csv("HA&KALMAN.csv")  # Read processed CSV
#  plot_results(data)
