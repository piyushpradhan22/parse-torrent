"""Data models and schemas for torrent parsing."""

from typing import Optional
from pydantic import BaseModel


class TorrentQuery(BaseModel):
    """Request schema for torrent query."""
    torrent_name: Optional[str] = None
    torrent_file: Optional[str] = None


class EpisodeInfo(BaseModel):
    """Episode information for series."""
    season: Optional[int] = None
    episode: Optional[int] = None
    episode_title: Optional[str] = None


class MetadataExtraction(BaseModel):
    """Extracted metadata from torrent."""
    title: Optional[str] = None
    year: Optional[int] = None
    resolution: Optional[str] = None  # 1080p, 720p, 2160p, etc.
    quality: Optional[str] = None  # WEB-DL, BluRay, HDTV, etc.
    audio_codec: Optional[str] = None  # AAC, DDP, TrueHD, etc.
    audio_channels: Optional[str] = None  # 5.1, 7.1, 2.0, etc.
    video_codec: Optional[str] = None  # H.264, H.265, VP9, etc.
    hdr: Optional[bool] = None  # HDR, DV, etc.
    publisher: Optional[str] = None
    language: Optional[list[str]] = None


class TorrentParsedInfo(BaseModel):
    """Complete parsed torrent information."""
    original_name: str
    is_series: bool
    title_type: Optional[str] = None        # IMDb title type: movie, tvSeries, tvMovie, tvSpecial
    title: Optional[str] = None
    year: Optional[int] = None
    episode: Optional[EpisodeInfo] = None
    metadata: Optional[MetadataExtraction] = None
    imdb_id: Optional[str] = None
    confidence: Optional[float] = None


class TorrentResponse(BaseModel):
    """API response for torrent parsing."""
    status: str
    data: Optional[TorrentParsedInfo] = None
    error: Optional[str] = None
