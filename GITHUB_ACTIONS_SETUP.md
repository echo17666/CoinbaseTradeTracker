# GitHub Actions Setup Guide

This guide explains how to set up automatic daily updates using GitHub Actions, which runs in the cloud instead of your local machine.

## ⚠️ Important Considerations

### Pros of GitHub Actions:
- ✅ Runs even when your computer is off
- ✅ Free for public repositories (2,000 minutes/month for private repos)
- ✅ No local machine resources used
- ✅ Automatic git commits with updated data

### Cons of GitHub Actions:
- ⚠️ Your trade data and charts will be committed to the repository (publicly visible if repo is public)
- ⚠️ API keys stored as GitHub secrets (secure, but in the cloud)
- ⚠️ Uses your GitHub Actions minutes quota
- ⚠️ Requires pushing sensitive data to git

## 🔐 Security Recommendations

### Option 1: Private Repository (Recommended)
If your data is sensitive, keep the repository **private**:
```bash
# On GitHub, go to: Settings → General → Danger Zone → Change visibility → Make private
```

### Option 2: Exclude Data from Git
Add to `.gitignore` to prevent committing data:
```
trade_history/
profit_history/
comparison/
charts/
logs/
```
**Note**: This defeats the purpose of auto-commits, but keeps data local.

## 📝 Setup Instructions

### Step 1: Add Secrets to GitHub

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add two secrets:

**Secret 1:**
- Name: `COINBASE_API_KEY`
- Value: Your Coinbase API key (from `.env` file)

**Secret 2: ⚠️ IMPORTANT - Preserving PEM Format**
- Name: `COINBASE_API_SECRET_KEY` (note: ends with `_KEY`)
- Value: Your Coinbase API secret from `.env` file
- **CRITICAL**: The private key MUST have actual newlines, not `\n` characters
  
**How to add the secret correctly:**

**Step 1: Extract the actual key with proper newlines**

Your `.env` file shows the key with `\n` escape sequences. You need to convert these to real newlines:

```bash
# Method 1: Use echo -e to interpret \n
cd /Users/echo/Desktop/CoinbaseTradeTracker/CoinbaseTradeTracker
grep COINBASE_API__KEY .env | cut -d'=' -f2- | tr -d '"' | xargs echo -e
```

This will output the key with REAL newlines. Copy this output.

**Step 2: Paste into GitHub**

The output should look like:
```
-----BEGIN EC PRIVATE KEY-----
Multiple lines
-----END EC PRIVATE KEY-----
```

Paste THIS into the GitHub Secret value field (with the newlines, not the `\n` characters).

### Step 2: Enable GitHub Actions

1. Go to **Settings** → **Actions** → **General**
2. Under "Workflow permissions", select:
   - ✅ **Read and write permissions**
   - ✅ **Allow GitHub Actions to create and approve pull requests**
3. Click **Save**

### Step 3: Push Workflow File

The workflow file is already created at `.github/workflows/daily_update.yml`.

Push it to GitHub:
```bash
git add .github/workflows/daily_update.yml
git commit -m "Add GitHub Actions workflow for daily updates"
git push
```

### Step 4: Verify Setup

1. Go to the **Actions** tab on GitHub
2. You should see "Daily Trade Update" workflow
3. Click **Run workflow** → **Run workflow** to test manually
4. Check the logs to ensure it runs successfully

## 🕐 Schedule Configuration

The workflow runs at **00:00 UTC** every day by default.

To change the time, edit `.github/workflows/daily_update.yml`:
```yaml
on:
  schedule:
    - cron: '0 8 * * *'  # 8 AM UTC = 4 AM EDT / 1 AM PDT
```

Cron format: `minute hour day month day-of-week`
- `0 0 * * *` = Midnight UTC daily
- `0 12 * * *` = Noon UTC daily
- `30 6 * * 1-5` = 6:30 AM UTC, Monday-Friday only

### Time Zone Conversion Examples:
- **PST (UTC-8)**: `0 8 * * *` = Midnight PST
- **EST (UTC-5)**: `0 5 * * *` = Midnight EST
- **CST (UTC-6)**: `0 6 * * *` = Midnight CST

