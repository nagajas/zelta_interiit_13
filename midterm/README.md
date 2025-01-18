# Mid Term Submission - Team-44 for the Problem Statement "Curating Alphas On BTC And USDT Crypto Market" by Zelta Automations

This is the **midterm submission** of **Team-44** for the problem statement *"Curating Alphas On BTC And USDT Crypto Market"* by **Zelta Automations** for the **Inter IIT Tech Meet 13.0**.

## File Structure

The file structure for this submission is organized as follows:

1. **44_h2_zelta_midterm.pdf**
   This document contains our **midterm progress report** outlining the progress, strategy, and results thus far.

2. **Strategies Folder**
   The folder contains the following eight python files:

These python files contains the backtesting code for **execution of the strategy** using **Bollinger Bands (BB)** and **Average True Range (ATR)** for BTC market. It includes detailed steps for calculating and utilizing these indicators to generate trading signals based on market volatility.
   - **bb_atr_btc.py**
   - **bb_atr_eth.py** 
   
   These python files contains the backtesting code the **execution of the strategy** using **Bollinger Bands (BB)** and **Relative Strength Index (RSI)**. The strategy captures price deviations using BB and confirms overbought/oversold conditions using RSI for more accurate trade signals.
   - **bb_rsi_btc.py** 
   - **bb_rsi_eth** 

These python files contains the backtesting code for **execution of the strategy** using **Moving Average Convergence Divergence (MACD)** with modified time periods and **Relative Strength Index (RSI)**. The MACD indicator helps identify trend-following signals while the RSI helps in identifying overbought or oversold conditions, making the strategy more robust.
   - **macd_rsi_btc_1.py** 
   - **macd_rsi_eth_1.py** 
     
     These files also contain execution of the above strategy with added conditions for book profits.
   - **macd_rsi_btc_2.py** 
   - **macd_rsi_eth_2.py** 
---

### Key Points:
- The **midterm progress report** provides a comprehensive overview of the work done so far.
- The **strategies** implemented in the code notebooks use combinations of well-known technical indicators for **BTC and USDT market analysis**.
