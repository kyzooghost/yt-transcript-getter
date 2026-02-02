# YouTube Transcript Snippet Web App

A minimal static web utility that allows users to paste a YouTube URL, fetch the transcript, and view/download it in 20-minute snippets optimized for mobile copy-paste.

## Features

- **Simple Interface**: Paste a YouTube URL and get transcript snippets
- **Smart Splitting**: Automatically splits transcripts into ~20-minute chunks at sentence boundaries
- **Mobile Optimized**: Touch-friendly interface with easy copy-paste functionality
- **Multiple Formats**: Copy to clipboard or download as individual Markdown files
- **Error Handling**: Clear error messages with helpful suggestions
- **No Tracking**: No analytics, no user tracking, minimal and privacy-focused

## Project Structure

```
youtube-transcript/
├── api/
│   ├── transcript.py       # Serverless function for fetching transcripts
│   └── requirements.txt    # Python dependencies
├── public/
│   ├── index.html         # Main web page
│   ├── styles.css         # Styling
│   └── script.js          # Frontend logic
└── vercel.json            # Deployment configuration
```

## Local Development

### Prerequisites

- Python 3.9+
- Vercel CLI (optional, for local testing)

### Install Vercel CLI

```bash
npm install -g vercel
```

### Run Locally

```bash
vercel dev
```

This will start a local development server at `http://localhost:3000`.

### Testing the API Endpoint

You can test the serverless function directly:

```bash
curl -X POST http://localhost:3000/api/transcript \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtu.be/7wWRoqC0gnU"}'
```

## Deployment

### Deploy to Vercel

1. Install Vercel CLI if you haven't already:
   ```bash
   npm install -g vercel
   ```

2. Deploy to production:
   ```bash
   vercel --prod
   ```

3. Follow the prompts to link your project to Vercel

### Environment Variables

No environment variables are required for basic functionality.

## How It Works

1. **User Input**: User pastes a YouTube URL
2. **Video ID Extraction**: Frontend validates URL and extracts video ID
3. **API Request**: POST request sent to `/api/transcript` with the URL
4. **Transcript Fetching**: Serverless function uses `youtube-transcript-api` to fetch transcript
5. **Snippet Splitting**: Transcript is split into ~20-minute chunks at sentence boundaries (±2 min variance)
6. **Response**: JSON response contains snippets and full transcript
7. **Display**: Frontend renders accordion UI with copy/download buttons

## API Endpoint

### POST `/api/transcript`

**Request Body:**
```json
{
  "url": "https://youtube.com/watch?v=..."
}
```

**Success Response (200):**
```json
{
  "success": true,
  "video_id": "abc123",
  "language": "en",
  "is_generated": false,
  "snippets": [
    {
      "index": 1,
      "start_time": "00:00:00",
      "end_time": "00:20:15",
      "markdown": "00:00:00 Text here\n00:00:05 More text...",
      "duration_minutes": 20.25
    }
  ],
  "full_transcript": "00:00:00 Full text..."
}
```

**Error Response (400/500):**
```json
{
  "success": false,
  "error": "Error message",
  "suggestion": "Helpful suggestion"
}
```

## Supported URL Formats

- `https://youtu.be/VIDEO_ID`
- `https://youtube.com/watch?v=VIDEO_ID`
- `https://youtube.com/live/VIDEO_ID`
- `https://youtube.com/embed/VIDEO_ID`
- `https://youtube.com/v/VIDEO_ID`
- URLs with timestamps and query parameters

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile browsers (iOS Safari, Chrome Android)
- Requires JavaScript enabled
- Clipboard API for copy functionality (fallback provided)

## Limitations

- Individual videos only (no playlist support)
- Requires video to have captions/transcripts enabled
- Client-side throttling: 2-second minimum between requests
- No history or saved transcripts (fresh state per session)

## Troubleshooting

### "Transcripts are disabled"
The video creator has disabled captions for this video.

### "Video unavailable"
The video may be private, deleted, or region-restricted.

### "No transcript found"
The video doesn't have any available transcripts or captions.

### "Invalid YouTube URL"
Check that you're using a valid YouTube video URL format.

## License

Same as the main CLI tool.
