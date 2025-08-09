#!/usr/bin/env python3
"""Generate embeddings for Bollywood song catalog."""

import argparse
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_embeddings(
    catalog_path: str,
    embeddings_path: str,
    faiss_index_path: str = None,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
):
    """Generate embeddings for the song catalog."""
    
    # Load catalog
    logger.info(f"Loading catalog from {catalog_path}")
    df = pd.read_csv(catalog_path)
    logger.info(f"Loaded {len(df)} songs")
    
    # Initialize model
    logger.info(f"Loading model: {model_name}")
    model = SentenceTransformer(model_name)
    
    # Create text representations for each song
    texts = []
    for _, row in df.iterrows():
        # Combine title, artist, moods, and themes
        text_parts = [
            str(row.get('title', '')),
            str(row.get('artist', '')),
            str(row.get('moods', '')),
            str(row.get('themes', ''))
        ]
        text = ' '.join(text_parts)
        texts.append(text)
    
    # Generate embeddings
    logger.info("Generating embeddings...")
    embeddings = model.encode(texts, normalize_embeddings=True)
    
    # Save embeddings
    logger.info(f"Saving embeddings to {embeddings_path}")
    np.save(embeddings_path, embeddings)
    
    # Create FAISS index if requested
    if faiss_index_path:
        logger.info(f"Creating FAISS index...")
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        index.add(embeddings.astype('float32'))
        
        logger.info(f"Saving FAISS index to {faiss_index_path}")
        faiss.write_index(index, faiss_index_path)
    
    logger.info("Embedding generation completed!")
    logger.info(f"Embeddings shape: {embeddings.shape}")
    if faiss_index_path:
        logger.info(f"FAISS index size: {index.ntotal}")


def main():
    parser = argparse.ArgumentParser(description="Generate embeddings for Bollywood song catalog")
    parser.add_argument("--catalog", default="data/bollywood_songs.csv", help="Path to song catalog CSV")
    parser.add_argument("--embeddings", default="data/bollywood_songs_embeddings.npy", help="Path to save embeddings")
    parser.add_argument("--faiss-index", default="data/bollywood_songs.index", help="Path to save FAISS index")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2", help="Hugging Face model name")
    parser.add_argument("--no-faiss", action="store_true", help="Skip FAISS index creation")
    
    args = parser.parse_args()
    
    # Create output directories
    Path(args.embeddings).parent.mkdir(parents=True, exist_ok=True)
    if not args.no_faiss:
        Path(args.faiss_index).parent.mkdir(parents=True, exist_ok=True)
    
    # Generate embeddings
    generate_embeddings(
        catalog_path=args.catalog,
        embeddings_path=args.embeddings,
        faiss_index_path=None if args.no_faiss else args.faiss_index,
        model_name=args.model
    )


if __name__ == "__main__":
    main()
