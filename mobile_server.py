#!/usr/bin/env python3
"""
Mobile Flask server for YouTube Transcript Snippet app.
Serves both API endpoints and static frontend files.
Designed to run on Android via Termux.
"""

import os
import sys
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Import the transcript logic from api/transcript.py
sys.path.insert(0, 'api')
from transcript import (
    extract_video_id,
    fetch_transcript,
    split_into_snippets,
    format_transcript_to_markdown,
    get_error_suggestion
)

app = Flask(__name__, static_folder='public')
CORS(app)  # Enable CORS for local development

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('public', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    """Serve static files (CSS, JS)"""
    return send_from_directory('public', path)

@app.route('/api/transcript', methods=['POST', 'OPTIONS'])
def get_transcript():
    """API endpoint for fetching transcripts"""

    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response

    try:
        # Get URL from request
        data = request.get_json()
        url = data.get('url', '').strip()

        if not url:
            return jsonify({
                'success': False,
                'error': 'URL is required.',
                'suggestion': 'Please provide a YouTube URL.'
            }), 400

        # Extract video ID
        video_id = extract_video_id(url)
        if not video_id:
            return jsonify({
                'success': False,
                'error': f'Invalid YouTube URL: {url}',
                'suggestion': 'Please provide a valid YouTube video URL (e.g., youtube.com/watch?v=... or youtu.be/...)'
            }), 400

        # Fetch transcript
        segments, language, is_generated, error = fetch_transcript(video_id)
        if error:
            return jsonify({
                'success': False,
                'error': error,
                'suggestion': get_error_suggestion(error)
            }), 400

        # Split into snippets
        snippets = split_into_snippets(segments, target_minutes=15, variance_minutes=2)

        # Format full transcript
        full_transcript = format_transcript_to_markdown(segments)

        # Success response
        return jsonify({
            'success': True,
            'video_id': video_id,
            'language': language,
            'is_generated': is_generated,
            'snippets': snippets,
            'full_transcript': full_transcript
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}',
            'suggestion': 'Please try again later.'
        }), 500

if __name__ == '__main__':
    print("=" * 60)
    print("YouTube Transcript Snippet Server")
    print("=" * 60)
    print("\n📱 Running on Android/Termux")
    print("🌐 Open in browser: http://localhost:5000")
    print("⏹️  Press Ctrl+C to stop\n")
    print("=" * 60)

    # Run on all interfaces (0.0.0.0) to allow access from other devices if needed
    # Use port 5000 (common for Flask)
    app.run(host='0.0.0.0', port=5000, debug=True)
