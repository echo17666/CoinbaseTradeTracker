# Quick Start Guide

## First Time Setup (5 minutes)

### 1. Install and Configure
```bash
# Clone repository
git clone https://github.com/echo17666/CoinbaseTradeTracker.git
cd CoinbaseTradeTracker

# Create environment
conda create -n trade python=3.12 -y
conda activate trade

# Install dependencies
pip install -r requirements.txt

# Add your API credentials to .env file
echo "COINBASE_API_KEY=your_key_here" > .env
echo "COINBASE_API_SECRET_KEY=your_secret_key_here" >> .env
```

### 2. Initial Data Collection
```bash
# Fetch all trades
python get_filled_history.py

# Calculate profit
python calculate_profit_history.py

# Generate 30 days of historical data
python generate_daily_history.py

# Create charts
python visualize_profit_history.py
```

### 3. Enable Auto-Updates (Optional)
```bash
# macOS
./setup_auto_update.sh

# Linux - add to crontab
crontab -e
# Add: 0 0 * * * cd /path/to/CoinbaseTradeTracker && /path/to/python daily_update.py
```

## Daily Usage

### Manual Update
```bash
python daily_update.py
```

### View Charts
```bash
open charts/total_daily_profit.png
open charts/daily_profit_all_coins.png
```

### Check Logs
```bash
tail -f logs/daily_update_*.log
```

## Key Files

- `charts/` - All generated visualizations
- `profit_history/` - Daily profit snapshots
- `trade_history/` - Raw trade data from Coinbase
- `logs/` - Update logs

## Troubleshooting

**No trades showing up?**
- Check your `.env` file has correct API credentials
- Verify your Coinbase account has trade history

**Charts not generating?**
- Run `python generate_daily_history.py` first
- Check `profit_history/` folder has data files

**Auto-update not working?**
- macOS: `launchctl list | grep coinbase`
- Check logs in `logs/` directory

## Quick Reference

```bash
# Full update cycle
python get_filled_history.py && \
python calculate_profit_history.py && \
python generate_daily_history.py && \
python visualize_profit_history.py

# Or use the automated script
python daily_update.py
```

For detailed documentation, see [README.md](README.md)
