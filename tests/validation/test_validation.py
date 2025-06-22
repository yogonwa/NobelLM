"""
Unit tests for rag.validation module.

These tests ensure that all validation functions work correctly and handle edge cases properly.
The validation module is critical for Phase 1 robustness improvements.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from rag.validation import (
    validate_query_string,
    validate_embedding_vector,
    validate_filters,
    validate_retrieval_parameters,
    validate_model_id,
    safe_faiss_scoring
)


@pytest.mark.validation
class TestValidateQueryString:
    """Test query string validation."""
    
    @pytest.mark.validation
    def test_valid_query_string(self):
        """Test that valid query strings pass validation."""
        valid_queries = [
            "What do laureates say about justice?",
            "Justice",
            "AB",  # Changed from "A" to "AB" - minimum 2 chars
            "Justice and peace in literature",
            "What are the themes in Nobel literature?",
            "Write a speech in the style of a Nobel laureate",
            "Justice 123",  # Mixed text and numbers is valid
            "123 Justice"   # Mixed text and numbers is valid
        ]
        
        for query in valid_queries:
            # Should not raise any exception
            validate_query_string(query, context="test")
    
    @pytest.mark.validation
    def test_empty_query_string(self):
        """Test that empty query strings are rejected."""
        invalid_queries = [
            "",
            None,
            123,  # Not a string
            [],
            {}
        ]
        
        for query in invalid_queries:
            with pytest.raises(ValueError, match="must be a non-empty string"):
                validate_query_string(query, context="test")
    
    @pytest.mark.validation
    def test_whitespace_only_query(self):
        """Test that whitespace-only queries are rejected."""
        whitespace_queries = [
            "   ",
            "\t\n",
            " \n \t ",
            "\n\n\n"
        ]
        
        for query in whitespace_queries:
            with pytest.raises(ValueError, match="cannot be whitespace-only"):
                validate_query_string(query, context="test")
    
    @pytest.mark.validation
    def test_too_short_query(self):
        """Test that queries shorter than 2 characters are rejected."""
        short_queries = [
            "a",
            "1",
            "x"
        ]
        
        for query in short_queries:
            with pytest.raises(ValueError, match="must be at least 2 characters long"):
                validate_query_string(query, context="test")
    
    @pytest.mark.validation
    def test_suspicious_patterns(self):
        """Test that suspicious patterns are rejected."""
        suspicious_queries = [
            "!@#$%",  # Only special characters
            "12345",  # Only digits
        ]
        
        for query in suspicious_queries:
            with pytest.raises(ValueError, match="contains suspicious pattern"):
                validate_query_string(query, context="test")


@pytest.mark.validation
class TestValidateEmbeddingVector:
    """Test embedding vector validation."""
    
    @pytest.mark.validation
    def test_valid_embedding_vector(self):
        """Test that valid embedding vectors pass validation."""
        # Valid 1D vector
        vec_1d = np.random.rand(384).astype(np.float32)
        validate_embedding_vector(vec_1d, context="test")
        
        # Valid 2D vector
        vec_2d = np.random.rand(1, 384).astype(np.float32)
        validate_embedding_vector(vec_2d, context="test")
        
        # Valid vector with expected dimension
        validate_embedding_vector(vec_1d, expected_dim=384, context="test")
    
    @pytest.mark.validation
    def test_invalid_vector_types(self):
        """Test that non-numpy arrays are rejected."""
        invalid_vectors = [
            [1, 2, 3],  # List
            (1, 2, 3),  # Tuple
            "string",   # String
            123,        # Integer
            None        # None
        ]
        
        for vec in invalid_vectors:
            with pytest.raises(ValueError, match="must be a numpy array"):
                validate_embedding_vector(vec, context="test")
    
    @pytest.mark.validation
    def test_empty_vector(self):
        """Test that empty vectors are rejected."""
        empty_vectors = [
            np.array([]),
            np.array([[]]),
            np.array([], dtype=np.float32)
        ]
        
        for vec in empty_vectors:
            with pytest.raises(ValueError, match="cannot be empty"):
                validate_embedding_vector(vec, context="test")
    
    @pytest.mark.validation
    def test_nan_values(self):
        """Test that vectors with NaN values are rejected."""
        vec_with_nan = np.array([1.0, np.nan, 3.0], dtype=np.float32)
        
        with pytest.raises(ValueError, match="contains NaN values"):
            validate_embedding_vector(vec_with_nan, context="test")
    
    @pytest.mark.validation
    def test_infinite_values(self):
        """Test that vectors with infinite values are rejected."""
        vec_with_inf = np.array([1.0, np.inf, 3.0], dtype=np.float32)
        
        with pytest.raises(ValueError, match="contains infinite values"):
            validate_embedding_vector(vec_with_inf, context="test")
    
    @pytest.mark.validation
    def test_zero_vector(self):
        """Test that zero vectors are rejected."""
        zero_vec = np.zeros(384, dtype=np.float32)
        
        with pytest.raises(ValueError, match="is a zero vector"):
            validate_embedding_vector(zero_vec, context="test")
    
    @pytest.mark.validation
    def test_scalar_vector(self):
        """Test that scalar vectors are rejected."""
        scalar_vec = np.array(1.0)
        
        with pytest.raises(ValueError, match="is a scalar, expected array"):
            validate_embedding_vector(scalar_vec, context="test")
    
    @pytest.mark.validation
    def test_high_dimensional_vector(self):
        """Test that vectors with more than 2 dimensions are rejected."""
        high_dim_vec = np.random.rand(1, 384, 1).astype(np.float32)
        
        with pytest.raises(ValueError, match="too many dimensions"):
            validate_embedding_vector(high_dim_vec, context="test")
    
    @pytest.mark.validation
    def test_dimension_mismatch(self):
        """Test that vectors with wrong dimensions are rejected."""
        vec = np.random.rand(512).astype(np.float32)  # 512 dimensions
        
        with pytest.raises(ValueError, match="dimension mismatch"):
            validate_embedding_vector(vec, expected_dim=384, context="test")
    
    @pytest.mark.validation
    def test_dtype_conversion(self):
        """Test that non-float32 vectors trigger dtype conversion warning."""
        vec_float64 = np.random.rand(384).astype(np.float64)
        
        # Mock the logger to capture the warning
        with patch('rag.validation.logger') as mock_logger:
            validate_embedding_vector(vec_float64, context="test")
            # Verify warning was logged
            mock_logger.warning.assert_called_once()
            warning_call = mock_logger.warning.call_args[0][0]
            assert "dtype is float64, converting to float32" in warning_call


@pytest.mark.validation
class TestValidateFilters:
    """Test filter validation."""
    
    @pytest.mark.validation
    def test_valid_filters(self):
        """Test that valid filters pass validation."""
        valid_filters = [
            None,  # None is valid
            {},    # Empty dict is valid
            {"source_type": "lecture"},
            {"laureate": "Bob Dylan", "year_awarded": 2016},
            {"country": "USA", "source_type": "ceremony_speech"}
        ]
        
        for filters in valid_filters:
            validate_filters(filters, context="test")
    
    @pytest.mark.validation
    def test_invalid_filter_types(self):
        """Test that non-dict filters are rejected."""
        invalid_filters = [
            "string",
            123,
            [1, 2, 3],
            (1, 2, 3),
            None  # None is actually valid
        ]
        
        for filters in invalid_filters:
            if filters is not None:  # Skip None as it's valid
                with pytest.raises(ValueError, match="must be a dictionary or None"):
                    validate_filters(filters, context="test")
    
    @pytest.mark.validation
    def test_invalid_filter_keys(self):
        """Test that filters with invalid keys are rejected."""
        invalid_key_filters = [
            {123: "value"},  # Non-string key
            {"": "value"},   # Empty key
            {"key": None}    # None value (should warn but not fail)
        ]
        
        for filters in invalid_key_filters:
            if 123 in filters:  # Non-string key
                with pytest.raises(ValueError, match="keys must be strings"):
                    validate_filters(filters, context="test")
            elif "" in filters:  # Empty key
                with pytest.raises(ValueError, match="contains empty key"):
                    validate_filters(filters, context="test")
            else:  # None value
                with patch('rag.validation.logger') as mock_logger:
                    validate_filters(filters, context="test")
                    # Verify warning was logged
                    mock_logger.warning.assert_called_once()
                    warning_call = mock_logger.warning.call_args[0][0]
                    assert "has None value" in warning_call
    
    @pytest.mark.validation
    def test_filter_key_validation(self):
        """Test validation against valid keys list."""
        valid_keys = ["source_type", "laureate", "year_awarded"]
        
        # Valid filters
        validate_filters({"source_type": "lecture"}, valid_keys=valid_keys, context="test")
        
        # Invalid filters
        with pytest.raises(ValueError, match="contains invalid keys"):
            validate_filters({"invalid_key": "value"}, valid_keys=valid_keys, context="test")


@pytest.mark.validation
class TestValidateRetrievalParameters:
    """Test retrieval parameter validation."""
    
    @pytest.mark.validation
    def test_valid_parameters(self):
        """Test that valid parameters pass validation."""
        # All parameters valid
        validate_retrieval_parameters(
            top_k=5,
            score_threshold=0.2,
            min_return=3,
            max_return=10,
            context="test"
        )
        
        # Without max_return
        validate_retrieval_parameters(
            top_k=5,
            score_threshold=0.2,
            min_return=3,
            context="test"
        )
    
    @pytest.mark.validation
    def test_invalid_top_k(self):
        """Test that invalid top_k values are rejected."""
        invalid_top_k_values = [
            0,      # Zero
            -1,     # Negative
            1.5,    # Float
            "5",    # String
            None    # None
        ]
        
        for top_k in invalid_top_k_values:
            with pytest.raises(ValueError, match="top_k must be positive integer"):
                validate_retrieval_parameters(
                    top_k=top_k,
                    score_threshold=0.2,
                    min_return=3,
                    context="test"
                )
    
    @pytest.mark.validation
    def test_invalid_score_threshold(self):
        """Test that invalid score_threshold values are rejected."""
        invalid_thresholds = [
            -0.1,   # Negative
            "0.2",  # String
            None    # None
        ]
        
        for threshold in invalid_thresholds:
            with pytest.raises(ValueError, match="score_threshold must be non-negative"):
                validate_retrieval_parameters(
                    top_k=5,
                    score_threshold=threshold,
                    min_return=3,
                    context="test"
                )
    
    @pytest.mark.validation
    def test_invalid_min_return(self):
        """Test that invalid min_return values are rejected."""
        invalid_min_returns = [
            0,      # Zero
            -1,     # Negative
            1.5,    # Float
            "3",    # String
            None    # None
        ]
        
        for min_return in invalid_min_returns:
            with pytest.raises(ValueError, match="min_return must be positive integer"):
                validate_retrieval_parameters(
                    top_k=5,
                    score_threshold=0.2,
                    min_return=min_return,
                    context="test"
                )
    
    @pytest.mark.validation
    def test_invalid_max_return(self):
        """Test that invalid max_return values are rejected."""
        invalid_max_returns = [
            0,      # Zero
            -1,     # Negative
            1.5,    # Float
            "10",   # String
        ]
        
        for max_return in invalid_max_returns:
            with pytest.raises(ValueError, match="max_return must be positive integer"):
                validate_retrieval_parameters(
                    top_k=5,
                    score_threshold=0.2,
                    min_return=3,
                    max_return=max_return,
                    context="test"
                )
    
    @pytest.mark.validation
    def test_max_return_less_than_min_return(self):
        """Test that max_return cannot be less than min_return."""
        with pytest.raises(ValueError, match="max_return.*cannot be less than min_return"):
            validate_retrieval_parameters(
                top_k=5,
                score_threshold=0.2,
                min_return=5,
                max_return=3,
                context="test"
            )
    
    @pytest.mark.validation
    def test_min_return_greater_than_top_k(self):
        """Test that min_return cannot be greater than top_k."""
        with pytest.raises(ValueError, match="min_return.*cannot be greater than top_k"):
            validate_retrieval_parameters(
                top_k=3,
                score_threshold=0.2,
                min_return=5,
                context="test"
            )


@pytest.mark.validation
class TestValidateModelId:
    """Test model ID validation."""
    
    @pytest.mark.validation
    def test_valid_model_ids(self):
        """Test that valid model IDs pass validation."""
        valid_ids = [
            "bge-large",
            "miniLM",
            "all-MiniLM-L6-v2",
            "model_name_123",
            "model-name",
            "model.name"
        ]
        
        for model_id in valid_ids:
            validate_model_id(model_id, context="test")
    
    @pytest.mark.validation
    def test_invalid_model_ids(self):
        """Test that invalid model IDs are rejected."""
        invalid_ids = [
            "",           # Empty
            "   ",        # Whitespace only
            None,         # None
            123,          # Not string
            "model<name", # Invalid characters
            "model>name",
            "model:name",
            "model\"name",
            "model|name",
            "model?name",
            "model*name"
        ]
        
        for model_id in invalid_ids:
            if model_id is None:
                with pytest.raises(ValueError, match="must be non-empty string"):
                    validate_model_id(model_id, context="test")
            elif model_id == "":
                with pytest.raises(ValueError, match="must be non-empty string"):
                    validate_model_id(model_id, context="test")
            elif model_id == "   ":
                with pytest.raises(ValueError, match="cannot be whitespace-only"):
                    validate_model_id(model_id, context="test")
            elif not isinstance(model_id, str):
                with pytest.raises(ValueError, match="must be non-empty string"):
                    validate_model_id(model_id, context="test")
            else:
                with pytest.raises(ValueError, match="contains invalid characters"):
                    validate_model_id(model_id, context="test")


@pytest.mark.validation
class TestSafeFaissScoring:
    """Test safe FAISS scoring function."""
    
    @pytest.mark.validation
    def test_valid_scoring(self):
        """Test that valid inputs produce correct scores."""
        # Create test vectors
        filtered_vectors = np.random.rand(5, 384).astype(np.float32)
        query_embedding = np.random.rand(1, 384).astype(np.float32)
        
        # Normalize vectors
        filtered_vectors = filtered_vectors / np.linalg.norm(filtered_vectors, axis=1, keepdims=True)
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        scores = safe_faiss_scoring(filtered_vectors, query_embedding, context="test")
        
        # Check output
        assert isinstance(scores, np.ndarray)
        assert scores.ndim == 1
        assert len(scores) == 5
        assert all(score >= -1.0 and score <= 1.0 for score in scores)
    
    @pytest.mark.validation
    def test_1d_vector_handling(self):
        """Test that 1D vectors are properly reshaped."""
        # 1D vectors
        filtered_vectors = np.random.rand(384).astype(np.float32)
        query_embedding = np.random.rand(384).astype(np.float32)
        
        scores = safe_faiss_scoring(filtered_vectors, query_embedding, context="test")
        
        assert isinstance(scores, np.ndarray)
        assert scores.ndim == 1
        assert len(scores) == 1
    
    @pytest.mark.validation
    def test_invalid_inputs(self):
        """Test that invalid inputs are rejected."""
        # Invalid filtered vectors
        with pytest.raises(ValueError, match="must be a numpy array"):
            safe_faiss_scoring("invalid", np.random.rand(384), context="test")
        
        # Invalid query embedding
        with pytest.raises(ValueError, match="must be a numpy array"):
            safe_faiss_scoring(np.random.rand(384), "invalid", context="test")
        
        # Zero vectors
        zero_vec = np.zeros(384, dtype=np.float32)
        with pytest.raises(ValueError, match="is a zero vector"):
            safe_faiss_scoring(zero_vec, np.random.rand(384), context="test")
    
    @pytest.mark.validation
    def test_shape_mismatch(self):
        """Test that shape mismatches are handled properly."""
        # Different dimensions
        filtered_vectors = np.random.rand(5, 384).astype(np.float32)
        query_embedding = np.random.rand(1, 512).astype(np.float32)  # Wrong dimension
        
        with pytest.raises(ValueError, match="Dimension mismatch"):
            safe_faiss_scoring(filtered_vectors, query_embedding, context="test")
    
    @pytest.mark.validation
    def test_scalar_output_handling(self):
        """Test that scalar outputs are properly converted to arrays."""
        # Single vector case that might produce scalar
        filtered_vectors = np.random.rand(1, 384).astype(np.float32)
        query_embedding = np.random.rand(1, 384).astype(np.float32)
        
        scores = safe_faiss_scoring(filtered_vectors, query_embedding, context="test")
        
        assert isinstance(scores, np.ndarray)
        assert scores.ndim == 1
        assert len(scores) == 1


@pytest.mark.validation
class TestValidationIntegration:
    """Integration tests for validation functions."""
    
    @pytest.mark.validation
    def test_validation_chain(self):
        """Test that validation functions work together correctly."""
        # Valid inputs should pass all validations
        query = "What do laureates say about justice?"
        model_id = "bge-large"
        filters = {"source_type": "lecture"}
        embedding = np.random.rand(384).astype(np.float32)
        
        # All validations should pass
        validate_query_string(query, context="integration")
        validate_model_id(model_id, context="integration")
        validate_filters(filters, context="integration")
        validate_embedding_vector(embedding, context="integration")
        validate_retrieval_parameters(
            top_k=5,
            score_threshold=0.2,
            min_return=3,
            max_return=10,
            context="integration"
        )
    
    @pytest.mark.validation
    def test_validation_error_propagation(self):
        """Test that validation errors propagate correctly."""
        # Invalid inputs should fail validation
        with pytest.raises(ValueError):
            validate_query_string("", context="integration")
        
        with pytest.raises(ValueError):
            validate_model_id("", context="integration")
        
        with pytest.raises(ValueError):
            validate_embedding_vector(np.array([]), context="integration") 