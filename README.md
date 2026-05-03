# README for Torrent IMDB Parser

A powerful Python-based HTTP API that parses torrent names and metadata to extract IMDB IDs, detect series information, and enrich data with AI-powered metadata extraction.

## Features

- 🎬 **Torrent Parsing**: Extract title, year, resolution, quality, codecs, and more from torrent filenames
- 🔍 **IMDB Search**: Local indexed search for movie/series metadata
- 🤖 **AI Metadata Extraction**: Use NVIDIA free API for intelligent metadata extraction
- 📺 **Series Detection**: Automatically identify series and extract season/episode information
- 🚀 **REST API**: Simple HTTP endpoints for integration
- 🐳 **Docker Ready**: Pre-configured Dockerfile for HuggingFace deployment
- 📚 **IMDB Indexing**: Download and index IMDB datasets locally for fast searching

## Supported Torrent Metadata

- **Resolution**: 1080p, 720p, 2160p (4K), 480p, etc.
- **Quality**: WEB-DL, BluRay, HDTV, DVDRip, BDRip, etc.
- **Video Codec**: H.264, H.265/HEVC, VP9, AV1
- **Audio Codec**: AAC, DDP, TrueHD, DTS, AC3, E-AC3
- **Audio Channels**: 2.0, 5.1, 7.1
- **HDR**: Detects HDR, Dolby Vision, etc.
- **Languages**: Multi-language support (French, English, Hindi, Spanish, etc.)
- **Series Info**: Season and episode numbers

## Installation

### HuggingFace Spaces (Recommended)

The easiest way to deploy:

