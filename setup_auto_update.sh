#!/bin/bash
# Setup script for automatic daily updates using launchd on macOS

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Detect Python path
PYTHON_PATH=$(which python)
if [ -z "$PYTHON_PATH" ]; then
    echo "❌ Python not found. Make sure conda environment is activated."
    exit 1
fi

echo "Using Python: $PYTHON_PATH"
echo "Project directory: $PROJECT_DIR"

# Create the plist file for launchd
PLIST_FILE="$HOME/Library/LaunchAgents/com.coinbase.tradetracker.plist"

cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.coinbase.tradetracker</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>$PROJECT_DIR/daily_update.py</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>0</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    
    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/logs/launchd_stdout.log</string>
    
    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/logs/launchd_stderr.log</string>
    
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
EOF

echo "✅ Created plist file at: $PLIST_FILE"

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"

# Load the launch agent
launchctl unload "$PLIST_FILE" 2>/dev/null
launchctl load "$PLIST_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Successfully loaded launch agent"
    echo ""
    echo "The script will run automatically every day at midnight (00:00)"
    echo ""
    echo "Useful commands:"
    echo "  - Check status: launchctl list | grep coinbase.tradetracker"
    echo "  - View logs: tail -f $PROJECT_DIR/logs/daily_update_*.log"
    echo "  - Stop auto-update: launchctl unload $PLIST_FILE"
    echo "  - Start auto-update: launchctl load $PLIST_FILE"
    echo "  - Run manually now: python $PROJECT_DIR/daily_update.py"
else
    echo "❌ Failed to load launch agent"
    exit 1
fi
