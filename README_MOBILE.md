# Running on Android (Pixel 7)

## One-Time Setup

1. **Install F-Droid** (if not installed)
   - Visit https://f-droid.org/ in Chrome
   - Download and install F-Droid APK
   - Open F-Droid app

2. **Install Termux**
   - Search "Termux" in F-Droid
   - Install Termux (NOT from Google Play)
   - Open Termux app

3. **Setup Environment** (copy/paste into Termux)
   ```bash
   # Update packages
   pkg update && pkg upgrade -y

   # Install Python and Git
   pkg install -y python git

   # Install Python dependencies
   pip install youtube-transcript-api==0.6.2 flask==3.1.0 flask-cors==5.0.0

   # Setup storage access (optional)
   termux-setup-storage
   ```

4. **Clone Project** (or transfer files)
   ```bash
   # Option A: Clone from GitHub
   git clone https://github.com/yourusername/youtube-transcript.git
   cd youtube-transcript

   # Option B: Transfer files manually
   # Copy project folder to: /sdcard/Download/youtube-transcript
   # Then in Termux:
   cp -r /sdcard/Download/youtube-transcript ~/
   cd ~/youtube-transcript
   ```

## Running the Server

1. **Open Termux**

2. **Navigate to project**
   ```bash
   cd ~/youtube-transcript
   ```

3. **Start server**
   ```bash
   bash start_server.sh
   ```

   Or manually:
   ```bash
   python mobile_server.py
   ```

4. **Open Chrome on your phone**
   - Navigate to: `http://localhost:5000`
   - Bookmark this URL for easy access

5. **Use the app!**
   - Paste YouTube URL
   - Click "Process Transcript"
   - Copy/download snippets

## Stopping the Server

In Termux, press: `Ctrl + C`

Or close the Termux app.

## Keeping Server Running in Background

Install Termux:Boot (optional):
```bash
pkg install termux-boot
```

Or use Termux:Widget to create home screen shortcut.

## Troubleshooting

**"Connection refused" in browser**
- Make sure mobile_server.py is still running in Termux
- Check that you're using `localhost:5000` not `127.0.0.1:5000`

**"Module not found" errors**
- Reinstall dependencies: `pip install youtube-transcript-api flask flask-cors`

**"YouTube blocking" error**
- This shouldn't happen on mobile! But if it does:
  - Toggle airplane mode on/off (changes IP)
  - Switch between WiFi and mobile data
  - Your mobile carrier IP should not be blocked

**Termux closes automatically**
- Enable "Don't optimize" in Android battery settings for Termux
- Settings → Apps → Termux → Battery → Don't optimize

## Advanced: Auto-Start on Phone Boot

1. Install Termux:Boot from F-Droid
2. Create: `~/.termux/boot/start-transcript-server`
   ```bash
   #!/data/data/com.termux/files/usr/bin/bash
   cd ~/youtube-transcript
   python mobile_server.py
   ```
3. Make executable: `chmod +x ~/.termux/boot/start-transcript-server`
4. Server starts automatically when phone boots

## Testing Locally on Desktop First

Before deploying to phone, test on your Mac/PC:

```bash
# Install dependencies
uv pip install flask==3.1.0 flask-cors==5.0.0

# Run server
python mobile_server.py

# Open browser: http://localhost:5000
```

This verifies everything works before transferring to Android.