1. Create a new Space on [HuggingFace](https://huggingface.co/spaces)
2. Select **Docker** as the runtime
3. Clone this repository:
   ```bash
   git clone <repo-url> my-torrent-parser
   cd my-torrent-parser
   ```
4. Push to HuggingFace:
   ```bash
   git push
   ```
5. Go to Space settings and add `NVIDIA_API_KEY` as a secret
6. Restart the Space - it's deployed! 🚀

Access at: `https://huggingface.co/spaces/your-username/your-space-name`

### Local Setup

```bash
# Clone repository
git clone <repo-url>
cd parse-torrent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your settings
# Particularly: NVIDIA_API_KEY (from https://build.nvidia.com/endpoints)
```

### Docker (Local)

```bash
# Build image
docker build -t torrent-parser .

# Run container
docker run -p 7860:7860 \
  -e NVIDIA_API_KEY=your_key_here \
  torrent-parser
```

## Quick Start

### 1. Set NVIDIA API Key

Get your free API key from: https://build.nvidia.com/endpoints

```bash
# In .env file
NVIDIA_API_KEY=your_nvidia_api_key_here
```

### 2. Start the Server

```bash
# Local
python -m uvicorn app.main:app --reload --port 7860
```

### 3. Access API

Open browser to: http://localhost:7860/docs

## API Endpoints

### Health Check
```
GET /health
```

### Parse Torrent
```
POST /api/parse
Content-Type: application/json

{
  "torrent_name": "Hoppers 2026.MULTi.FRENCH.2160p.WEB.DV.HDR.H.265.mkv"
}
```

Response:
```json
{
  "status": "success",
  "data": {
    "original_name": "Hoppers 2026.MULTi.FRENCH.2160p.WEB.DV.HDR.H.265.mkv",
    "is_series": false,
    "title": "Hoppers",
    "year": 2026,
    "metadata": {
      "resolution": "2160p",
      "quality": "WEB-DL",
      "video_codec": "H.265",
      "hdr": true,
      "language": ["FRENCH", "MULTI"]
    },
    "imdb_id": "tt1234567",
    "confidence": 0.95
  }
}
```

### Parse with AI Enhancement
```
POST /api/parse-with-ai
Content-Type: application/json

{
  "torrent_name": "Fallout.2025.S02.1080p.Hindi.Multi.WEB.HDRip.DDP.5.1.x264.MSubs"
}
```

### Search IMDB
```
GET /api/search-imdb?title=Fallout&year=2025&is_series=true
```

### Statistics
```
GET /stats
```

## Example Torrent Names

The parser handles complex torrent names:

```
Hoppers 2026.MULTi.FRENCH.2160p.WEB.DV.HDR.H.265.mkv
→ Title: Hoppers, Year: 2026, Resolution: 2160p, HDR: Yes

Fallout.2025.S02.1080p.Hindi.Multi.WEB.HDRip.DDP.5.1.x264.MSubs
→ Title: Fallout, Year: 2025, Season: 2, Resolution: 1080p, Series: Yes

Munna Bhai M.B.B.S. (2003) 1080p BluRay
→ Title: Munna Bhai M.B.B.S., Year: 2003, Resolution: 1080p
```

## Configuration

Create `.env` file with:

```env
# Debug mode
DEBUG=false

# API Configuration (HuggingFace uses port 7860)
API_HOST=0.0.0.0
API_PORT=7860

# NVIDIA API Key (free tier available)
NVIDIA_API_KEY=your_key_here

# Data paths
IMDB_DATASETS_PATH=./data/imdb
IMDB_INDEX_PATH=./indexer/imdb_index

# Model settings
MODEL_NAME=bert-base-uncased
DEVICE=cpu

# Feature flags
USE_FUZZY_MATCHING=true
FUZZY_THRESHOLD=0.8
```

## NVIDIA API Setup

1. Visit: https://build.nvidia.com/
2. Sign up (free)
3. Navigate to Endpoints
4. Get your API key
5. Use Llama 2 Chat model (free tier)
6. Add to `.env` as `NVIDIA_API_KEY`

## Project Structure

```
parse-torrent/
├── app/                          # Application code
│   ├── main.py                   # FastAPI server
│   ├── core/
│   │   ├── config.py             # Configuration
│   │   └── torrent_parser.py     # Parsing logic
│   ├── services/
│   │   ├── imdb_indexer.py       # IMDB search
│   │   └── metadata_extractor.py # AI extraction
│   ├── api/
│   │   └── routes.py             # REST endpoints
│   └── models/
│       └── schemas.py            # Data models
├── Dockerfile                    # Docker image (HuggingFace ready)
├── requirements.txt              # Dependencies
├── README.md                     # This file
└── API_REFERENCE.md              # Complete API docs
```

## Performance Tips

1. **Use IMDB Indexer**: Pre-index IMDB titles for faster searching
2. **GPU Support**: Set `DEVICE=cuda` if you have NVIDIA GPU
3. **Cache Results**: Consider adding caching layer for frequent queries
4. **Batch Processing**: Process multiple torrents in parallel

## Deployment on HuggingFace Spaces

**This project is fully optimized for HuggingFace Spaces!**

### Step-by-Step:

1. **Create Space**: Go to [HuggingFace Spaces](https://huggingface.co/spaces)
2. **Choose Runtime**: Select **Docker**
3. **Add Repository**: Connect this repository
4. **Add Secret**: In Space settings, add `NVIDIA_API_KEY` secret
5. **Deploy**: HuggingFace will automatically build and deploy from the `Dockerfile`

The included `Dockerfile` is pre-configured for HuggingFace (runs on port 7860).

### Accessing Your Space:
```
https://huggingface.co/spaces/your-username/your-space-name
```

API will be available at:
```
https://your-username-your-space-name.hf.space/docs
```

## Local Development

```bash
# For local development, install dev dependencies:
# pip install -r requirements-dev.txt

# Or use the provided setup on your own machine
# See HUGGINGFACE_SPACES.md for quickest deployment
```

## Contributing

Pull requests welcome! Please ensure:
- Code is well-documented
- Tests are added for new features
- Code follows PEP 8 style guide

## License

MIT

## Support

For issues and questions, please use GitHub issues or contact the team.

## Acknowledgments

- NVIDIA for free API access
- IMDB for datasets
- FastAPI framework
- Python community
