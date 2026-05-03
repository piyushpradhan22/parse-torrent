"""Metadata extraction using NVIDIA-hosted models with regex fallback."""

import httpx
import json
import logging
import re
from typing import Optional, Dict, List
from app.core.config import settings


logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extract metadata from torrent names using NVIDIA API and local models."""
    
    NVIDIA_API_ENDPOINT = settings.NVIDIA_API_BASE_URL
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the extractor.
        
        Args:
            api_key: NVIDIA API key (uses settings if not provided)
        """
        self.api_key = api_key or settings.NVIDIA_API_KEY
        self.client = httpx.AsyncClient(timeout=30.0)
        self.models: List[str] = [
            settings.NVIDIA_API_MODEL,
            *settings.NVIDIA_API_FALLBACK_MODELS,
        ]
    
    async def extract_metadata(self, text: str) -> Dict:
        """
        Extract metadata from torrent name using NVIDIA API.
        
        Args:
            text: Torrent name or description
            
        Returns:
            Dictionary with extracted metadata
        """
        if not self.api_key:
            return await self._extract_with_fallback(text)
        
        try:
            return await self._extract_with_nvidia_api(text)
        except Exception as e:
            logger.warning("Error with NVIDIA API: %s. Using fallback method.", e)
            return await self._extract_with_fallback(text)
    
    async def _extract_with_nvidia_api(self, text: str) -> Dict:
        """Extract using NVIDIA API."""
        prompt = f"""Extract metadata from this torrent/media filename:
        
"{text}"

Provide JSON response with:
- title: Media title
- year: Release year
- resolution: Video resolution (1080p, 720p, 2160p, etc.)
- quality: Quality type (WEB-DL, BluRay, HDTV, etc.)
- audio_codec: Audio codec (AAC, DDP, etc.)
- audio_channels: Audio channels (5.1, 7.1, etc.)
- video_codec: Video codec (H.264, H.265, etc.)
- hdr: Whether HDR is present (true/false)
- language: List of languages
- is_series: Whether it's a series (true/false)
- notes: Any additional observations

Return only valid JSON."""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        seen = set()
        candidate_models = [m for m in self.models if m and not (m in seen or seen.add(m))]
        if not candidate_models:
            raise Exception("No NVIDIA models configured")

        last_error = None

        for model in candidate_models:
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                "temperature": 0.2,
                "top_p": 0.7,
                "max_tokens": 500,
            }

            response = await self.client.post(
                f"{self.NVIDIA_API_ENDPOINT}/chat/completions",
                json=payload,
                headers=headers,
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")

                try:
                    metadata = json.loads(content)
                    return metadata if isinstance(metadata, dict) else {}
                except json.JSONDecodeError:
                    json_match = re.search(r"\{.*\}", content, re.DOTALL)
                    if json_match:
                        try:
                            metadata = json.loads(json_match.group())
                            return metadata if isinstance(metadata, dict) else {}
                        except json.JSONDecodeError:
                            pass

                return {}

            # Try next model on not-found/bad-request style errors.
            if response.status_code in (400, 404):
                last_error = f"model={model}, status={response.status_code}, body={response.text[:300]}"
                logger.info("NVIDIA model failed, trying next model: %s", last_error)
                continue

            raise Exception(f"NVIDIA API error {response.status_code}: {response.text[:300]}")

        raise Exception(f"NVIDIA API model resolution failed: {last_error}")
    
    async def _extract_with_fallback(self, text: str) -> Dict:
        """Fallback extraction using regex patterns."""

        metadata = {
            'title': None,
            'year': None,
            'resolution': None,
            'quality': None,
            'audio_codec': None,
            'audio_channels': None,
            'video_codec': None,
            'hdr': False,
            'language': [],
            'is_series': False,
        }
        
        # Resolution
        res_match = re.search(r'\b(4320p|2160p|1440p|1080p|720p|480p|360p)\b', text, re.IGNORECASE)
        if res_match:
            metadata['resolution'] = res_match.group(1)
        
        # Quality
        quality_match = re.search(r'\b(WEB-?DL|WEBRip|BluRay|HDTV|DVDRip|BDRip)\b', text, re.IGNORECASE)
        if quality_match:
            metadata['quality'] = quality_match.group(1)
        
        # Video codec
        video_match = re.search(r'\b(H\.?264|H\.?265|HEVC|VP9|AV1)\b', text, re.IGNORECASE)
        if video_match:
            metadata['video_codec'] = video_match.group(1)
        
        # Audio codec
        audio_match = re.search(r'\b(AAC|DDP|TrueHD|DTS|AC3|E-AC3)\b', text, re.IGNORECASE)
        if audio_match:
            metadata['audio_codec'] = audio_match.group(1)
        
        # Audio channels
        channels_match = re.search(r'\b(7\.1|5\.1|2\.0)\b', text, re.IGNORECASE)
        if channels_match:
            metadata['audio_channels'] = channels_match.group(1)
        
        # HDR
        metadata['hdr'] = bool(re.search(r'\b(HDR|DV|Dolby\s?Vision)\b', text, re.IGNORECASE))
        
        # Languages
        languages = []
        if re.search(r'\bFRENCH\b', text, re.IGNORECASE):
            languages.append('FRENCH')
        if re.search(r'\bENGLISH\b', text, re.IGNORECASE):
            languages.append('ENGLISH')
        if re.search(r'\bHINDI\b', text, re.IGNORECASE):
            languages.append('HINDI')
        if re.search(r'\bMULTi\b', text, re.IGNORECASE):
            languages.append('MULTI')
        metadata['language'] = languages
        
        # Series detection
        metadata['is_series'] = bool(re.search(r'\bS\d{1,2}E\d{1,2}\b', text, re.IGNORECASE))
        
        return metadata
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
