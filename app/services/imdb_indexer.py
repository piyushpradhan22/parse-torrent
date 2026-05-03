"""IMDB dataset indexer and search service."""

import json
import gzip
import os
from typing import Optional, List, Dict
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import pickle

# title.episode.tsv.gz columns:
# 0:tconst(episode) 1:parentTconst(series) 2:seasonNumber 3:episodeNumber


class IMDBIndexer:
    """Index and search IMDB titles locally."""
    
    def __init__(self, index_path: str):
        """
        Initialize the indexer.
        
        Args:
            index_path: Path to store/load the index
        """
        self.index_path = index_path
        self.titles_index = {}  # {imdb_id: title_info}
        self.title_lookup = {}  # {normalized_title: [imdb_ids]}
        self.year_index = {}  # {year: [imdb_ids]}
        self.episode_index = {}  # {episode_tconst: {parent_tconst, season, episode}}
        
        self._ensure_index_dir()
        self._load_or_create_index()
    
    def _ensure_index_dir(self):
        """Ensure index directory exists."""
        os.makedirs(self.index_path, exist_ok=True)
    
    def _load_or_create_index(self):
        """Load existing index or create empty one."""
        index_file = os.path.join(self.index_path, 'titles_index.pkl')
        lookup_file = os.path.join(self.index_path, 'title_lookup.pkl')
        episode_file = os.path.join(self.index_path, 'episode_index.pkl')

        if os.path.exists(index_file) and os.path.exists(lookup_file):
            try:
                with open(index_file, 'rb') as f:
                    self.titles_index = pickle.load(f)
                with open(lookup_file, 'rb') as f:
                    self.title_lookup = pickle.load(f)
            except Exception as e:
                print(f"Error loading index: {e}. Creating new index.")
                self.titles_index = {}
                self.title_lookup = {}

        if os.path.exists(episode_file):
            try:
                with open(episode_file, 'rb') as f:
                    self.episode_index = pickle.load(f)
            except Exception as e:
                print(f"Error loading episode index: {e}.")
                self.episode_index = {}
    
    def add_title(self, imdb_id: str, title: str, title_type: str, year: Optional[int] = None,
                  is_series: bool = False, episode_count: Optional[int] = None):
        """
        Add a title to the index.
        
        Args:
            imdb_id: IMDB ID
            title: Movie/Series title
            title_type: 'movie', 'series', 'short', etc.
            year: Release year
            is_series: Whether it's a series
            episode_count: Number of episodes (for series)
        """
        title_info = {
            'imdb_id': imdb_id,
            'title': title,
            'title_type': title_type,
            'year': year,
            'is_series': is_series,
            'episode_count': episode_count,
        }
        
        self.titles_index[imdb_id] = title_info
        
        # Add to lookup (normalized)
        normalized = self._normalize_title(title)
        if normalized not in self.title_lookup:
            self.title_lookup[normalized] = []
        self.title_lookup[normalized].append(imdb_id)
        
        # Add to year index
        if year:
            if year not in self.year_index:
                self.year_index[year] = []
            self.year_index[year].append(imdb_id)
    
    def search(self, title: str, year: Optional[int] = None, 
               is_series: Optional[bool] = None, threshold: float = 0.7) -> List[Dict]:
        """
        Search for titles in the index.
        
        Args:
            title: Title to search for
            year: Optional year filter
            is_series: Optional series filter
            threshold: Fuzzy match threshold (0-1)
            
        Returns:
            List of matching titles sorted by score
        """
        if not self.titles_index:
            return []
        
        # Normalize search title
        normalized_title = self._normalize_title(title)
        
        # Try exact match first
        if normalized_title in self.title_lookup:
            results = []
            for imdb_id in self.title_lookup[normalized_title]:
                title_info = self.titles_index[imdb_id]
                if self._matches_filters(title_info, year, is_series):
                    results.append({**title_info, 'score': 1.0})
            if results:
                return results
        
        # Fuzzy search
        results = []
        for imdb_id, title_info in self.titles_index.items():
            score = fuzz.token_set_ratio(title, title_info['title']) / 100.0
            
            if score >= threshold and self._matches_filters(title_info, year, is_series):
                results.append({**title_info, 'score': score})
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:10]  # Return top 10
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison."""
        return title.lower().strip()
    
    def _matches_filters(self, title_info: Dict, year: Optional[int], 
                        is_series: Optional[bool]) -> bool:
        """Check if title matches filters."""
        if year and title_info.get('year') != year:
            # Allow year ± 1 for flexibility
            if title_info.get('year') not in [year - 1, year, year + 1]:
                return False
        
        if is_series is not None and title_info.get('is_series') != is_series:
            return False
        
        return True
    
    def save_index(self):
        """Save index to disk."""
        index_file = os.path.join(self.index_path, 'titles_index.pkl')
        lookup_file = os.path.join(self.index_path, 'title_lookup.pkl')
        episode_file = os.path.join(self.index_path, 'episode_index.pkl')

        try:
            with open(index_file, 'wb') as f:
                pickle.dump(self.titles_index, f)
            with open(lookup_file, 'wb') as f:
                pickle.dump(self.title_lookup, f)
            if self.episode_index:
                with open(episode_file, 'wb') as f:
                    pickle.dump(self.episode_index, f)
        except Exception as e:
            print(f"Error saving index: {e}")
    
    def load_from_imdb_dataset(self, dataset_path: str):
        """
        Load titles from IMDB dataset files.
        
        Expected format: TSV files with title.basics.tsv
        
        Args:
            dataset_path: Path to IMDB dataset directory
        """
        basics_file = os.path.join(dataset_path, 'title.basics.tsv')
        basics_gz_file = f"{basics_file}.gz"

        open_fn = None
        source_file = None
        if os.path.exists(basics_file):
            source_file = basics_file
            open_fn = lambda p: open(p, 'rt', encoding='utf-8')
        elif os.path.exists(basics_gz_file):
            source_file = basics_gz_file
            open_fn = lambda p: gzip.open(p, 'rt', encoding='utf-8')
        else:
            print(f"Dataset file not found: {basics_file} or {basics_gz_file}")
            return

        print(f"Loading IMDB dataset from {source_file}...")
        
        try:
            with open_fn(source_file) as f:
                # Skip header
                next(f)
                
                count = 0
                for line in f:
                    parts = line.strip().split('\t')
                    # IMDb title.basics.tsv columns:
                    # 0:tconst 1:titleType 2:primaryTitle 3:originalTitle
                    # 4:isAdult 5:startYear 6:endYear 7:runtimeMinutes 8:genres
                    if len(parts) < 9:
                        continue
                    
                    imdb_id = parts[0]
                    title_type = parts[1]
                    primary_title = parts[2]
                    is_adult = parts[4] == '1'
                    year = int(parts[5]) if parts[5] != '\\N' else None
                    
                    # Skip adult content and certain types
                    if is_adult or title_type not in ['movie', 'tvSeries', 'tvSpecial', 'tvMovie']:
                        continue
                    
                    is_series = title_type in ['tvSeries', 'tvSpecial']
                    
                    self.add_title(
                        imdb_id=imdb_id,
                        title=primary_title,
                        title_type=title_type,
                        year=year,
                        is_series=is_series
                    )
                    
                    count += 1
                    if count % 100000 == 0:
                        print(f"Loaded {count} titles...")
            
            print(f"Total titles loaded: {count}")
            self.save_index()
            
        except Exception as e:
            print(f"Error loading dataset: {e}")
    
    def get_title_info(self, imdb_id: str) -> Optional[Dict]:
        """Get title info by IMDB ID."""
        return self.titles_index.get(imdb_id)

    def get_episode_info(self, episode_tconst: str) -> Optional[Dict]:
        """
        Look up episode-to-series mapping from title.episode dataset.

        Returns dict with parent_tconst, season, episode or None.
        """
        return self.episode_index.get(episode_tconst)

    def load_episode_dataset(self, dataset_path: str):
        """
        Load title.episode.tsv(.gz) to build episode → parent series index.

        Columns: tconst, parentTconst, seasonNumber, episodeNumber
        """
        ep_file = os.path.join(dataset_path, 'title.episode.tsv')
        ep_gz_file = f"{ep_file}.gz"

        open_fn = None
        source_file = None
        if os.path.exists(ep_file):
            source_file = ep_file
            open_fn = lambda p: open(p, 'rt', encoding='utf-8')
        elif os.path.exists(ep_gz_file):
            source_file = ep_gz_file
            open_fn = lambda p: gzip.open(p, 'rt', encoding='utf-8')
        else:
            print(f"Episode dataset not found at {ep_file} or {ep_gz_file}")
            return

        print(f"Loading episode dataset from {source_file}...")
        count = 0
        try:
            with open_fn(source_file) as f:
                next(f)  # skip header
                for line in f:
                    parts = line.strip().split('\t')
                    if len(parts) < 4:
                        continue
                    ep_tconst, parent_tconst = parts[0], parts[1]
                    season = int(parts[2]) if parts[2] != '\\N' else None
                    episode = int(parts[3]) if parts[3] != '\\N' else None
                    self.episode_index[ep_tconst] = {
                        'parent_tconst': parent_tconst,
                        'season': season,
                        'episode': episode,
                    }
                    count += 1
            print(f"Episode dataset loaded: {count} entries")
            self.save_index()
        except Exception as e:
            print(f"Error loading episode dataset: {e}")
    
    def get_title_count(self) -> int:
        """Get total number of titles in index."""
        return len(self.titles_index)
