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
    
    # Thematic subtype information (for thematic queries)
    thematic_subtype: Optional[str] = None  # synthesis, enumerative, analytical, exploratory
    subtype_confidence: Optional[float] = None
    subtype_cues: Optional[List[str]] = None

class IntentClassifier:
    """
    Classifies the intent of a user query (e.g., factual, thematic, generative).
    Returns a structured IntentResult with confidence scoring and matched terms.
    """
    
    def __init__(self, laureate_names_path: str = "config/nobel_literature.json", config_path: str = "config/intent_keywords.json"):
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
            # Create fallback data with common Nobel laureates for testing
            fallback_data = self._create_fallback_laureate_data()
            full_names = set()
            last_names = set()
            for year in fallback_data:
                for laureate in year.get("laureates", []):
                    name = laureate.get("full_name")
                    if name:
                        full_names.add(name)
                        last = name.split()[-1]
                        last_names.add(last)
            logging.info(f"Using fallback laureate data with {len(full_names)} names")
            return (sorted(full_names, key=lambda n: -len(n)), sorted(last_names, key=lambda n: -len(n)))
    
    def _create_fallback_laureate_data(self):
        """Create minimal fallback data for testing when nobel_literature.json is missing."""
        return [
            {
                "year": 1993,
                "laureates": [{"full_name": "Toni Morrison", "country": "United States"}]
            },
            {
                "year": 2017,
                "laureates": [{"full_name": "Kazuo Ishiguro", "country": "United Kingdom"}]
            },
            {
                "year": 1989,
                "laureates": [{"full_name": "Camilo José Cela", "country": "Spain"}]
            },
            {
                "year": 2001,
                "laureates": [{"full_name": "V. S. Naipaul", "country": "United Kingdom"}]
            },
            {
                "year": 1995,
                "laureates": [{"full_name": "Seamus Heaney", "country": "Ireland"}]
            },
            {
                "year": 1990,
                "laureates": [{"full_name": "Octavio Paz", "country": "Mexico"}]
            }
        ]

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

    def _detect_thematic_subtype(self, query: str) -> tuple[Optional[str], Optional[float], Optional[List[str]]]:
        """
        Detect thematic subtype based on query patterns and keywords.
        
        Enhanced with flexible subject+verb matching for synthesis detection using
        the intent_utils module. Supports four subtypes:
        - synthesis: Cohesive, essay-like responses (enhanced with subject+verb patterns)
        - enumerative: List-based, example-focused responses
        - analytical: Comparative, contrast-focused responses  
        - exploratory: Contextual, explanatory responses
        
        Args:
            query: The user query string
            
        Returns:
            Tuple of (subtype, confidence, cues) where:
            - subtype: synthesis, enumerative, analytical, exploratory, or None
            - confidence: confidence score (0.0-1.0) or None
            - cues: list of keywords that triggered detection or None
        """
        query_lower = query.lower()
        cues = []
        max_confidence = 0.0
        detected_subtype = None
        
        # Import flexible matching utility
        try:
            from rag.intent_utils import matches_synthesis_frame
        except ImportError:
            # Fallback if intent_utils not available
            matches_synthesis_frame = lambda x: False
        
        # Define subtype patterns and keywords
        subtype_patterns = {
            "synthesis": [
                "synthesize", "synthesis", "connect", "unify", "coherent", "narrative",
                "draw together", "overall", "in general",
                "unified", "cohesive", "integrated", "holistic"
            ],
            "enumerative": [
                "list", "examples", "which speeches", "show me", "enumerate",
                "what are the", "give me", "find", "search", "locate",
                "specific", "instances", "cases", "occurrences"
            ],
            "analytical": [
                "compare", "contrast", "difference", "evolution", "change over time",
                "versus", "vs", "against", "similar", "different", "trend",
                "development", "progression", "transformation", "shift"
            ],
            "exploratory": [
                "context", "background", "significance", "history", "meaning",
                "explain", "why", "what is", "how did", "when", "where",
                "circumstances", "situation", "environment", "setting"
            ]
        }
        
        # Check each subtype pattern
        for subtype, patterns in subtype_patterns.items():
            subtype_cues = []
            confidence = 0.0
            
            for pattern in patterns:
                if pattern in query_lower:
                    subtype_cues.append(pattern)
                    confidence += 0.3  # Base confidence per match
            
            # Additional confidence for multiple matches
            if len(subtype_cues) > 1:
                confidence += 0.2
            
            # Check for strong indicators
            if any(strong_indicator in query_lower for strong_indicator in ["synthesize", "compare", "list", "context"]):
                confidence += 0.3
            
            # Enhanced synthesis detection using flexible subject+verb matching
            if subtype == "synthesis" and matches_synthesis_frame(query_lower):
                subtype_cues.append("synthesis_frame_match")
                confidence += 0.3
            
            if confidence > max_confidence:
                max_confidence = confidence
                detected_subtype = subtype
                cues = subtype_cues
        
        # Normalize confidence to 0.0-1.0 range
        if max_confidence > 0:
            max_confidence = min(max_confidence, 1.0)
            return detected_subtype, max_confidence, cues
        
        return None, None, None

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
        # Validate input
        if not query or not query.strip():
            raise ValueError("Could not determine intent: Empty or whitespace-only query")
        
        # Get pattern scores for each intent
        intent_scores = self._compute_pattern_scores(query)
        
        # Determine winning intent with precedence logic
        if not intent_scores:
            # No patterns matched, check if query is too vague
            if self._is_query_too_vague(query):
                raise ValueError("Could not determine intent: Query too vague or unclear")
            # Use fallback for simple factual queries
            winning_intent = self.config["settings"]["fallback_intent"]
            confidence = 0.1
        else:
            # Apply precedence logic: generative > thematic > factual
            winning_intent = self._apply_precedence_logic(intent_scores)
            confidence = self.compute_hybrid_confidence(query, intent_scores)
        
        # Get matched terms
        matched_terms = self._get_matched_terms(query, winning_intent)
        
        # Find laureates
        scoped_entities = self._find_laureates_in_query(query)
        
        # Detect thematic subtype if this is a thematic query
        thematic_subtype = None
        subtype_confidence = None
        subtype_cues = None
        
        if winning_intent == "thematic":
            thematic_subtype, subtype_confidence, subtype_cues = self._detect_thematic_subtype(query)
        
        # Build decision trace
        decision_trace = {
            "pattern_scores": intent_scores,
            "matched_patterns": matched_terms,
            "ambiguity": confidence < 0.7,
            "fallback_used": not intent_scores,
            "laureate_matches": len(scoped_entities),
            "lemmatization_used": self.use_lemmatization,
            "thematic_subtype": thematic_subtype,
            "subtype_confidence": subtype_confidence,
            "subtype_cues": subtype_cues
        }
        
        return IntentResult(
            intent=winning_intent,
            confidence=confidence,
            matched_terms=matched_terms,
            scoped_entities=scoped_entities,
            decision_trace=decision_trace,
            thematic_subtype=thematic_subtype,
            subtype_confidence=subtype_confidence,
            subtype_cues=subtype_cues
        )
    
    def _apply_precedence_logic(self, intent_scores: Dict[str, float]) -> str:
        """
        Apply precedence logic when multiple intents have similar scores.
        Precedence: generative > thematic > factual
        
        Args:
            intent_scores: Dictionary mapping intent to score
            
        Returns:
            Winning intent after applying precedence
        """
        if len(intent_scores) <= 1:
            return max(intent_scores, key=intent_scores.get)
        
        # Sort by score descending
        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
        max_score = sorted_intents[0][1]
        second_score = sorted_intents[1][1] if len(sorted_intents) > 1 else 0
        
        # If scores are close (within 0.3), apply precedence
        if max_score - second_score <= 0.3:
            # Check for generative intent
            if "generative" in intent_scores:
                return "generative"
            # Check for thematic intent
            elif "thematic" in intent_scores:
                return "thematic"
            # Fall back to highest score
            else:
                return sorted_intents[0][0]
        else:
            # Clear winner, no precedence needed
            return sorted_intents[0][0]

    def _is_query_too_vague(self, query: str) -> bool:
        """
        Check if a query is too vague to classify.
        
        Args:
            query: The user query string
            
        Returns:
            True if query is too vague, False otherwise
        """
        # List of vague phrases that should raise ValueError
        vague_phrases = [
            "tell me about",
            "information on",
            "details about",
            "something about",
            "tell me something",
            "give me information",
            "what can you tell me",
            "what do you know"
        ]
        
        query_lower = query.lower().strip()
        
        # Check for vague phrases
        for phrase in vague_phrases:
            if phrase in query_lower:
                return True
        
        # Check for very short queries (less than 3 words)
        words = query_lower.split()
        if len(words) < 3:
            return True
        
        # Check for queries that are just punctuation or nonsense
        if not any(c.isalpha() for c in query_lower):
            return True
        
        return False

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