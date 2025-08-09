"""Tests for Bollywood song recommendation system."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch

from recommenders.hf_bollywood import (
    BollywoodSongRecommender,
    load_song_catalog,
    create_recommender
)
from utils.types import MessageType, SongRecommendation


@pytest.fixture
def sample_catalog():
    """Create a sample song catalog for testing."""
    return pd.DataFrame({
        'song_id': ['B001', 'B002', 'B003'],
        'title': ['Tum Hi Ho', 'Pehla Nasha', 'Tere Sang Yaara'],
        'artist': ['Arijit Singh', 'Udit Narayan', 'Rahat Fateh Ali Khan'],
        'year': [2013, 1992, 2016],
        'language': ['Hindi', 'Hindi', 'Hindi'],
        'moods': ['romantic', 'romantic', 'romantic'],
        'themes': ['longing', 'first_love', 'devotion'],
        'url': ['https://example.com/1', 'https://example.com/2', 'https://example.com/3'],
        'duration_sec': [280, 320, 310],
        'views': [150000000, 45000000, 85000000],
        'is_explicit': [False, False, False]
    })


@pytest.fixture
def sample_embeddings():
    """Create sample embeddings for testing."""
    return np.random.rand(3, 384).astype('float32')  # 384 is typical for all-MiniLM-L6-v2


def test_load_song_catalog(tmp_path):
    """Test loading song catalog from CSV."""
    # Create a temporary CSV file
    catalog_data = {
        'song_id': ['B001'],
        'title': ['Test Song'],
        'artist': ['Test Artist'],
        'year': [2020],
        'language': ['Hindi'],
        'moods': ['romantic'],
        'themes': ['love'],
        'url': ['https://example.com'],
        'duration_sec': [300],
        'views': [1000000],
        'is_explicit': [False]
    }
    
    catalog_path = tmp_path / "test_catalog.csv"
    pd.DataFrame(catalog_data).to_csv(catalog_path, index=False)
    
    # Test loading
    df = load_song_catalog(str(catalog_path))
    assert len(df) == 1
    assert df.iloc[0]['title'] == 'Test Song'


@patch('recommenders.hf_bollywood.SENTENCE_TRANSFORMERS_AVAILABLE', False)
def test_recommender_without_sentence_transformers(sample_catalog):
    """Test recommender behavior when sentence-transformers is not available."""
    recommender = BollywoodSongRecommender(sample_catalog)
    assert recommender.st is None
    assert recommender.ce is None


@patch('recommenders.hf_bollywood.SENTENCE_TRANSFORMERS_AVAILABLE', True)
@patch('recommenders.hf_bollywood.SentenceTransformer')
@patch('recommenders.hf_bollywood.CrossEncoder')
def test_recommender_initialization(mock_cross_encoder, mock_sentence_transformer, sample_catalog, sample_embeddings):
    """Test recommender initialization."""
    # Mock the models
    mock_st = Mock()
    mock_st.encode.return_value = sample_embeddings
    mock_sentence_transformer.return_value = mock_st
    
    mock_ce = Mock()
    mock_cross_encoder.return_value = mock_ce
    
    recommender = BollywoodSongRecommender(
        catalog_df=sample_catalog,
        emb_matrix=sample_embeddings
    )
    
    assert recommender.df is not None
    assert recommender.emb is not None
    assert recommender.st is not None
    assert recommender.ce is not None


def test_filter_candidates(sample_catalog, sample_embeddings):
    """Test candidate filtering."""
    recommender = BollywoodSongRecommender(sample_catalog, sample_embeddings)
    
    candidates = [
        {'title': 'Good Song', 'is_explicit': False, 'duration_sec': 300, 'url': 'https://example.com', 'language': 'Hindi', 'views': 1000000},
        {'title': 'Bad Song', 'is_explicit': True, 'duration_sec': 300, 'url': 'https://example.com', 'language': 'Hindi', 'views': 1000000},
        {'title': 'Short Song', 'is_explicit': False, 'duration_sec': 60, 'url': 'https://example.com', 'language': 'Hindi', 'views': 1000000},
        {'title': 'No URL Song', 'is_explicit': False, 'duration_sec': 300, 'url': '', 'language': 'Hindi', 'views': 1000000}
    ]
    
    preferences = {
        'language_priority': ['Hindi'],
        'blacklist': ['bad'],
        'max_age_days': 36500
    }
    
    filtered = recommender.filter_candidates(candidates, preferences)
    
    # Should filter out explicit, short, and no-URL songs
    assert len(filtered) == 1
    assert filtered[0]['title'] == 'Good Song'


def test_pick_one(sample_catalog, sample_embeddings):
    """Test song selection avoiding recent picks."""
    recommender = BollywoodSongRecommender(sample_catalog, sample_embeddings)
    
    candidates = [
        {'song_id': 'B001', 'title': 'Song 1', 'url': 'https://example.com/1'},
        {'song_id': 'B002', 'title': 'Song 2', 'url': 'https://example.com/2'},
        {'song_id': 'B003', 'title': 'Song 3', 'url': 'https://example.com/3'}
    ]
    
    recent_ids = {'B001', 'B002'}
    
    result = recommender.pick_one(candidates, recent_ids)
    
    assert result is not None
    assert result['song_id'] == 'B003'
    assert result['title'] == 'Song 3'


@patch('recommenders.hf_bollywood.SENTENCE_TRANSFORMERS_AVAILABLE', True)
@patch('recommenders.hf_bollywood.SentenceTransformer')
@patch('recommenders.hf_bollywood.CrossEncoder')
def test_create_recommender(mock_cross_encoder, mock_sentence_transformer, tmp_path):
    """Test creating recommender with all components."""
    # Create temporary files
    catalog_path = tmp_path / "test_catalog.csv"
    embeddings_path = tmp_path / "test_embeddings.npy"
    
    # Create catalog
    catalog_data = {
        'song_id': ['B001'],
        'title': ['Test Song'],
        'artist': ['Test Artist'],
        'year': [2020],
        'language': ['Hindi'],
        'moods': ['romantic'],
        'themes': ['love'],
        'url': ['https://example.com'],
        'duration_sec': [300],
        'views': [1000000],
        'is_explicit': [False]
    }
    pd.DataFrame(catalog_data).to_csv(catalog_path, index=False)
    
    # Create embeddings
    embeddings = np.random.rand(1, 384).astype('float32')
    np.save(embeddings_path, embeddings)
    
    # Mock models
    mock_st = Mock()
    mock_st.encode.return_value = embeddings
    mock_sentence_transformer.return_value = mock_st
    
    mock_ce = Mock()
    mock_cross_encoder.return_value = mock_ce
    
    # Test creation
    recommender = create_recommender(
        catalog_path=str(catalog_path),
        embeddings_path=str(embeddings_path)
    )
    
    assert recommender is not None
    assert len(recommender.df) == 1
    assert recommender.emb is not None


def test_song_recommendation_dataclass():
    """Test SongRecommendation dataclass."""
    song = SongRecommendation(
        song_id="B001",
        title="Tum Hi Ho",
        url="https://example.com"
    )
    
    assert song.song_id == "B001"
    assert song.title == "Tum Hi Ho"
    assert song.url == "https://example.com"


if __name__ == "__main__":
    pytest.main([__file__])
