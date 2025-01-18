"""
All modules and functions required for back_test should be added in requirements.txt.
"""

import pandas as pd
import pandas_ta as ta
from untrade.client import Client
from tqdm import tqdm

# ALL your imports here


def process_data(data):
    data['PVT'] = 0.0 
    data['EMA20'] = ta.ema(data['close'], length=200)
    # data['EMA11'] = ta.ema(data['close'], length=11)
    # data['EMA45'] = ta.ema(data['close'], length=45)
    data['PVT'] = (((data['close']-data['close'].shift(1))/data['close'].shift(1))*data['volume']) + data['PVT'].shift(1)
    
    # Calculate Parabolic SAR
    psar = ta.psar(data['high'], data['low'], data['close'], af=0.02, max_af=0.2)
    data['PSAR'] = psar['PSARl_0.02_0.2']
    
    # Calculate ADX, +DI, and -DI
    adx = ta.adx(data['high'], data['low'], data['close'], length=14)
    data['ADX'] = adx['ADX_14']
    data['+DI'] = adx['DMP_14']
    data['-DI'] = adx['DMN_14']
    return data


# -------STRATEGY LOGIC--------#
def strat(data):
    df = data.copy()
    df['signals'] = 0
    df['trade_type'] = ''
    df.reset_index(drop=True, inplace=True)
    prev = 0
    for i in tqdm(range(1, len(df))):
        prev = df['signals'][i-1]

        # Buy condition
        if (
            df.iloc[i]['PVT'] > df.iloc[i]['EMA20'] and
            # df.iloc[i]['close'] > df.iloc[i]['PSAR'] and
            df.iloc[i]['ADX'] > 15
        ):
            if prev == -1 or prev == -2:
                df.at[i, 'signals'] = 2
                df.at[i, 'trade_type'] = 'short_reversal'
            else:
                df.at[i, 'signals'] = 1
                df.at[i, 'trade_type'] = 'long'

        # Sell condition
        elif (
            df.iloc[i]['PVT'] < df.iloc[i]['EMA20'] and
            # df.iloc[i]['close'] < df.iloc[i]['PSAR'] and
            df.iloc[i]['ADX'] < 15
        ):
            if prev == 1 or prev == 2:
                df.at[i, 'signals'] = -2
                df.at[i, 'trade_type'] = 'long_reversal'
            else:
                df.at[i, 'signals'] = -1
                df.at[i, 'trade_type'] = 'short'

        prev = df['signals'][i]
    
    return df


# def strat(data):
#     df = data.copy()
#     df['signals'] = 0
#     df['trade_type'] = ''
#     df.reset_index(drop=True, inplace=True)
#     prev = 0
#     entry_price = None
#     stop_loss_pct = 0.05 # Stop-loss percentage (10%)
#     current_trade = 0  # 0 = no trade, 1 = long, -1 = short

#     for i in tqdm(range(1, len(df))):
#         prev = df['signals'][i-1]

#         # Long trade conditions
#         if (
#             df.iloc[i]['EMA9'] > df.iloc[i]['EMA11'] and 
#             df.iloc[i]['EMA9'] > df.iloc[i]['EMA45'] and
#             df.iloc[i]['ADX'] > 25
#         ):
#             if prev == -1 or prev == -2:  # Reversal from short to long
#                 df.at[i, 'signals'] = 2
#                 df.at[i, 'trade_type'] = 'short_reversal'
#                 current_trade = 1
#                 entry_price = df.iloc[i]['close']  # Set entry price for stop-loss
#             elif prev != 1:  # No active long trade
#                 df.at[i, 'signals'] = 1
#                 df.at[i, 'trade_type'] = 'long'
#                 current_trade = 1
#                 entry_price = df.iloc[i]['close']  # Set entry price for stop-loss

#         # Short trade conditions
#         elif (
#             df.iloc[i]['EMA9'] < df.iloc[i]['EMA11'] and 
#             df.iloc[i]['EMA9'] < df.iloc[i]['EMA45'] and
#             df.iloc[i]['ADX'] < 25
#         ):
#             if prev == 1 or prev == 2:  # Reversal from long to short
#                 df.at[i, 'signals'] = -2
#                 df.at[i, 'trade_type'] = 'long_reversal'
#                 current_trade = -1
#                 entry_price = df.iloc[i]['close']  # Set entry price for stop-loss
#             elif prev != -1:  # No active short trade
#                 df.at[i, 'signals'] = -1
#                 df.at[i, 'trade_type'] = 'short'
#                 current_trade = -1
#                 entry_price = df.iloc[i]['close']  # Set entry price for stop-loss

#         # Stop-loss logic
#         if current_trade == 1:  # Long trade stop-loss
#             if df.iloc[i]['close'] <= entry_price * (1 - stop_loss_pct):  # Price drops by stop-loss percentage
#                 df.at[i, 'signals'] = -1
#                 df.at[i, 'trade_type'] = 'stop_loss'
#                 current_trade = 0  # Exit trade
#                 entry_price = None  # Reset entry price

#         prev = df['signals'][i]  # Update previous signal

#     return df



def perform_backtest(csv_file_path):
    client = Client()
    result = client.backtest(
        jupyter_id="haricharan",
        file_path=csv_file_path,
        leverage=1, 
    )
    return result


def main():
    data = pd.read_csv("ETH_1d.csv")

    processed_data = process_data(data)

    result_data = strat(processed_data)

    csv_file_path = "results_psar_adx.csv"

    result_data.to_csv(csv_file_path, index=False)

    backtest_result = perform_backtest(csv_file_path)
    print(backtest_result)
    last_value = None
    for value in backtest_result:
        last_value = value
    print(last_value)


if __name__ == "__main__":
    main()