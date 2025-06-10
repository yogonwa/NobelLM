"""
Utility functions for testing intent classification results.
These functions help validate the output of the IntentClassifier across different test files.
"""

def is_thematic(result, expected_scoped=None):
    """
    Check if a classification result indicates a thematic intent.
    
    Args:
        result: Either a string "thematic" or a dict with "intent" and optional "scoped_entity"
        expected_scoped: Optional expected scoped entity name to validate
        
    Returns:
        bool: True if result indicates thematic intent and matches scoped entity if specified
    """
    if isinstance(result, dict):
        if result.get("intent") != "thematic":
            return False
        if expected_scoped is not None:
            return result.get("scoped_entity") == expected_scoped
        return True
    return result == "thematic"

def is_factual(result):
    """
    Check if a classification result indicates a factual intent.
    
    Args:
        result: Either a string "factual" or a dict with "intent"
        
    Returns:
        bool: True if result indicates factual intent
    """
    if isinstance(result, dict):
        return result.get("intent") == "factual"
    return result == "factual"

def is_generative(result):
    """
    Check if a classification result indicates a generative intent.
    
    Args:
        result: Either a string "generative" or a dict with "intent"
        
    Returns:
        bool: True if result indicates generative intent
    """
    if isinstance(result, dict):
        return result.get("intent") == "generative"
    return result == "generative" 