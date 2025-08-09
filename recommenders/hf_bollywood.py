"""Bollywood song recommendation using Hugging Face models."""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
import logging

# Global availability flags
SENTENCE_TRANSFORMERS_AVAILABLE = False
FAISS_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer, CrossEncoder
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    logging.warning("sentence-transformers not available. Song recommendations will be disabled.")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    logging.warning("faiss not available. Will use numpy-based search instead.")


class BollywoodSongRecommender:
    """Recommends Bollywood songs using Hugging Face models and vector search."""
    
    def __init__(
        self,
        catalog_df: pd.DataFrame,
        emb_matrix: Optional[np.ndarray] = None,
        faiss_index: Optional[Any] = None,
        embed_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        cross_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    ):
        """Initialize the recommender.
        
        Args:
            catalog_df: DataFrame with song catalog
            emb_matrix: Pre-computed embeddings matrix
            faiss_index: Optional FAISS index for faster search
            embed_model: Hugging Face model for embeddings
            cross_model: Hugging Face model for cross-encoder reranking
        """
        self.df = catalog_df.reset_index(drop=True)
        self.emb = emb_matrix.astype("float32") if emb_matrix is not None else None
        self.faiss = faiss_index
        self.st = None
        self.ce = None
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.st = SentenceTransformer(embed_model)
                self.ce = CrossEncoder(cross_model)
                logging.info(f"Initialized models: {embed_model}, {cross_model}")
            except Exception as e:
                logging.error(f"Failed to load models: {e}")
                self.st = None
                self.ce = None
        
        if self.st is None:
            logging.warning("Sentence transformers not available. Using fallback search.")
    
    def _encode(self, text: str) -> Optional[np.ndarray]:
        """Encode text to vector using sentence transformer."""
        if self.st is None:
            return None
        
        try:
            v = self.st.encode([text], normalize_embeddings=True)
            return v[0].astype("float32")
        except Exception as e:
            logging.error(f"Encoding failed: {e}")
            return None
    
    def search_candidates(self, qv: np.ndarray, top_k: int = 30) -> List[Dict]:
        """Search for candidate songs using vector similarity."""
        if self.emb is None:
            logging.warning("No embeddings available for search")
            return []
        
        try:
            if self.faiss is not None and FAISS_AVAILABLE:
                D, I = self.faiss.search(qv.reshape(1, -1), top_k)
                idxs = I[0].tolist()
            else:
                # Fallback to numpy-based search
                sims = self.emb @ qv
                idxs = np.argsort(-sims)[:top_k].tolist()
            
            return [self.df.iloc[i].to_dict() for i in idxs]
        except Exception as e:
            logging.error(f"Search failed: {e}")
            return []
    
    def filter_candidates(
        self,
        candidates: List[Dict],
        preferences: Dict[str, Any]
    ) -> List[Dict]:
        """Filter candidates based on preferences and constraints."""
        def is_acceptable(candidate: Dict) -> bool:
            # Check explicit content
            if candidate.get("is_explicit", False):
                return False
            
            # Check blacklist terms
            title_lower = candidate.get("title", "").lower()
            blacklist = preferences.get("blacklist", [])
            if any(bad.lower() in title_lower for bad in blacklist):
                return False
            
            # Check duration (2-7 minutes)
            duration = candidate.get("duration_sec", 0)
            if not (120 <= duration <= 420):
                return False
            
            # Check URL availability
            if not candidate.get("url"):
                return False
            
            return True
        
        # Filter acceptable candidates
        filtered = [c for c in candidates if is_acceptable(c)]
        
        # Sort by language priority and views
        lang_order = {
            lang: i for i, lang in enumerate(preferences.get("language_priority", ["Hindi"]))
        }
        
        def sort_key(candidate: Dict) -> tuple:
            lang = candidate.get("language", "")
            views = candidate.get("views", 0) or 0
            return (lang_order.get(lang, 999), -views)
        
        filtered.sort(key=sort_key)
        return filtered
    
    def rerank_with_cross_encoder(
        self,
        query_text: str,
        candidates: List[Dict],
        top_k: int = 10
    ) -> List[Dict]:
        """Rerank candidates using cross-encoder for better relevance."""
        if self.ce is None or not candidates:
            return candidates[:top_k]
        
        try:
            subset = candidates[:top_k]
            pairs = [
                (query_text, f'{c["title"]} {c.get("artist", "")} {c.get("moods", "")}')
                for c in subset
            ]
            scores = self.ce.predict(pairs).tolist()
            order = np.argsort(-np.array(scores)).tolist()
            return [subset[i] for i in order]
        except Exception as e:
            logging.error(f"Cross-encoder reranking failed: {e}")
            return candidates[:top_k]
    
    def pick_one(
        self,
        candidates: List[Dict],
        recent_ids: Set[str]
    ) -> Optional[Dict]:
        """Pick one song avoiding recent selections."""
        for candidate in candidates:
            if candidate["song_id"] not in recent_ids:
                return {
                    "song_id": candidate["song_id"],
                    "title": candidate["title"],
                    "url": candidate["url"]
                }
        return None
    
    def recommend_song(
        self,
        query_text: str,
        preferences: Dict[str, Any],
        recent_ids: Set[str],
        top_k: int = 30
    ) -> Optional[Dict]:
        """Main recommendation method."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE or self.st is None:
            logging.warning("Models not available for song recommendation")
            return None
        
        # Encode query
        query_vector = self._encode(query_text)
        if query_vector is None:
            logging.error("Failed to encode query")
            return None
        
        # Search candidates
        candidates = self.search_candidates(query_vector, top_k)
        if not candidates:
            logging.error("No candidates found")
            return None
        
        # Filter candidates
        filtered = self.filter_candidates(candidates, preferences)
        if not filtered:
            logging.error("No candidates after filtering")
            return None
        
        # Rerank with cross-encoder
        reranked = self.rerank_with_cross_encoder(query_text, filtered)
        if not reranked:
            logging.error("No candidates after reranking")
            return None
        
        # Pick one avoiding recent selections
        try:
            return self.pick_one(reranked, recent_ids)
        except Exception as e:
            logging.error(f"Error in pick_one: {e}")
            logging.error(f"reranked type: {type(reranked)}, recent_ids type: {type(recent_ids)}")
            return None


def load_song_catalog(catalog_path: str) -> pd.DataFrame:
    """Load song catalog from CSV file."""
    try:
        df = pd.read_csv(catalog_path)
        logging.info(f"Loaded {len(df)} songs from {catalog_path}")
        return df
    except Exception as e:
        logging.error(f"Failed to load catalog: {e}")
        return pd.DataFrame()


def load_embeddings(embeddings_path: str) -> Optional[np.ndarray]:
    """Load pre-computed embeddings."""
    try:
        emb = np.load(embeddings_path)
        logging.info(f"Loaded embeddings with shape {emb.shape}")
        return emb
    except Exception as e:
        logging.error(f"Failed to load embeddings: {e}")
        return None


def load_faiss_index(index_path: str) -> Optional[Any]:
    """Load FAISS index if available."""
    if not FAISS_AVAILABLE:
        return None
    
    try:
        index = faiss.read_index(index_path)
        logging.info(f"Loaded FAISS index from {index_path}")
        return index
    except Exception as e:
        logging.error(f"Failed to load FAISS index: {e}")
        return None


def create_recommender(
    catalog_path: str,
    embeddings_path: Optional[str] = None,
    faiss_index_path: Optional[str] = None,
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    cross_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
) -> Optional[BollywoodSongRecommender]:
    """Create a recommender instance with all components."""
    # Load catalog
    catalog_df = load_song_catalog(catalog_path)
    if catalog_df.empty:
        return None
    
    # Load embeddings
    emb_matrix = None
    if embeddings_path:
        emb_matrix = load_embeddings(embeddings_path)
    
    # Load FAISS index
    faiss_index = None
    if faiss_index_path:
        faiss_index = load_faiss_index(faiss_index_path)
    
    # Create recommender
    return BollywoodSongRecommender(
        catalog_df=catalog_df,
        emb_matrix=emb_matrix,
        faiss_index=faiss_index,
        embed_model=embed_model,
        cross_model=cross_model
    )
