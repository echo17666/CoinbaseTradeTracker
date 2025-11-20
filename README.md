# CoinbaseTradeTracker
A trade tracker using coinbase advanced api

## Setup
1. Clone the repository
2. Create a conda environment
   ```bash
   conda create -n coinbase-trade-tracker python=3.12 -y
   conda activate coinbase-trade-tracker
   ```

3. Install the required packages
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the root directory and add your Coinbase API credentials:
   ```env
   COINBASE_API_KEY=your_api_key
   COINBASE_API_SECRET=your_api_secret
    ```
5. Run the script to get filled trade history:
    ```bash
    python get_filled_history.py
    ```
6. Run the script to calculate profit history:
    ```bash
    python calculate_profit_history.py
    ```

## Output
- The filled trade history will be saved in the `trade_history` directory as a JSON file
- The profit history will be saved in the `profit_history` directory as a JSON file
- The comparison of coin performance will be saved in the `performance_comparison` directory as a text file
- The summary will be printed in the console as below

  - Profit Summary:

   ```
   Coin       Realized        Unrealized      Total          
   ------------------------------------------------------------
   ETH        $        -0.24 $      -111.80 $      -112.04
   USDC       $         0.00 $         0.00 $         0.00
   FIL        $        -4.08 $        -0.00 $        -4.08
   DASH       $       -25.27 $         0.00 $       -25.27
   KAITO      $         0.00 $         0.00 $         0.00
   BTC        $        -8.54 $        -9.84 $       -18.38
   SOL        $       -36.17 $       -57.46 $       -93.63
   ZEC        $        69.71 $       108.10 $       177.81
   ------------------------------------------------------------
   TOTAL      $        -4.58 $       -71.00 $       -75.58
   ```

   - BTC Comparison Summary:
   ```
   ======================================================================
   BTC BASELINE COMPARISON (If All Investments Were in BTC)
   ======================================================================

   Getting BTC price at 2025-10-22T00:34:38.959435Z...
   ✅ BTC Price (@2025-10-22T00:34:38.959435Z): $108,092.02

   Earliest Trade Time: 2025-10-22T00:34:38.959435Z
   Comparison Start Time: 2025-10-22T00:34:38.959435Z
   Total Net Investment: $1,378.11

   BTC Price (@2025-10-22T00:34:38.959435Z): $108,092.02
   BTC Price (Current): $92,476.90

   If All Invested in BTC:
   BTC Amount: 0.01274939 BTC
   Current Value: $1,179.02
   Profit: $-199.08
   ROI: -14.45%

   Actual Trading Strategy:
   Total Profit: $-75.11
   ROI: -5.45%

   📈 Strategy Outperforms BTC
   Difference: $123.97 (+-62.27%)
   ======================================================================
   ```

   - Ticker vs Ticker Comparison Summary:
   ```

   ==================================================================================================================================
   TICKER PRICE vs TRADING PERFORMANCE (Price Change vs My Trading Performance)
   ==================================================================================================================================

   Coin       Start Time             Start $      Current $    Price Change Net Investment  My ROI       Difference   Status    
   ----------------------------------------------------------------------------------------------------------------------------------
   ETH        2025-10-22T00:34:38    $   3841.00 $   3036.32 📉-20.95%     $   704.28      ❌-15.91%     🟢 +5.04%     Holding   
   FIL        2025-11-07T16:15:06    $      2.62 $      1.87 📉-28.72%     $   454.79      ❌ -0.90%     🟢+27.83%     Holding   
   DASH       2025-11-04T10:33:24    $    144.33 $    129.03 📉-10.60%     $   223.06      ❌-11.33%     🔴 -0.72%     Sold Out  
   KAITO      N/A                    $      0.79 $      0.79 📉  0.00%     $     0.00      ❌  0.00%     🟢 +0.00%     Holding   
   BTC        2025-10-30T14:24:34    $ 107861.92 $  92029.42 📉-14.68%     $   211.82      ❌ -8.68%     🟢 +6.00%     Holding   
   SOL        2025-10-26T18:26:33    $    199.19 $    137.11 📉-31.17%     $   288.20      ❌-32.49%     🔴 -1.32%     Holding   
   ZEC        2025-10-31T17:29:06    $    373.88 $    676.98 📈 81.07%     $   336.96      ✅ 52.77%     🔴-28.30%     Holding   
   ----------------------------------------------------------------------------------------------------------------------------------

   📊 Statistics:
   Profitable Coins: 1/7 (14.3%)
   Beat HODL: 4/7 (57.1%)
   Average Price Change: -3.58%
   Average Trading ROI: -2.36%
   Total Investment: $7,954.52
   Net Investment (In Market): $2,219.11
   Total Profit: $-75.58
   Overall ROI: -3.41%
   ==================================================================================================================================
   ```
   - Ticker vs BTC Comparison Summary:
   ```
   ==========================================================================================
   TICKER vs BTC COMPARISON (Each ticker uses its own first trade time)
   ==========================================================================================

   Coin       Start Time             Actual          If BTC          Diff            Better?   
   ----------------------------------------------------------------------------------------------------
   ETH        2025-10-22T00:34:38    $     -112.04 $     -367.59 $      255.55 ✅         
   FIL        2025-11-07T16:15:06    $       -4.08 $      -39.41 $       35.33 ✅         
   DASH       2025-11-04T10:33:24    $      -25.27 $      -25.75 $        0.49 ✅         
   KAITO      N/A                    $        0.00 $        0.00 $        0.00 ✅         
   BTC        2025-10-30T14:24:34    $      -18.38 $      -81.70 $       63.31 ✅         
   SOL        2025-10-26T18:26:33    $      -93.63 $     -249.43 $      155.80 ✅         
   ZEC        2025-10-31T17:29:06    $      177.81 $     -451.97 $      629.78 ✅         
   ----------------------------------------------------------------------------------------------------

   Coins Outperforming BTC: 7/7 (100.0%)
   ====================================================================================================
   ```
- The output files will be named with the date range used for fetching trade history and profit calculation.


## Usage
- Modify the `start_date` and `end_date` variables in `get_filled_history.py` to specify the date range for fetching trade history.
- The filled trade history will be saved in the `trade_history` directory as a JSON file.
- Modify the `range` variable in `calculate_profit_history.py` to specify the date range for profit calculation.
- The profit history will be saved in the `profit_history` directory as a JSON file.