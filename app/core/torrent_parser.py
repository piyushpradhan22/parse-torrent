"""Torrent name parser - extracts metadata from torrent filenames."""

import re
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass


@dataclass
class ParsedTorrent:
    """Parsed torrent information."""
    title: str
    year: Optional[int]
    season: Optional[int]
    episode: Optional[int]
    episode_title: Optional[str]
    resolution: Optional[str]
    quality: Optional[str]
    audio_codec: Optional[str]
    audio_channels: Optional[str]
    video_codec: Optional[str]
    hdr: bool
    language: List[str]
    publisher: Optional[str]
    is_series: bool


class TorrentParser:
    """Parser for extracting metadata from torrent names."""
    
    # Resolution patterns
    RESOLUTION_PATTERN = re.compile(r'\b(4320p|2160p|1440p|1080p|720p|480p|360p|240p|8K|4K|HD|SD)\b', re.IGNORECASE)
    
    # Quality patterns
    QUALITY_PATTERN = re.compile(r'\b(WEB-?DL|WEBRip|BluRay|Blu-Ray|HDTV|DVDRip|BDRip|HDRip|PROPER|REPACK)\b', re.IGNORECASE)
    
    # Video codec patterns
    VIDEO_CODEC_PATTERN = re.compile(r'\b(H\.?264|H\.?265|HEVC|VP9|AV1|MPEG-?2|VC-?1)\b', re.IGNORECASE)
    
    # Audio codec patterns
    AUDIO_CODEC_PATTERN = re.compile(r'\b(AAC|DDP|TrueHD|DTS|FLAC|MP3|Opus|AC3|E-AC3)\b', re.IGNORECASE)
    
    # Audio channels patterns
    AUDIO_CHANNELS_PATTERN = re.compile(r'\b(7\.1|5\.1|2\.0|Mono|Stereo|2CH|6CH|8CH)\b', re.IGNORECASE)
    
    # HDR patterns
    HDR_PATTERN = re.compile(r'\b(HDR|DV|Dolby\s?Vision|SDR)\b', re.IGNORECASE)
    
    # Season/Episode patterns
    EPISODE_PATTERN = re.compile(r'S(\d{1,2})E(\d{1,2})', re.IGNORECASE)
    SEASON_PATTERN = re.compile(r'Season\s+(\d{1,2})', re.IGNORECASE)
    
    # Language patterns
    LANGUAGE_PATTERNS = {
        'FRENCH': r'\bFRENCH\b',
        'ENGLISH': r'\bENGLISH\b',
        'HINDI': r'\bHINDI\b',
        'SPANISH': r'\bSPANISH\b',
        'PORTUGUESE': r'\bPORTUGUESE\b',
        'GERMAN': r'\bGERMAN\b',
        'ITALIAN': r'\bITALIAN\b',
        'JAPANESE': r'\bJAPANESE\b',
        'CHINESE': r'\bCHINESE\b',
        'RUSSIAN': r'\bRUSSIAN\b',
        'MULTI': r'\bMULTi\b',
    }
    
    # Publisher/Release group patterns
    PUBLISHER_PATTERN = re.compile(r'-([A-Za-z0-9]+)$')
    
    # Year pattern (1900-2100)
    YEAR_PATTERN = re.compile(r'\b(19\d{2}|20\d{2})\b')
    
    def parse(self, torrent_name: str) -> ParsedTorrent:
        """
        Parse a torrent name and extract metadata.
        
        Args:
            torrent_name: The torrent filename/name
            
        Returns:
            ParsedTorrent object with extracted metadata
        """
        # Clean and normalize
        name = self._normalize(torrent_name)
        
        # Extract main components
        title = self._extract_title(name, torrent_name)
        year = self._extract_year(name)
        season, episode = self._extract_episode(name)
        is_series = season is not None or episode is not None
        
        # Extract technical details
        resolution = self._extract_first_match(name, self.RESOLUTION_PATTERN)
        quality = self._extract_first_match(name, self.QUALITY_PATTERN)
        audio_codec = self._extract_first_match(name, self.AUDIO_CODEC_PATTERN)
        audio_channels = self._extract_first_match(name, self.AUDIO_CHANNELS_PATTERN)
        video_codec = self._extract_first_match(name, self.VIDEO_CODEC_PATTERN)
        hdr = bool(self.HDR_PATTERN.search(name))
        language = self._extract_languages(name)
        publisher = self._extract_publisher(name)
        
        return ParsedTorrent(
            title=title,
            year=year,
            season=season,
            episode=episode,
            episode_title=None,
            resolution=resolution,
            quality=quality,
            audio_codec=audio_codec,
            audio_channels=audio_channels,
            video_codec=video_codec,
            hdr=hdr,
            language=language,
            publisher=publisher,
            is_series=is_series,
        )
    
    def _normalize(self, text: str) -> str:
        """Normalize torrent name."""
        # Remove file extensions
        text = re.sub(r'\.(mkv|avi|mp4|mov|flv|wmv)$', '', text, flags=re.IGNORECASE)
        # Replace dots and underscores with spaces (except in titles like M.B.B.S.)
        text = re.sub(r'[\._]+', ' ', text)
        # Remove .com, URLs, etc.
        text = re.sub(r'\.com|\w+@\w+', '', text, flags=re.IGNORECASE)
        return text.strip()
    
    def _extract_title(self, normalized: str, original: str) -> str:
        """Extract title from torrent name."""
        # Remove leading/trailing special characters
        text = normalized.strip()
        
        # Try to find title before year or episode info
        # Look for patterns: "Title Year" or "Title SxxExx"
        
        # Remove episode info temporarily
        text_no_episode = re.sub(r'\s*S\d{1,2}E\d{1,2}.*$', '', text, flags=re.IGNORECASE)
        
        # Remove technical specs at the end
        title = re.sub(r'\s+(WEB|1080|720|2160|480|H\.?26[45]|BluRay|HDTV|AAC|DDP|MULTI)\b.*$', '', 
                      text_no_episode, flags=re.IGNORECASE).strip()
        
        # If too short, try original
        if len(title) < 3:
            title = original.split('.')[0].strip()
        
        return title[:100]  # Limit title length
    
    def _extract_year(self, text: str) -> Optional[int]:
        """Extract year from torrent name."""
        match = self.YEAR_PATTERN.search(text)
        if match:
            try:
                year = int(match.group(1))
                if 1900 <= year <= 2100:
                    return year
            except (ValueError, IndexError):
                pass
        return None
    
    def _extract_episode(self, text: str) -> Tuple[Optional[int], Optional[int]]:
        """Extract season and episode numbers."""
        match = self.EPISODE_PATTERN.search(text)
        if match:
            try:
                season = int(match.group(1))
                episode = int(match.group(2))
                return season, episode
            except (ValueError, IndexError):
                pass
        return None, None
    
    def _extract_first_match(self, text: str, pattern: re.Pattern) -> Optional[str]:
        """Extract first match from pattern."""
        match = pattern.search(text)
        if match:
            return match.group(0)
        return None
    
    def _extract_languages(self, text: str) -> List[str]:
        """Extract languages from torrent name."""
        languages = []
        for lang, pattern in self.LANGUAGE_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                languages.append(lang)
        return languages
    
    def _extract_publisher(self, text: str) -> Optional[str]:
        """Extract publisher/release group."""
        match = self.PUBLISHER_PATTERN.search(text)
        if match:
            return match.group(1)
        return None