## 🔍 Monitoring

### View Workflow Runs:
- Go to **Actions** tab on GitHub
- Click on any workflow run to see detailed logs

### Check Auto-Commits:
- Commits will appear as "Auto-update: YYYY-MM-DD HH:MM:SS"
- Author: `github-actions[bot]`

### Debugging Failed Runs:
1. Check workflow logs in Actions tab
2. Common issues:
   - Secrets not set correctly
   - Workflow permissions not enabled
   - API rate limits (Coinbase API)
   - Python dependency installation failures

## 🔄 Local vs GitHub Actions

You can run **both simultaneously**:
- **Local (launchd/cron)**: Runs on your machine, data stays local
- **GitHub Actions**: Runs in cloud, data committed to repo

Or choose one:
- **Choose Local** if: Data privacy is critical, unlimited runs needed
- **Choose GitHub Actions** if: Want cloud automation, don't mind data in repo

## 🛑 Disabling GitHub Actions

To stop automatic runs:

**Option 1: Disable workflow**
```bash
# Rename the workflow file
mv .github/workflows/daily_update.yml .github/workflows/daily_update.yml.disabled
git add .github/workflows/
git commit -m "Disable GitHub Actions"
git push
```

**Option 2: Delete workflow**
```bash
git rm .github/workflows/daily_update.yml
git commit -m "Remove GitHub Actions workflow"
git push
```

## 📊 Cost Analysis

### GitHub Actions Free Tier:
- **Public repos**: Unlimited minutes
- **Private repos**: 2,000 minutes/month
- Each workflow run ≈ 2-5 minutes
- Daily runs = ~60-150 minutes/month (well within free tier)

## 🔐 Best Practices

1. **Use Private Repository** for sensitive financial data
2. **Regularly Rotate API Keys** (every 90 days)
3. **Monitor Workflow Runs** for failures
4. **Backup Data Locally** before relying on GitHub Actions
5. **Review Commits** to ensure no sensitive data leaks

## 🆘 Troubleshooting

### "Could not deserialize key data" / "unsupported key type"
**This is the most common error!** It means the private key format is incorrect.

**Root Cause:** Your `.env` file has `\n` as literal characters, but the Python code needs ACTUAL newlines.

**Solution:**

1. **Extract the key with real newlines:**
   ```bash
   cd /Users/echo/Desktop/CoinbaseTradeTracker/CoinbaseTradeTracker
   grep COINBASE_API_SECRET_KEY .env | cut -d'=' -f2- | tr -d '"' | xargs echo -e
   ```

2. **Copy the output** (it will have multiple lines)

3. **Go to GitHub:**
   - Settings → Secrets and variables → Actions
   - Delete existing `COINBASE_API_SECRET_KEY` if it exists
   - Create new secret:
     - Name: `COINBASE_API_SECRET_KEY`
     - Value: Paste the output from step 2

4. **Verify the secret has multiple lines in the text box**

**The secret should look like:**
```
-----BEGIN EC PRIVATE KEY-----
Multiple lines
-----END EC PRIVATE KEY-----
```

**❌ NOT like this (with `\n` visible):**
```
-----BEGIN EC PRIVATE KEY-----\nMHcCAQEE...\n-----END EC PRIVATE KEY-----\n
```

### "Error: API credentials not found"
- Check that secrets are set correctly in GitHub Settings
- Secret names must match exactly: `COINBASE_API_KEY` and `COINBASE_API_SECRET_KEY` (note the `_KEY` suffix)

### "Permission denied" when pushing
- Verify workflow permissions are set to "Read and write"
- Check that GitHub token has correct permissions

### "Python module not found"
- Ensure all dependencies are in `requirements.txt`
- Check Python version in workflow matches project requirements

### Workflow not triggering
- Cron schedules can have ~15 minute delay
- Use "workflow_dispatch" to test manually
- Check repository Actions settings are enabled

## 📞 Support

For issues specific to GitHub Actions, check:
- GitHub Actions documentation: https://docs.github.com/actions
- Workflow syntax: https://docs.github.com/actions/reference/workflow-syntax-for-github-actions
- This project's Issues tab on GitHub
