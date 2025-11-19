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
## Usage
- Modify the `start_date` and `end_date` variables in `get_filled_history.py` to specify the date range for fetching trade history.
- The filled trade history will be saved in the `trade_history` directory as a JSON file.