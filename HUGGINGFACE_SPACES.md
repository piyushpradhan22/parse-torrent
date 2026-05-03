"""Quick deployment guide for HuggingFace Spaces"""

# HUGGINGFACE_SPACES_DEPLOYMENT.md

## HuggingFace Spaces Deployment Guide

> This project is **production-ready** for HuggingFace Spaces!

### Quick Start (5 minutes)

#### Step 1: Create a HuggingFace Space

1. Go to [HuggingFace Spaces](https://huggingface.co/spaces)
2. Click **Create new Space**
3. Choose settings:
   - **Name**: `torrent-imdb-parser` (or your preferred name)
   - **License**: Apache 2.0 (or your choice)
   - **Space SDK**: Select **Docker**
   - **Visibility**: Public or Private
4. Click **Create Space**

#### Step 2: Clone the Repository

```bash
# Clone this repo into the Space
git clone https://github.com/your-username/parse-torrent.git ./your-space-name
cd your-space-name
```

Or just copy all files to your Space repository.

#### Step 3: Add NVIDIA API Key Secret

1. Go to your Space settings
2. Find **Repository secrets**
3. Add a new secret:
   - **Name**: `NVIDIA_API_KEY`
   - **Value**: Your API key from https://build.nvidia.com/endpoints
4. Save

#### Step 4: Push Code

```bash
git add .
git commit -m "Deploy torrent parser to HuggingFace"
git push
```

#### Step 5: Wait for Deployment

HuggingFace will automatically:
1. Detect the `Dockerfile`
2. Build the Docker image
3. Deploy your Space
4. Assign a public URL

Your API will be available at:
```
https://your-username-your-space-name.hf.space
```

---

## Accessing Your Deployed API

### Swagger UI Documentation
```
https://your-username-your-space-name.hf.space/docs
```

### API Endpoints
```
POST   https://your-username-your-space-name.hf.space/api/parse
POST   https://your-username-your-space-name.hf.space/api/parse-with-ai
GET    https://your-username-your-space-name.hf.space/api/search-imdb
GET    https://your-username-your-space-name.hf.space/health
```

### Example API Call
```bash
curl -X POST https://your-username-your-space-name.hf.space/api/parse \
  -H "Content-Type: application/json" \
  -d '{
    "torrent_name": "Inception.2010.1080p.BluRay.x264"
  }'
```

---

## What's Included

✅ **Dockerfile** - Fully optimized for HuggingFace (port 7860)
✅ **FastAPI** - REST API with Swagger documentation
✅ **Torrent Parser** - Extracts metadata from torrent names
✅ **IMDB Integration** - Searches for matching IMDB titles
✅ **AI Enhancement** - Uses NVIDIA API for intelligent extraction
✅ **Health Checks** - Built-in monitoring

---

## Environment Variables

The only required secret is:

| Variable | Source |
|----------|--------|
| `NVIDIA_API_KEY` | https://build.nvidia.com/endpoints (free) |

All other settings use defaults optimized for HuggingFace.

---

## Docker Image Details

- **Base Image**: `python:3.11-slim` (minimal size)
- **Port**: `7860` (HuggingFace standard)
- **Health Check**: Enabled
- **Build Time**: ~2-3 minutes
- **Image Size**: ~1.5GB (with all dependencies)

---

## Usage Examples

### Parse a Movie

```bash
curl -X POST https://your-space.hf.space/api/parse \
  -H "Content-Type: application/json" \
  -d '{
    "torrent_name": "Oppenheimer.2023.2160p.WEB-DL.H.265.AAC.5.1"
  }'
```

Response:
```json
{
  "status": "success",
  "data": {
    "original_name": "Oppenheimer.2023.2160p.WEB-DL.H.265.AAC.5.1",
    "is_series": false,
    "title": "Oppenheimer",
    "year": 2023,
    "metadata": {
      "resolution": "2160p",
      "quality": "WEB-DL",
      "video_codec": "H.265",
      "audio_codec": "AAC",
      "audio_channels": "5.1"
    },
    "imdb_id": "tt15398776",
    "confidence": 0.98
  }
}
```

### Parse a TV Series

```bash
curl -X POST https://your-space.hf.space/api/parse \
  -H "Content-Type: application/json" \
  -d '{
    "torrent_name": "Breaking.Bad.S05E16.1080p.HDTV.x264.DDP.5.1"
  }'
```

### Search IMDB

```bash
curl https://your-space.hf.space/api/search-imdb?title=Inception&year=2010
```

---

## Space Health & Monitoring

### Check Space Status
```bash
curl https://your-space.hf.space/health
```

Expected response:
```json
{
  "status": "healthy",
  "app_name": "Torrent IMDB Parser",
  "version": "1.0.0"
}
```

### View Logs
In Space settings, view the "Logs" tab to debug any issues.

---

## Troubleshooting

### Space won't start
**Problem**: Build fails or Space doesn't respond

**Solution**:
1. Check Space logs in settings
2. Verify `NVIDIA_API_KEY` is set as secret
3. Ensure all files are committed
4. Restart Space from settings

### API returns 502 Bad Gateway
**Problem**: Space is temporarily unavailable

**Solution**:
- Space may be restarting (normal, takes 1-2 min)
- Check Space logs
- Try again in a few seconds

### Slow responses
**Problem**: First request is slow

**Solution**: Normal - Space is loading model. First request loads everything into memory.

---

## Scaling Considerations

- **Free Tier**: Suitable for light usage (< 100 requests/day)
- **Pro Tier**: Better for higher traffic
- **Persistent Storage**: Available for caching IMDB index
- **GPU**: Not required (CPU sufficient for parsing)

---

## Advanced Configuration

To customize beyond defaults, modify `.env` before deploying:

```env
DEBUG=false
API_HOST=0.0.0.0
API_PORT=7860
NVIDIA_API_KEY=your-key  # Or use secret
DEVICE=cpu
USE_FUZZY_MATCHING=true
FUZZY_THRESHOLD=0.8
```

---

## Security Notes

✅ **API Keys**: Only stored in HuggingFace Secrets (secure)
✅ **Data**: No persistent storage of queries
✅ **CORS**: Enabled for all origins (customizable)
✅ **HTTPS**: Built-in with HuggingFace domain

---

## Support & Issues

- **HuggingFace Docs**: https://huggingface.co/docs/hub/spaces
- **NVIDIA API**: https://build.nvidia.com/
- **FastAPI**: https://fastapi.tiangolo.com/
- **GitHub Issues**: Submit issues in the repository

---

## Next Steps

After deployment:

1. ✅ Test API at `/docs` endpoint
2. ✅ Try parsing a torrent
3. ✅ Search IMDB for matches
4. ✅ Share your Space URL with others
5. ✅ Star the repository! ⭐

---

## One-Liner Deployment

```bash
# If you already have git configured
git clone https://huggingface.co/spaces/your-username/torrent-parser
cd torrent-parser
# Add NVIDIA_API_KEY to .env or use Space secrets
git push
```

That's it! Your API is live! 🚀
