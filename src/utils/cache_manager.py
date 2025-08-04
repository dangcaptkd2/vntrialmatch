"""
Cache manager for keyword extraction and enrichment steps.

This module provides caching functionality to store and retrieve
keyword extraction and enrichment results to avoid redundant processing.
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching for keyword extraction and enrichment results."""

    def __init__(self, cache_dir: str = "cache", max_age_days: int = 30):
        """
        Initialize the cache manager.

        Args:
            cache_dir: Directory to store cache files
            max_age_days: Maximum age of cache entries in days
        """
        self.cache_dir = Path(cache_dir)
        self.max_age_days = max_age_days
        self.cache_file = self.cache_dir / "keyword_cache.json"
        self.logger = logging.getLogger(__name__)

        # Ensure cache directory exists
        self.cache_dir.mkdir(exist_ok=True)

        # Load existing cache
        self.cache_data = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """Load cache data from JSON file."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                self.logger.info(f"Loaded cache with {len(cache_data)} entries")
                return cache_data
            else:
                self.logger.info("No existing cache found, creating new cache")
                return {}
        except Exception as e:
            self.logger.error(f"Error loading cache: {e}")
            return {}

    def _save_cache(self):
        """Save cache data to JSON file."""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved cache with {len(self.cache_data)} entries")
        except Exception as e:
            self.logger.error(f"Error saving cache: {e}")

    def _generate_key(self, patient_profile: str) -> str:
        """
        Generate a unique key for the patient profile.

        Args:
            patient_profile: Patient profile text

        Returns:
            Unique hash key for the profile
        """
        # Normalize the profile (remove extra whitespace, convert to lowercase)
        normalized_profile = " ".join(patient_profile.strip().lower().split())

        # Generate SHA-256 hash
        hash_object = hashlib.sha256(normalized_profile.encode("utf-8"))
        return hash_object.hexdigest()

    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """
        Check if a cache entry is still valid (not expired).

        Args:
            cache_entry: Cache entry dictionary

        Returns:
            True if cache entry is valid, False otherwise
        """
        if "timestamp" not in cache_entry:
            return False

        try:
            timestamp = datetime.fromisoformat(cache_entry["timestamp"])
            max_age = timedelta(days=self.max_age_days)
            return datetime.now() - timestamp < max_age
        except Exception:
            return False

    def get_cached_result(
        self, patient_profile: str, cache_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached result for a patient profile.

        Args:
            patient_profile: Patient profile text
            cache_type: Type of cache ("extraction" or "enrichment")

        Returns:
            Cached result if available and valid, None otherwise
        """
        key = self._generate_key(patient_profile)
        cache_key = f"{key}_{cache_type}"

        if cache_key in self.cache_data:
            cache_entry = self.cache_data[cache_key]

            if self._is_cache_valid(cache_entry):
                self.logger.info(f"Cache hit for {cache_type}: {key[:8]}...")
                return cache_entry.get("result")
            else:
                # Remove expired entry
                del self.cache_data[cache_key]
                self._save_cache()
                self.logger.info(f"Removed expired cache entry for {cache_type}")

        return None

    def set_cached_result(
        self, patient_profile: str, cache_type: str, result: Dict[str, Any]
    ):
        """
        Store result in cache.

        Args:
            patient_profile: Patient profile text
            cache_type: Type of cache ("extraction" or "enrichment")
            result: Result to cache
        """
        key = self._generate_key(patient_profile)
        cache_key = f"{key}_{cache_type}"

        cache_entry = {
            "timestamp": datetime.now().isoformat(),
            "key": key,
            "cache_type": cache_type,
            "result": result,
        }

        self.cache_data[cache_key] = cache_entry
        self._save_cache()
        self.logger.info(f"Cached {cache_type} result for key: {key[:8]}...")

    def clear_cache(self, cache_type: Optional[str] = None):
        """
        Clear cache entries.

        Args:
            cache_type: Specific cache type to clear ("extraction", "enrichment", or None for all)
        """
        if cache_type is None:
            # Clear all cache
            self.cache_data.clear()
            self.logger.info("Cleared all cache entries")
        else:
            # Clear specific cache type
            keys_to_remove = [
                key for key in self.cache_data.keys() if key.endswith(f"_{cache_type}")
            ]
            for key in keys_to_remove:
                del self.cache_data[key]
            self.logger.info(
                f"Cleared {len(keys_to_remove)} {cache_type} cache entries"
            )

        self._save_cache()

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_entries = len(self.cache_data)
        valid_entries = sum(
            1 for entry in self.cache_data.values() if self._is_cache_valid(entry)
        )
        expired_entries = total_entries - valid_entries

        extraction_entries = sum(
            1 for key in self.cache_data.keys() if key.endswith("_extraction")
        )
        enrichment_entries = sum(
            1 for key in self.cache_data.keys() if key.endswith("_enrichment")
        )

        return {
            "total_entries": total_entries,
            "valid_entries": valid_entries,
            "expired_entries": expired_entries,
            "extraction_entries": extraction_entries,
            "enrichment_entries": enrichment_entries,
            "cache_file_size": (
                self.cache_file.stat().st_size if self.cache_file.exists() else 0
            ),
        }

    def cleanup_expired_entries(self):
        """Remove expired cache entries."""
        keys_to_remove = []

        for key, entry in self.cache_data.items():
            if not self._is_cache_valid(entry):
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.cache_data[key]

        if keys_to_remove:
            self._save_cache()
            self.logger.info(f"Cleaned up {len(keys_to_remove)} expired cache entries")

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get detailed cache information.

        Returns:
            Dictionary with detailed cache information
        """
        stats = self.get_cache_stats()

        # Get oldest and newest timestamps
        timestamps = []
        for entry in self.cache_data.values():
            if "timestamp" in entry:
                try:
                    timestamps.append(datetime.fromisoformat(entry["timestamp"]))
                except Exception:
                    pass

        if timestamps:
            oldest = min(timestamps)
            newest = max(timestamps)
        else:
            oldest = newest = None

        return {
            **stats,
            "oldest_entry": oldest.isoformat() if oldest else None,
            "newest_entry": newest.isoformat() if newest else None,
            "cache_directory": str(self.cache_dir),
            "cache_file": str(self.cache_file),
        }


# Global cache manager instance
cache_manager = CacheManager()
