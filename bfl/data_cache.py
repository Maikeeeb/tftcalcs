"""Caching module for parsed data files."""

from __future__ import annotations

import hashlib
import os
import threading
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable, Dict, Hashable, Tuple, TypeVar

T = TypeVar("T")


class DataCache:
    """Thread-safe cache for parsed data files with file modification time tracking.

    Automatically invalidates cache entries when source files are modified.
    """

    def __init__(self, max_size: int | None = None):
        """Initialize the cache.

        Parameters
        ----------
        max_size : int | None
            Maximum number of cache entries. If None, unlimited (default: None).
        """
        self._cache: OrderedDict[Hashable, Tuple[Any, float]] = OrderedDict()
        self._lock = threading.Lock()
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    def get(
        self,
        key: Hashable,
        loader: Callable[[], T],
        file_paths: list[Path] | None = None,
    ) -> T:
        """Get cached value or load it using the loader function.

        Parameters
        ----------
        key : Hashable
            Cache key (typically a tuple of function arguments).
        loader : Callable[[], T]
            Function to load the data if not cached or cache is invalid.
        file_paths : list[Path] | None
            List of file paths to check modification times. If any file has been
            modified since caching, the cache is invalidated.

        Returns
        -------
        T
            Cached or freshly loaded data.
        """
        with self._lock:
            # Check if we have a cached value
            if key in self._cache:
                cached_value, cached_mtime = self._cache[key]

                # Check file modification times if provided
                if file_paths:
                    current_mtimes = []
                    for file_path in file_paths:
                        try:
                            current_mtimes.append(os.path.getmtime(file_path))
                        except OSError:
                            # File doesn't exist or can't be accessed - invalidate cache
                            del self._cache[key]
                            self._misses += 1
                            return loader()

                    # If any file has been modified, invalidate cache
                    if any(mtime > cached_mtime for mtime in current_mtimes):
                        del self._cache[key]
                        self._misses += 1
                        value = loader()
                        max_mtime = max(current_mtimes) if current_mtimes else 0.0
                        self._set(key, value, max_mtime)
                        return value

                # Cache hit - move to end (LRU)
                self._cache.move_to_end(key)
                self._hits += 1
                return cached_value

            # Cache miss
            self._misses += 1
            value = loader()

            # Determine mtime for caching
            if file_paths:
                mtimes = []
                for file_path in file_paths:
                    try:
                        mtimes.append(os.path.getmtime(file_path))
                    except OSError:
                        mtimes.append(0.0)
                mtime = max(mtimes) if mtimes else 0.0
            else:
                mtime = 0.0

            self._set(key, value, mtime)
            return value

    def _set(self, key: Hashable, value: Any, mtime: float):
        """Set a cache entry, respecting max_size."""
        self._cache[key] = (value, mtime)
        self._cache.move_to_end(key)

        # Evict oldest entry if over max_size
        if self._max_size and len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def get_stats(self) -> Dict[str, int | float]:
        """Get cache statistics.

        Returns
        -------
        Dict[str, int | float]
            Dictionary with hits, misses, size, and hit_rate.
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0.0
            return {
                "hits": self._hits,
                "misses": self._misses,
                "size": len(self._cache),
                "hit_rate": hit_rate,
            }


# Global cache instance
_cache = DataCache(max_size=10)


def _make_cache_key(file_path: Path, set_id: str, blacklist_traits: set[str] | None) -> Hashable:
    """Create a cache key for set data loading."""
    blacklist_hash = (
        hashlib.md5(str(sorted(blacklist_traits)).encode()).hexdigest() if blacklist_traits else ""
    )
    return (str(file_path.resolve()), set_id, blacklist_hash)


def cached_load_set_data(
    path: str | Path,
    set_id: str,
    blacklist_traits: set[str] | None = None,
):
    """Cached version of load_set_data.

    This function wraps the original load_set_data with caching. The cache
    automatically invalidates when the source file is modified.

    Parameters
    ----------
    path : str | Path
        Path to the Riot set data JSON file.
    set_id : str
        Set identifier within the JSON file.
    blacklist_traits : set[str] | None
        Traits to exclude from eligibility.

    Returns
    -------
    Tuple
        Same return value as load_set_data.
    """
    from bfl.set_loader import load_set_data

    file_path = Path(path)
    cache_key = _make_cache_key(file_path, set_id, blacklist_traits)

    def loader():
        return load_set_data(path, set_id, blacklist_traits)

    return _cache.get(cache_key, loader, file_paths=[file_path])


def cached_load_metatft_txt(path: str) -> str:
    """Cached version of load_metatft_txt.

    This function wraps the original load_metatft_txt with caching. The cache
    automatically invalidates when the source file is modified.

    Parameters
    ----------
    path : str
        Path to the MetaTFT paste file.

    Returns
    -------
    str
        File contents as a string. Returns empty string if file not found.
    """
    from bfl.metatft import load_metatft_txt

    file_path = Path(path)
    cache_key = str(file_path.resolve())

    def loader():
        return load_metatft_txt(path)

    # Only cache if file exists (load_metatft_txt returns "" for missing files)
    if file_path.exists():
        return _cache.get(cache_key, loader, file_paths=[file_path])
    else:
        return load_metatft_txt(path)
