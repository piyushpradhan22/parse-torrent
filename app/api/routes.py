"""API routes for torrent parsing."""

import os
import re
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.schemas import TorrentQuery, TorrentResponse, TorrentParsedInfo, EpisodeInfo
from app.core.torrent_parser import TorrentParser
import logging
from app import main

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["torrent"])

torrent_parser = TorrentParser()


def _resolve_torrent_text(query: TorrentQuery) -> str:
    """Resolve input text from torrent_name or torrent_file path."""
    if query.torrent_name:
        return query.torrent_name

    if query.torrent_file:
        # Normalize file paths so parsing uses only the release name.
        normalized = query.torrent_file.replace('\\', '/')
        return os.path.basename(normalized)

    return ""


def _resolve_file_text(query: TorrentQuery) -> str:
    """Resolve normalized basename from torrent_file path."""
    if not query.torrent_file:
        return ""
    normalized = query.torrent_file.replace('\\', '/')
    return os.path.basename(normalized)


def _clean_imdb_search_title(title: str) -> str:
    """Normalize noisy release strings into a cleaner IMDb search title."""
    if not title:
        return ""

    t = title
    t = re.sub(r"\[[^\]]*\]|\([^\)]*\)", " ", t)
    t = re.sub(r"\bS\d{1,2}E\d{1,2}\b", " ", t, flags=re.IGNORECASE)
    t = re.sub(r"\bS\d{1,2}\b", " ", t, flags=re.IGNORECASE)
    t = re.sub(r"\bSeason\s*\d{1,2}\b", " ", t, flags=re.IGNORECASE)

    # Strip common non-title terms found in torrent names.
    t = re.sub(
        r"\b(Dual\s*Audio|Multi|MULTi|Hindi|English|NF|WEB-?DL|WEBRip|HDRip|BluRay|HDTV|x264|H\.?(?:264|265)|HEVC|AAC|DDP|DD|MSubs|SDR|HDR|Dolby\s*Vision)\b",
        " ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"\b\d{3,4}p\b", " ", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+", " ", t).strip(" -._")
    return t


def _derive_title_from_episode_filename(file_text: str) -> str:
    """Extract probable series title from filenames like 'Name - S01E08.ext'."""
    if not file_text:
        return ""

    base = re.sub(r"\.[A-Za-z0-9]{2,5}$", "", file_text)
    m = re.match(r"^(.*?)\s*[-._ ]\s*S\d{1,2}E\d{1,2}\b", base, flags=re.IGNORECASE)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip(" -._")
    return ""


@router.post("/parse", response_model=TorrentResponse)
async def parse_torrent(query: TorrentQuery) -> TorrentResponse:
    """
    Parse a torrent name and extract metadata.
    
    Args:
        query: TorrentQuery with torrent_name or torrent_file
        
    Returns:
        TorrentResponse with parsed information and IMDB ID
    """
    
    # Primary extraction source is torrent_name.
    torrent_name = _resolve_torrent_text(query)
    torrent_file = _resolve_file_text(query)
    
    if not torrent_name:
        raise HTTPException(status_code=400, detail="Either torrent_name or torrent_file required")
    
    try:
        # Parse primary text for title/year/technical metadata.
        parsed = torrent_parser.parse(torrent_name)

        # Parse file text only to enrich season/episode for series-like inputs.
        parsed_file = torrent_parser.parse(torrent_file) if torrent_file else None
        file_has_episode = bool(parsed_file and (parsed_file.season or parsed_file.episode))
        allow_file_episode = file_has_episode

        resolved_is_series = parsed.is_series or (allow_file_episode and file_has_episode)
        resolved_season = parsed_file.season if (allow_file_episode and file_has_episode) else parsed.season
        resolved_episode = parsed_file.episode if (allow_file_episode and file_has_episode) else parsed.episode
        
        # Extract metadata
        metadata_data = {
            "title": parsed.title,
            "year": parsed.year,
            "resolution": parsed.resolution,
            "quality": parsed.quality,
            "audio_codec": parsed.audio_codec,
            "audio_channels": parsed.audio_channels,
            "video_codec": parsed.video_codec,
            "hdr": parsed.hdr,
            "publisher": parsed.publisher,
            "language": parsed.language,
        }
        
        # Step 1: broad IMDb search without is_series filter to get the match.
        imdb_id = None
        confidence = None
        imdb_title_type = None
        imdb_is_series = resolved_is_series  # default from name/file heuristic

        if main.indexer:
            imdb_title_query = _clean_imdb_search_title(parsed.title)
            file_title_hint = _derive_title_from_episode_filename(torrent_file)
            if file_title_hint:
                imdb_title_query = file_title_hint

            results = main.indexer.search(
                title=imdb_title_query or parsed.title,
                year=parsed.year,
                is_series=None,   # let IMDb decide the type
                threshold=0.7,
            )
            if results:
                best_match = results[0]
                imdb_id = best_match['imdb_id']
                confidence = best_match['score']
                imdb_title_type = best_match.get('title_type')      # movie/tvSeries/tvMovie/tvSpecial
                imdb_is_series = best_match.get('is_series', resolved_is_series)

        # Step 2: IMDb type is now authoritative for movie vs series.
        resolved_is_series = imdb_is_series

        # Step 3: episode enrichment from file only makes sense for series.
        if not resolved_is_series:
            resolved_season = parsed.season
            resolved_episode = parsed.episode

        # Build episode info if series
        episode_info = None
        if resolved_is_series and (resolved_season or resolved_episode):
            episode_info = EpisodeInfo(
                season=resolved_season,
                episode=resolved_episode,
                episode_title=parsed.episode_title,
            )

        # Build response
        result = TorrentParsedInfo(
            original_name=torrent_name,
            is_series=resolved_is_series,
            title_type=imdb_title_type,
            title=parsed.title,
            year=parsed.year,
            episode=episode_info,
            metadata=metadata_data,
            imdb_id=imdb_id,
            confidence=confidence,
        )
        
        return TorrentResponse(status="success", data=result)
    
    except Exception as e:
        logger.error(f"Error parsing torrent: {e}", exc_info=True)
        return TorrentResponse(
            status="error",
            error=f"Parsing error: {str(e)}"
        )


