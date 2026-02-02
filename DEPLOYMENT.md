# Deployment Guide - YouTube Transcript Snippet Web App

## Quick Deployment to Vercel

### Prerequisites
- [Vercel account](https://vercel.com/signup) (free tier works)
- Git repository with the code
- Vercel CLI (optional, for command-line deployment)

### Option 1: Deploy via Vercel Dashboard (Easiest)

1. **Push your code to GitHub**
   ```bash
   git push origin main
   ```

2. **Connect to Vercel**
   - Go to [vercel.com/new](https://vercel.com/new)
   - Click "Import Project"
   - Connect your GitHub account
   - Select the `youtube-transcript` repository

3. **Configure Project**
   - Framework Preset: **Other** (no framework needed)
   - Build Command: Leave empty or use `echo 'No build required'`
   - Output Directory: `public`
   - Root Directory: `.` (project root)

4. **Deploy**
   - Click "Deploy"
   - Wait for deployment to complete (usually < 1 minute)
   - Get your live URL (e.g., `https://youtube-transcript-xyz.vercel.app`)

### Option 2: Deploy via Vercel CLI

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy**
   ```bash
   # From project root directory
   vercel --prod
   ```

4. **Follow prompts**
   - Set up and deploy? **Y**
   - Which scope? Select your account
   - Link to existing project? **N** (for first time)
   - Project name? (default: youtube-transcript)
   - In which directory is your code located? **.**

5. **Get deployment URL**
   - CLI will output the live URL
   - Also visible at [vercel.com/dashboard](https://vercel.com/dashboard)

## Local Testing Before Deployment

### Install Vercel CLI
```bash
npm install -g vercel
```

### Run Development Server
```bash
vercel dev
```

This starts a local server at `http://localhost:3000` with:
- Static file serving from `public/`
- Serverless function at `/api/transcript`
- Hot reloading on file changes

### Test the API Endpoint
```bash
curl -X POST http://localhost:3000/api/transcript \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtu.be/7wWRoqC0gnU"}'
```

### Test the Web Interface
1. Open `http://localhost:3000` in your browser
2. Paste a YouTube URL
3. Click "Process Transcript"
4. Verify snippets appear correctly
5. Test copy and download buttons

## Project Structure for Deployment

```
youtube-transcript/
├── api/                    # Serverless functions
│   ├── transcript.py      # Main API endpoint
│   └── requirements.txt   # Python dependencies
├── public/                # Static files (served at /)
│   ├── index.html
│   ├── styles.css
│   └── script.js
└── vercel.json           # Deployment configuration
```

## Vercel Configuration Explained

```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "/api/$1"
    }
  ],
  "functions": {
    "api/transcript.py": {
      "runtime": "python3.9"
    }
  }
}
```

- **rewrites**: Routes `/api/*` requests to serverless functions
- **functions**: Specifies Python runtime for the API endpoint
- **No build step needed**: Static files served directly from `public/`

## Post-Deployment

### Verify Deployment
1. Visit your Vercel URL
2. Test with a YouTube URL:
   - Example: `https://youtu.be/dQw4w9WgXcQ`
   - Example: `https://youtube.com/watch?v=7wWRoqC0gnU`

3. Check for:
   - Successful transcript fetch
   - Correct snippet splitting (~20 min each)
   - Copy button works
   - Download button creates `.md` files
   - Mobile responsive design

### View Logs
- Go to [vercel.com/dashboard](https://vercel.com/dashboard)
- Select your project
- Click "Deployments" → Select latest deployment → "Functions"
- View logs for `/api/transcript` function

### Custom Domain (Optional)
1. Go to project settings on Vercel dashboard
2. Navigate to "Domains"
3. Add your custom domain
4. Follow DNS configuration instructions

## Troubleshooting

### "Module not found" errors
- Check `api/requirements.txt` has correct dependencies
- Ensure `youtube-transcript-api` version is compatible
- Check Python runtime version in `vercel.json`

### API endpoint returns 404
- Verify `vercel.json` has correct rewrites configuration
- Check that `api/transcript.py` exists and is committed
- Ensure file is named exactly `transcript.py` (case-sensitive)

### CORS errors
- API endpoint includes `Access-Control-Allow-Origin: *` headers
- Check browser console for specific CORS issues
- Verify OPTIONS method is handled in `transcript.py`

### Slow response times
- Cold start: First request may be slow (~2-5 seconds)
- Subsequent requests should be faster
- Consider using Vercel Pro for faster cold starts

### Python dependency issues
- Ensure `requirements.txt` uses pinned versions
- Test locally with `vercel dev` before deploying
- Check Vercel function logs for import errors

## Environment Variables

Currently, no environment variables are required. If you need to add any:

1. **Via Dashboard**
   - Go to project settings → Environment Variables
   - Add key-value pairs

2. **Via CLI**
   ```bash
   vercel env add VARIABLE_NAME
   ```

## Monitoring & Analytics

### Built-in Vercel Analytics (Free)
- Automatic page view tracking
- Performance metrics
- No setup required

### Function Logs
- Available in Vercel dashboard
- Real-time streaming
- Filter by function name
- Export to external logging services

## Cost Considerations

### Vercel Free Tier Limits
- ✅ Unlimited deployments
- ✅ Unlimited bandwidth for personal projects
- ✅ 100 GB-hours serverless function execution
- ✅ 1000 GB bandwidth for commercial projects

### Expected Usage
- **Small scale** (< 1000 requests/month): Free tier sufficient
- **Medium scale** (1000-10000 requests/month): Free tier likely sufficient
- **Large scale** (> 10000 requests/month): Consider Pro plan

### Function Execution Costs
- API calls to YouTube transcript API are free
- Each request takes ~1-3 seconds
- Free tier: 100 GB-hours = ~100,000 requests at 3 seconds each

## Security Considerations

1. **Rate Limiting**
   - Client-side: 2-second throttle between requests
   - Consider adding server-side rate limiting for production

2. **API Abuse Prevention**
   - No API key required (public endpoint)
   - Monitor usage via Vercel dashboard
   - Add rate limiting if needed

3. **CORS Policy**
   - Currently allows all origins (`*`)
   - Consider restricting to specific domains for production

4. **No User Data Storage**
   - No cookies, localStorage, or tracking
   - Privacy-friendly by design

## Updating the App

### Push updates
```bash
git add .
git commit -m "Update feature"
git push origin main
```

### Automatic Redeployment
- Vercel automatically redeploys on push to main branch
- Takes ~30-60 seconds
- Zero downtime deployments

### Manual Deployment
```bash
vercel --prod
```

## Support Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Vercel Python Runtime](https://vercel.com/docs/runtimes#official-runtimes/python)
- [YouTube Transcript API](https://github.com/jdepoix/youtube-transcript-api)
- [Project Repository](https://github.com/yourusername/youtube-transcript)

## Success Checklist

Before marking deployment complete:

- [ ] Code pushed to Git repository
- [ ] Deployed to Vercel successfully
- [ ] Tested with multiple YouTube URLs
- [ ] Verified snippet splitting works correctly
- [ ] Tested copy button on desktop
- [ ] Tested copy button on mobile (iOS/Android)
- [ ] Tested download button
- [ ] Verified error handling (invalid URL, no transcript)
- [ ] Checked responsive design on mobile
- [ ] Reviewed function logs for errors
- [ ] Confirmed no CORS errors in browser console
