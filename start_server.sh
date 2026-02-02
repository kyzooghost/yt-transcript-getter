#!/data/data/com.termux/files/usr/bin/bash
# Start script for YouTube Transcript Server on Android

echo "🚀 Starting YouTube Transcript Server..."
echo ""

# Check if in correct directory
if [ ! -f "mobile_server.py" ]; then
    echo "❌ Error: mobile_server.py not found"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Check if Python packages are installed
if ! python -c "import flask" 2>/dev/null; then
    echo "❌ Flask not installed. Installing dependencies..."
    pip install flask==3.1.0 flask-cors==5.0.0 youtube-transcript-api==0.6.2
fi

# Start the server
echo "✅ Starting server on http://localhost:5000"
echo "📱 Open Chrome and navigate to: http://localhost:5000"
echo ""
python mobile_server.py
