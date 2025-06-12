"""
Intent Classifier for Nobel Laureate Speech Explorer

Classifies user queries as factual, thematic, or generative, and detects if a thematic query is scoped to a specific laureate (by full or last name).

- Modular, testable, and extensible.
- Loads laureate names from Nobel metadata JSON.
- Prioritizes full name matches, but supports last name fallback.
- Uses configurable keywords with confidence scoring.
- Supports lemmatization for robust matching.
"""
import re
import json
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class IntentResult:
    """Structured result from intent classification."""
    intent: str
    confidence: float
    matched_terms: List[str]
    scoped_entities: List[str]
    decision_trace: Dict[str, Any]

class IntentClassifier:
    """
    Classifies the intent of a user query (e.g., factual, thematic, generative).
    Returns a structured IntentResult with confidence scoring and matched terms.
    """
    
    def __init__(self, laureate_names_path: str = "data/nobel_literature.json", config_path: str = "data/intent_keywords.json"):
        """
        Initialize the IntentClassifier.
        
        Args:
            laureate_names_path: Path to Nobel literature metadata JSON
            config_path: Path to intent keywords configuration JSON
        """
        self.laureate_full_names, self.laureate_last_names = self._load_laureate_names(laureate_names_path)
        self.config = self._load_config(config_path)
        self.use_lemmatization = self._setup_lemmatization()
        
        # Compile patterns for performance
        self._compile_patterns()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load intent keywords configuration from JSON."""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            logging.info(f"Loaded intent classifier config from {config_path}")
            return config
        except Exception as e:
            logging.warning(f"Could not load intent config from {config_path}: {e}")
            # Fallback to hardcoded config
            return self._get_fallback_config()
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """Fallback configuration if JSON config cannot be loaded."""
        return {
            "intents": {
                "factual": {
                    "keywords": {"what": 0.3, "when": 0.4, "who": 0.4, "quote": 0.9},
                    "phrases": {"who won": 0.8}
                },
                "thematic": {
                    "keywords": {"theme": 0.6, "compare": 0.7, "patterns": 0.8},
                    "phrases": {"what are": 0.5}
                },
                "generative": {
                    "keywords": {"write": 0.8, "compose": 0.9},
                    "phrases": {"in the style of": 0.95}
                }
            },
            "settings": {
                "min_confidence": 0.3,
                "ambiguity_threshold": 0.2,
                "fallback_intent": "factual",
                "max_laureate_matches": 3,
                "use_lemmatization": False,
                "lemmatization_fallback": True
            }
        }
    
    def _setup_lemmatization(self) -> bool:
        """Setup lemmatization support using ThemeReformulator if available."""
        try:
            from config.theme_reformulator import ThemeReformulator
            self.theme_reformulator = ThemeReformulator("config/themes.json")
            logging.info("Lemmatization enabled using ThemeReformulator")
            return True
        except ImportError:
            logging.warning("spaCy not available, lemmatization disabled")
            return False
        except Exception as e:
            logging.warning(f"Could not initialize lemmatization: {e}")
            return False
    
    def _compile_patterns(self):
        """Compile regex patterns for performance."""
        self.patterns = {}
        for intent, intent_config in self.config["intents"].items():
            # Compile keyword patterns
            keyword_patterns = []
            for keyword in intent_config["keywords"].keys():
                if ' ' not in keyword:  # Single word keywords
                    keyword_patterns.append(re.compile(rf'\b{re.escape(keyword)}\b', re.IGNORECASE))
            
            # Store phrases separately (no compilation needed)
            phrases = list(intent_config["phrases"].keys())
            
            self.patterns[intent] = {
                "keyword_patterns": keyword_patterns,
                "phrases": phrases
            }

    def _load_laureate_names(self, path: str):
        """Load all laureate full names and last names from the Nobel literature metadata JSON."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            full_names = set()
            last_names = set()
            for year in data:
                for laureate in year.get("laureates", []):
                    name = laureate.get("full_name")
                    if name:
                        full_names.add(name)
                        last = name.split()[-1]
                        last_names.add(last)
            # Sort by length descending for greedy match
            return (sorted(full_names, key=lambda n: -len(n)), sorted(last_names, key=lambda n: -len(n)))
        except Exception as e:
            logging.warning(f"Could not load laureate names: {e}")
            return [], []

    def _preprocess_query(self, query: str) -> str:
        """
        Preprocess query for matching: lowercase + lemmatization if available.
        
        Args:
            query: The user query string
            
        Returns:
            Preprocessed query string
        """
        if self.use_lemmatization:
            try:
                # Use ThemeReformulator's lemmatization
                lemmatized_tokens = self.theme_reformulator.lemmatize_query(query)
                return " ".join(lemmatized_tokens)
            except Exception as e:
                logging.warning(f"Lemmatization failed, falling back to basic processing: {e}")
                return query.lower()
        else:
            # Fallback to basic lowercase
            return query.lower()

    def _compute_pattern_scores(self, query: str) -> Dict[str, float]:
        """
        Compute pattern scores for each intent.
        
        Args:
            query: The user query string
            
        Returns:
            Dictionary mapping intent to score
        """
        processed_query = self._preprocess_query(query)
        intent_scores = {}
        
        for intent, intent_config in self.config["intents"].items():
            score = 0.0
            
            # Check keyword patterns
            for pattern in self.patterns[intent]["keyword_patterns"]:
                if pattern.search(processed_query):
                    keyword = pattern.pattern.replace(r'\b', '').replace(r'\b', '')
                    score += intent_config["keywords"].get(keyword, 0.0)
            
            # Check phrases
            for phrase in self.patterns[intent]["phrases"]:
                if phrase in processed_query:
                    score += intent_config["phrases"].get(phrase, 0.0)
            
            if score > 0:
                intent_scores[intent] = score
        
        return intent_scores

    def _get_matched_terms(self, query: str, intent: str) -> List[str]:
        """
        Get the specific terms that matched for the given intent.
        
        Args:
            query: The user query string
            intent: The intent to check for matches
            
        Returns:
            List of matched terms
        """
        processed_query = self._preprocess_query(query)
        matched_terms = []
        
        intent_config = self.config["intents"][intent]
        
        # Check keywords
        for keyword in intent_config["keywords"].keys():
            if ' ' not in keyword:  # Single word
                pattern = re.compile(rf'\b{re.escape(keyword)}\b', re.IGNORECASE)
                if pattern.search(processed_query):
                    matched_terms.append(keyword)
        
        # Check phrases
        for phrase in intent_config["phrases"].keys():
            if phrase in processed_query:
                matched_terms.append(phrase)
        
        return matched_terms

    def compute_hybrid_confidence(self, query: str, intent_scores: Dict[str, float]) -> float:
        """
        Compute hybrid confidence: pattern strength * (1 - ambiguity penalty).
        
        Args:
            query: The user query string
            intent_scores: Dictionary mapping intent to score
            
        Returns:
            Confidence score between 0.1 and 1.0
        """
        if not intent_scores:
            return 0.1
        
        # Pattern-based score (0.0 to 1.0)
        max_score = max(intent_scores.values())
        total_possible = sum(max(self.config["intents"][intent]["keywords"].values()) 
                            for intent in intent_scores)
        pattern_score = max_score / total_possible if total_possible > 0 else 0.0
        
        # Ambiguity penalty (0.0 to 1.0)
        ambiguity_penalty = self.compute_ambiguity_penalty(intent_scores)
        
        # Final confidence
        final_confidence = pattern_score * (1 - ambiguity_penalty)
        
        return max(0.1, min(1.0, final_confidence))

    def compute_ambiguity_penalty(self, intent_scores: Dict[str, float]) -> float:
        """
        Compute ambiguity penalty when multiple intents have similar scores.
        
        Args:
            intent_scores: Dictionary mapping intent to score
            
        Returns:
            Ambiguity penalty between 0.0 and 1.0
        """
        if len(intent_scores) <= 1:
            return 0.0
        
        scores = sorted(intent_scores.values(), reverse=True)
        max_score = scores[0]
        second_best = scores[1] if len(scores) > 1 else 0.0
        
        # Gap between best and second best
        gap = max_score - second_best
        
        # Normalize gap to 0-1 penalty
        if gap > 0.5:
            return 0.0  # Clear winner
        elif gap > 0.2:
            return 0.2  # Some ambiguity
        elif gap > 0.1:
            return 0.5  # High ambiguity
        else:
            return 0.8  # Very high ambiguity

    def _find_laureates_in_query(self, query: str) -> List[str]:
        """
        Find all laureate matches in query, not just the first one.
        
        Args:
            query: The user query string
            
        Returns:
            List of found laureate names
        """
        found_laureates = []
        q = query.lower()
        
        # Check full names first (more specific)
        for name in self.laureate_full_names:
            if name.lower() in q:
                found_laureates.append(name)
        
        # Check last names (less specific, but still valid)
        for last in self.laureate_last_names:
            if re.search(rf'\b{re.escape(last.lower())}\b', q):
                # Only add if not already found as full name
                if last not in found_laureates:
                    found_laureates.append(last)
        
        # Limit to max matches from config
        max_matches = self.config["settings"]["max_laureate_matches"]
        return found_laureates[:max_matches]

    def classify(self, query: str) -> IntentResult:
        """
        Classify query with hybrid confidence scoring and multiple laureate support.
        
        Args:
            query: The user query string
            
        Returns:
            IntentResult with intent, confidence, matched terms, and scoped entities
            
        Raises:
            ValueError: If no intent can be determined and no fallback is available
        """
        # Get pattern scores for each intent
        intent_scores = self._compute_pattern_scores(query)
        
        # Determine winning intent
        if not intent_scores:
            # No patterns matched, use fallback
            winning_intent = self.config["settings"]["fallback_intent"]
            confidence = 0.1
        else:
            winning_intent = max(intent_scores, key=intent_scores.get)
            confidence = self.compute_hybrid_confidence(query, intent_scores)
        
        # Get matched terms
        matched_terms = self._get_matched_terms(query, winning_intent)
        
        # Find laureates
        scoped_entities = self._find_laureates_in_query(query)
        
        # Build decision trace
        decision_trace = {
            "pattern_scores": intent_scores,
            "matched_patterns": matched_terms,
            "ambiguity": confidence < 0.7,
            "fallback_used": not intent_scores,
            "laureate_matches": len(scoped_entities),
            "lemmatization_used": self.use_lemmatization
        }
        
        return IntentResult(
            intent=winning_intent,
            confidence=confidence,
            matched_terms=matched_terms,
            scoped_entities=scoped_entities,
            decision_trace=decision_trace
        )

    # Legacy method for backward compatibility
    def classify_legacy(self, query: str) -> Any:
        """
        Legacy classification method that returns string or dict for backward compatibility.
        
        Args:
            query: The user query string
            
        Returns:
            String intent or dict with intent and scoped_entity
        """
        result = self.classify(query)
        
        if result.scoped_entities:
            return {"intent": result.intent, "scoped_entity": result.scoped_entities[0]}
        else:
            return result.intent 