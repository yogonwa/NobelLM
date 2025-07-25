"""
Reusable utilities for flexible intent matching and alias-based query pattern detection.
"""

SUBJECT_ALIASES = [
    "laureates", "winners", "recipients", "authors", "they", "these voices", "nobelists"
]

VERB_CUES = [
    "think", "feel", "say", "reflect", "talk about", "treat", "explore", "approach", "address"
]

def matches_synthesis_frame(query_lower: str) -> bool:
    """
    Return True if the query includes a fuzzy synthesis-style phrase like:
    'how do winners think about' or 'what do recipients say about'.
    
    Args:
        query_lower: The query string in lowercase
        
    Returns:
        True if the query matches a synthesis frame pattern
    """
    for subject in SUBJECT_ALIASES:
        for verb in VERB_CUES:
            phrase = f"{subject} {verb}"
            if phrase in query_lower:
                return True
    return False 