@router.post("/parse-with-ai", response_model=TorrentResponse)
async def parse_torrent_with_ai(query: TorrentQuery) -> TorrentResponse:
    """
    Parse torrent with AI-enhanced metadata extraction.
    
    Uses NVIDIA API for intelligent metadata extraction.
    """
    
    torrent_name = _resolve_torrent_text(query)
    torrent_file = _resolve_file_text(query)
    
    if not torrent_name:
        raise HTTPException(status_code=400, detail="Either torrent_name or torrent_file required")
    
    try:
        # Parse primary text for title/year/technical metadata.
        parsed = torrent_parser.parse(torrent_name)

        # Parse file text only to enrich season/episode for series-like inputs.
        parsed_file = torrent_parser.parse(torrent_file) if torrent_file else None
        file_has_episode = bool(parsed_file and (parsed_file.season or parsed_file.episode))
        allow_file_episode = file_has_episode

        resolved_is_series = parsed.is_series or (allow_file_episode and file_has_episode)
        resolved_season = parsed_file.season if (allow_file_episode and file_has_episode) else parsed.season
        resolved_episode = parsed_file.episode if (allow_file_episode and file_has_episode) else parsed.episode
        
        # Extract with AI
        ai_metadata = await main.extractor.extract_metadata(torrent_name)
        
        # Merge with parsed metadata
        metadata_data = {
            "title": ai_metadata.get("title") or parsed.title,
            "year": ai_metadata.get("year") or parsed.year,
            "resolution": ai_metadata.get("resolution") or parsed.resolution,
            "quality": ai_metadata.get("quality") or parsed.quality,
            "audio_codec": ai_metadata.get("audio_codec") or parsed.audio_codec,
            "audio_channels": ai_metadata.get("audio_channels") or parsed.audio_channels,
            "video_codec": ai_metadata.get("video_codec") or parsed.video_codec,
            "hdr": ai_metadata.get("hdr", parsed.hdr),
            "publisher": parsed.publisher,
            "language": ai_metadata.get("language", parsed.language),
        }
        
        # Step 1: broad IMDb search without is_series filter.
        imdb_id = None
        confidence = None
        imdb_title_type = None
        imdb_is_series = resolved_is_series

        if main.indexer:
            search_title = metadata_data.get('title') or parsed.title
            search_title = _clean_imdb_search_title(search_title)
            file_title_hint = _derive_title_from_episode_filename(torrent_file)
            if file_title_hint:
                search_title = file_title_hint
            search_year = metadata_data.get('year') or parsed.year

            results = main.indexer.search(
                title=search_title,
                year=search_year,
                is_series=None,   # let IMDb decide the type
                threshold=0.65,
            )
            if results:
                best_match = results[0]
                imdb_id = best_match['imdb_id']
                confidence = best_match['score']
                imdb_title_type = best_match.get('title_type')
                imdb_is_series = best_match.get('is_series', resolved_is_series)

        # Step 2: IMDb type is now authoritative.
        resolved_is_series = imdb_is_series

        # Step 3: episode enrichment from file only for confirmed series.
        if not resolved_is_series:
            resolved_season = parsed.season
            resolved_episode = parsed.episode

        # Build episode info
        episode_info = None
        if resolved_is_series and (resolved_season or resolved_episode):
            episode_info = EpisodeInfo(
                season=resolved_season,
                episode=resolved_episode,
            )

        result = TorrentParsedInfo(
            original_name=torrent_name,
            is_series=resolved_is_series,
            title_type=imdb_title_type,
            title=metadata_data.get('title'),
            year=metadata_data.get('year'),
            episode=episode_info,
            metadata=metadata_data,
            imdb_id=imdb_id,
            confidence=confidence,
        )
        
        return TorrentResponse(status="success", data=result)
    
    except Exception as e:
        logger.error(f"Error parsing torrent with AI: {e}", exc_info=True)
        return TorrentResponse(
            status="error",
            error=f"AI Parsing error: {str(e)}"
        )


@router.get("/search-imdb")
async def search_imdb(title: str, year: int = None, is_series: bool = None):
    """
    Search for titles in IMDB index.
    
    Args:
        title: Movie/Series title to search
        year: Optional year filter
        is_series: Optional series filter
        
    Returns:
        List of matching titles
    """
    
    if not main.indexer:
        raise HTTPException(status_code=503, detail="IMDB indexer not initialized")
    
    try:
        results = main.indexer.search(
            title=title,
            year=year,
            is_series=is_series,
            threshold=0.65
        )
        
        return {
            "status": "success",
            "query": {
                "title": title,
                "year": year,
                "is_series": is_series,
            },
            "results": results,
            "total": len(results),
        }
    
    except Exception as e:
        logger.error(f"Error searching IMDB: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }
