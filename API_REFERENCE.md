"""API Reference Documentation"""

# API Reference

## Overview

The Torrent IMDB Parser API provides RESTful endpoints for parsing torrent metadata and searching IMDB database.

### Base URL
```
http://localhost:8000/api
```

### Authentication
No authentication required for basic usage. For production, consider adding API key authentication.

---

## Endpoints

### 1. Health Check

Check if the API is running and healthy.

**Endpoint:**
```
GET /health
```

**Parameters:** None

**Response:**
```json
{
  "status": "healthy",
  "app_name": "Torrent IMDB Parser",
  "version": "1.0.0"
}
```

**Status Codes:**
- `200 OK` - API is healthy

---

### 2. Application Statistics

Get application statistics and indexing info.

**Endpoint:**
```
GET /stats
```

**Parameters:** None

**Response:**
```json
{
  "imdb_titles_indexed": 10500000,
  "api_version": "1.0.0"
}
```

**Status Codes:**
- `200 OK` - Statistics retrieved

---

### 3. Parse Torrent

Parse a torrent name and extract metadata.

**Endpoint:**
```
POST /api/parse
```

**Request Body:**
```json
{
  "torrent_name": "Hoppers 2026.MULTi.FRENCH.2160p.WEB.DV.HDR.H.265.mkv",
  "torrent_file": null
}
```

**Parameters:**
- `torrent_name` (string, optional): Torrent filename or name
- `torrent_file` (string, optional): Alternative to torrent_name
- At least one of the above is required

**Response:**
```json
{
  "status": "success",
  "data": {
    "original_name": "Hoppers 2026.MULTi.FRENCH.2160p.WEB.DV.HDR.H.265.mkv",
    "is_series": false,
    "title": "Hoppers",
    "year": 2026,
    "episode": null,
    "metadata": {
      "title": "Hoppers",
      "year": 2026,
      "resolution": "2160p",
      "quality": "WEB-DL",
      "audio_codec": "DDP",
      "audio_channels": "5.1",
      "video_codec": "H.265",
      "hdr": true,
      "publisher": null,
      "language": ["FRENCH", "MULTI"]
    },
    "imdb_id": "tt1234567",
    "confidence": 0.95
  },
  "error": null
}
```

**Response Fields:**
- `status` (string): "success" or "error"
- `data` (object): Parsed torrent information (if successful)
  - `original_name` (string): Original input name
  - `is_series` (boolean): Whether it's a TV series
  - `title` (string): Extracted title
  - `year` (integer): Release year
  - `episode` (object): Episode info if series (season, episode numbers)
  - `metadata` (object): Extracted technical metadata
    - `resolution` (string): Video resolution
    - `quality` (string): Release quality
    - `audio_codec` (string): Audio codec name
    - `audio_channels` (string): Audio channel configuration
    - `video_codec` (string): Video codec name
    - `hdr` (boolean): HDR presence
    - `language` (array): Languages detected
  - `imdb_id` (string): IMDB ID if found
  - `confidence` (number): Match confidence (0-1)
- `error` (string): Error message if unsuccessful

**Status Codes:**
- `200 OK` - Parsing successful
- `400 Bad Request` - Missing required parameters
- `500 Internal Server Error` - Processing error

**Examples:**

Movie:
```bash
curl -X POST http://localhost:8000/api/parse \
  -H "Content-Type: application/json" \
  -d '{"torrent_name": "The.Matrix.1999.720p.WEB-DL.x264.AAC.2.0"}'
```

Series:
```bash
curl -X POST http://localhost:8000/api/parse \
  -H "Content-Type: application/json" \
  -d '{"torrent_name": "Breaking.Bad.S05E16.1080p.HDTV.x264.DDP.5.1"}'
```

---

### 4. Parse with AI Enhancement

Parse torrent using NVIDIA AI API for intelligent metadata extraction.

**Endpoint:**
```
POST /api/parse-with-ai
```

**Request Body:**
```json
{
  "torrent_name": "Inception.2010.1080p.BluRay.x264.AAC.5.1.DL",
  "torrent_file": null
}
```

**Parameters:** Same as `/api/parse`

**Response:** Same as `/api/parse`, but with AI-enhanced metadata

**Note:** Requires `NVIDIA_API_KEY` to be configured. Falls back to regex extraction if API unavailable.

**Status Codes:**
- `200 OK` - Parsing successful
- `400 Bad Request` - Missing parameters
- `503 Service Unavailable` - NVIDIA API unreachable (uses fallback)

---

### 5. Search IMDB

Search for titles in the local IMDB index.

**Endpoint:**
```
GET /api/search-imdb
```

**Query Parameters:**
- `title` (string, required): Movie/Series title to search for
- `year` (integer, optional): Release year (allows ±1 year)
- `is_series` (boolean, optional): Filter by type (true for series, false for movies)
- `threshold` (float, optional): Fuzzy match threshold (0-1, default: 0.65)

**Response:**
```json
{
  "status": "success",
  "query": {
    "title": "Inception",
    "year": 2010,
    "is_series": false
  },
  "results": [
    {
      "imdb_id": "tt1375666",
      "title": "Inception",
      "title_type": "movie",
      "year": 2010,
      "is_series": false,
      "episode_count": null,
      "score": 1.0
    },
    {
      "imdb_id": "tt2488496",
      "title": "The Inception",
      "title_type": "movie",
      "year": 2010,
      "is_series": false,
      "episode_count": null,
      "score": 0.85
    }
  ],
  "total": 2
}
```

**Response Fields:**
- `status` (string): "success" or "error"
- `query` (object): Query parameters used
- `results` (array): List of matching titles, sorted by score (highest first)
  - `imdb_id` (string): IMDB ID (e.g., tt1234567)
  - `title` (string): Title name
  - `title_type` (string): Type (movie, tvSeries, etc.)
  - `year` (integer): Release year
  - `is_series` (boolean): Whether it's a series
  - `episode_count` (integer): Number of episodes (for series)
  - `score` (number): Match score (0-1, higher is better)
- `total` (integer): Total results found

**Status Codes:**
- `200 OK` - Search successful
- `503 Service Unavailable` - IMDB index not initialized

**Examples:**

Search movie by title:
```bash
curl "http://localhost:8000/api/search-imdb?title=Inception"
```

Search with filters:
```bash
curl "http://localhost:8000/api/search-imdb?title=Breaking%20Bad&is_series=true"
```

Search movie by year:
```bash
curl "http://localhost:8000/api/search-imdb?title=Oppenheimer&year=2023"
```

---

## Data Models

### TorrentQuery
```json
{
  "torrent_name": "string (optional)",
  "torrent_file": "string (optional)"
}
```

### MetadataExtraction
```json
{
  "title": "string (optional)",
  "year": "integer (optional)",
  "resolution": "string (optional)",
  "quality": "string (optional)",
  "audio_codec": "string (optional)",
  "audio_channels": "string (optional)",
  "video_codec": "string (optional)",
  "hdr": "boolean",
  "publisher": "string (optional)",
  "language": ["string"]
}
```

### EpisodeInfo
```json
{
  "season": "integer (optional)",
  "episode": "integer (optional)",
  "episode_title": "string (optional)"
}
```

### TorrentParsedInfo
```json
{
  "original_name": "string",
  "is_series": "boolean",
  "title": "string (optional)",
  "year": "integer (optional)",
  "episode": "EpisodeInfo (optional)",
  "metadata": "MetadataExtraction (optional)",
  "imdb_id": "string (optional)",
  "confidence": "number (optional)"
}
```

---

## Error Handling

All endpoints return consistent error format:

```json
{
  "status": "error",
  "data": null,
  "error": "Error message describing what went wrong"
}
```

### Common Error Codes

- `400 Bad Request` - Missing required parameters or invalid format
- `403 Forbidden` - API rate limit exceeded
- `500 Internal Server Error` - Server processing error
- `503 Service Unavailable` - External service unavailable

---

## Rate Limiting

No rate limiting by default, but can be added for production deployment.

---

## CORS

CORS is enabled for all origins (`*`). For production, configure specific allowed origins in `app/main.py`.

---

## Examples

### Example 1: Basic Parsing

```bash
curl -X POST http://localhost:8000/api/parse \
  -H "Content-Type: application/json" \
  -d '{
    "torrent_name": "Dune.Part.Two.2024.1080p.WEB-DL.x264"
  }'
```

### Example 2: Batch Processing

```python
import httpx

torrents = [
    "Movie1.2020.720p.BluRay",
    "Series.2021.S01E01.1080p.WEB-DL",
    "Movie2.2022.2160p.WEB.HDR"
]

async with httpx.AsyncClient() as client:
    tasks = [
        client.post("http://localhost:8000/api/parse", json={"torrent_name": t})
        for t in torrents
    ]
    responses = await asyncio.gather(*tasks)
    results = [r.json() for r in responses]
```

### Example 3: Search and Parse

```python
# Parse torrent
parse_response = await client.post(
    "http://localhost:8000/api/parse",
    json={"torrent_name": "Inception.2010.1080p.BluRay"}
)
parsed_data = parse_response.json()

# Get IMDB info
if not parsed_data["data"]["imdb_id"]:
    search_response = await client.get(
        "http://localhost:8000/api/search-imdb",
        params={
            "title": parsed_data["data"]["title"],
            "year": parsed_data["data"]["year"]
        }
    )
    search_results = search_response.json()
```

---

## SDK/Library Support

### Python
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/parse",
        json={"torrent_name": "Movie.2024.1080p"}
    )
    data = response.json()
```

### JavaScript/Node.js
```javascript
const response = await fetch("http://localhost:8000/api/parse", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ torrent_name: "Movie.2024.1080p" })
});
const data = await response.json();
```

### cURL
```bash
curl -X POST http://localhost:8000/api/parse \
  -H "Content-Type: application/json" \
  -d '{"torrent_name": "Movie.2024.1080p"}'
```

---

## Performance Notes

- Average parsing time: 10-50ms
- IMDB search time: 5-100ms (depending on index size)
- AI parsing time: 500-2000ms (depends on NVIDIA API)
- Batch processing recommended for multiple torrents

---

## Support & Documentation

- Full API docs: `http://localhost:8000/docs` (Swagger UI)
- Alternative docs: `http://localhost:8000/redoc` (ReDoc)
- README: See README.md
- Examples: See examples.py
