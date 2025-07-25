"""
Comprehensive Audit Logger for NobelLM RAG Pipeline

This module provides detailed audit logging that captures the entire RAG pipeline:
1. User query
2. Intent classification and routing
3. Keyword expansion (for thematic queries) & Thematic subtype detection
4. Retrieval process and chunks
5. Prompt construction
6. LLM request and response
7. Final answer compilation

Each audit log entry contains the complete trace of a query through the system.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import os

logger = logging.getLogger(__name__)

@dataclass
class QueryAuditLog:
    """Complete audit log entry for a single query."""
    
    # Basic query info
    query_id: str
    timestamp: str
    user_query: str
    source: str = "api"  # api, cli, web, etc.
    
    # Intent and routing
    intent: Optional[str] = None
    confidence: Optional[float] = None
    matched_terms: Optional[List[str]] = None
    scoped_entity: Optional[str] = None
    decision_trace: Optional[List[str]] = None
    
    # Thematic subtype detection (for thematic queries)
    thematic_subtype: Optional[str] = None  # synthesis, enumerative, analytical, exploratory
    subtype_confidence: Optional[float] = None
    subtype_cues: Optional[List[str]] = None  # Keywords that triggered subtype detection
    
    # Keyword expansion (for thematic queries)
    expanded_terms: Optional[List[str]] = None
    term_similarities: Optional[Dict[str, float]] = None
    expansion_method: Optional[str] = None
    
    # Retrieval process
    retrieval_method: Optional[str] = None  # qdrant, faiss, etc.
    top_k: Optional[int] = None
    score_threshold: Optional[float] = None
    filters_applied: Optional[Dict[str, Any]] = None
    chunks_retrieved: Optional[List[Dict[str, Any]]] = None
    retrieval_scores: Optional[List[float]] = None
    chunk_count: Optional[int] = None
    
    # Prompt construction
    prompt_template: Optional[str] = None
    prompt_length: Optional[int] = None
    context_length: Optional[int] = None
    final_prompt: Optional[str] = None
    
    # LLM interaction
    llm_model: Optional[str] = None
    llm_temperature: Optional[float] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    estimated_cost_usd: Optional[float] = None
    llm_response: Optional[str] = None
    
    # Final result
    answer_type: Optional[str] = None  # rag, metadata
    final_answer: Optional[str] = None
    answer_length: Optional[int] = None
    sources_used: Optional[List[Dict[str, Any]]] = None
    
    # Performance metrics
    total_processing_time_ms: Optional[float] = None
    retrieval_time_ms: Optional[float] = None
    llm_time_ms: Optional[float] = None
    
    # Error handling
    error_occurred: bool = False
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    
    # Metadata
    model_id: Optional[str] = None
    environment: Optional[str] = None
    version: str = "1.0"

class AuditLogger:
    """
    Comprehensive audit logger for the NobelLM RAG pipeline.
    
    Captures complete trace of each query through the system and logs to
    structured JSON files for analysis and debugging.
    """
    
    def __init__(self, log_dir: str = "logs/audit", max_file_size_mb: int = 100):
        """
        Initialize the audit logger.
        
        Args:
            log_dir: Directory to store audit logs
            max_file_size_mb: Maximum size of log files before rotation
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size = max_file_size_mb * 1024 * 1024
        
        # Current log file
        self.current_log_file = self._get_current_log_file()
        
        # Active audit entries
        self.active_audits: Dict[str, QueryAuditLog] = {}
    
    def _get_current_log_file(self) -> Path:
        """Get the current log file path based on date."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"audit_log_{date_str}.jsonl"
    
    def start_audit(self, query_id: str, user_query: str, source: str = "api") -> str:
        """
        Start a new audit log entry for a query.
        
        Args:
            query_id: Unique identifier for the query
            user_query: The user's original query
            source: Source of the query (api, cli, web, etc.)
            
        Returns:
            The query ID for tracking
        """
        audit_entry = QueryAuditLog(
            query_id=query_id,
            timestamp=datetime.utcnow().isoformat() + "Z",
            user_query=user_query,
            source=source,
            environment=os.getenv("NOBELLM_ENVIRONMENT", "development")
        )
        
        self.active_audits[query_id] = audit_entry
        logger.debug(f"Started audit for query {query_id}")
        return query_id
    
    def log_intent_classification(
        self,
        query_id: str,
        intent: str,
        confidence: float,
        matched_terms: Optional[List[str]] = None,
        scoped_entity: Optional[str] = None,
        decision_trace: Optional[List[str]] = None
    ):
        """Log intent classification results."""
        if query_id in self.active_audits:
            audit = self.active_audits[query_id]
            audit.intent = intent
            audit.confidence = confidence
            audit.matched_terms = matched_terms
            audit.scoped_entity = scoped_entity
            audit.decision_trace = decision_trace

    def log_thematic_subtype(
        self,
        query_id: str,
        thematic_subtype: str,
        subtype_confidence: Optional[float] = None,
        subtype_cues: Optional[List[str]] = None
    ):
        """Log thematic subtype detection results."""
        if query_id in self.active_audits:
            audit = self.active_audits[query_id]
            audit.thematic_subtype = thematic_subtype
            audit.subtype_confidence = subtype_confidence
            audit.subtype_cues = subtype_cues
            logger.info(f"Logged thematic subtype for {query_id}: {thematic_subtype} (confidence: {subtype_confidence})")
    
    def log_keyword_expansion(
        self,
        query_id: str,
        expanded_terms: List[str],
        term_similarities: Optional[Dict[str, float]] = None,
        expansion_method: str = "thematic"
    ):
        """Log keyword expansion results."""
        if query_id in self.active_audits:
            audit = self.active_audits[query_id]
            audit.expanded_terms = expanded_terms
            audit.term_similarities = term_similarities
            audit.expansion_method = expansion_method
    
    def log_retrieval_process(
        self,
        query_id: str,
        retrieval_method: str,
        top_k: int,
        score_threshold: float,
        filters_applied: Optional[Dict[str, Any]] = None,
        chunks_retrieved: Optional[List[Dict[str, Any]]] = None,
        retrieval_scores: Optional[List[float]] = None,
        processing_time_ms: Optional[float] = None
    ):
        """Log retrieval process details."""
        if query_id in self.active_audits:
            audit = self.active_audits[query_id]
            audit.retrieval_method = retrieval_method
            audit.top_k = top_k
            audit.score_threshold = score_threshold
            audit.filters_applied = filters_applied
            audit.chunks_retrieved = chunks_retrieved
            audit.retrieval_scores = retrieval_scores
            audit.chunk_count = len(chunks_retrieved) if chunks_retrieved else 0
            audit.retrieval_time_ms = processing_time_ms
    
    def log_prompt_construction(
        self,
        query_id: str,
        prompt_template: str,
        final_prompt: str,
        context_length: Optional[int] = None
    ):
        """Log prompt construction details."""
        if query_id in self.active_audits:
            audit = self.active_audits[query_id]
            audit.prompt_template = prompt_template
            audit.final_prompt = final_prompt
            audit.prompt_length = len(final_prompt)
            audit.context_length = context_length
    
    def log_llm_interaction(
        self,
        query_id: str,
        llm_model: str,
        llm_response: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        estimated_cost_usd: float,
        llm_temperature: float = 0.2,
        processing_time_ms: Optional[float] = None
    ):
        """Log LLM interaction details."""
        if query_id in self.active_audits:
            audit = self.active_audits[query_id]
            audit.llm_model = llm_model
            audit.llm_response = llm_response
            audit.prompt_tokens = prompt_tokens
            audit.completion_tokens = completion_tokens
            audit.total_tokens = total_tokens
            audit.estimated_cost_usd = estimated_cost_usd
            audit.llm_temperature = llm_temperature
            audit.llm_time_ms = processing_time_ms
    
    def log_final_result(
        self,
        query_id: str,
        answer_type: str,
        final_answer: str,
        sources_used: Optional[List[Dict[str, Any]]] = None,
        total_processing_time_ms: Optional[float] = None
    ):
        """Log final result details."""
        if query_id in self.active_audits:
            audit = self.active_audits[query_id]
            audit.answer_type = answer_type
            audit.final_answer = final_answer
            audit.answer_length = len(final_answer) if final_answer else 0
            audit.sources_used = sources_used
            audit.total_processing_time_ms = total_processing_time_ms
    
    def log_error(
        self,
        query_id: str,
        error_message: str,
        error_type: str,
        error_occurred: bool = True
    ):
        """Log error details."""
        if query_id in self.active_audits:
            audit = self.active_audits[query_id]
            audit.error_occurred = error_occurred
            audit.error_message = error_message
            audit.error_type = error_type
    
    def complete_audit(self, query_id: str) -> Optional[QueryAuditLog]:
        """
        Complete an audit log entry and write it to the log file.
        
        Args:
            query_id: The query ID to complete
            
        Returns:
            The completed audit log entry, or None if not found
        """
        if query_id not in self.active_audits:
            logger.warning(f"Attempted to complete non-existent audit for query {query_id}")
            return None
        
        audit = self.active_audits[query_id]
        
        # Write to log file
        try:
            # Check if we need to rotate the log file
            if self.current_log_file.exists() and self.current_log_file.stat().st_size > self.max_file_size:
                self.current_log_file = self._get_current_log_file()
            
            # Convert to dict and write as JSON line
            audit_dict = asdict(audit)
            with open(self.current_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(audit_dict, ensure_ascii=False) + "\n")
            
            # Remove from active audits
            del self.active_audits[query_id]
            
            logger.debug(f"Completed audit for query {query_id}")
            return audit
            
        except Exception as e:
            logger.error(f"Failed to write audit log for query {query_id}: {e}")
            return audit
    
    def get_audit_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get a summary of audit logs for the specified time period.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Summary statistics
        """
        cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
        audits = []
        
        # Read all audit files
        for log_file in self.log_dir.glob("audit_log_*.jsonl"):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            audit_data = json.loads(line.strip())
                            # Check if within time range
                            audit_time = datetime.fromisoformat(audit_data["timestamp"].replace("Z", "+00:00")).timestamp()
                            if audit_time >= cutoff_time:
                                audits.append(audit_data)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                logger.error(f"Error reading audit file {log_file}: {e}")
        
        if not audits:
            return {"total_queries": 0}
        
        # Calculate summary statistics
        total_queries = len(audits)
        successful_queries = len([a for a in audits if not a.get("error_occurred", False)])
        failed_queries = total_queries - successful_queries
        
        # Intent distribution
        intents = [a.get("intent") for a in audits if a.get("intent")]
        intent_counts = {}
        for intent in intents:
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        # Performance metrics
        processing_times = [a.get("total_processing_time_ms") for a in audits if a.get("total_processing_time_ms")]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Cost analysis
        total_cost = sum([a.get("estimated_cost_usd", 0) for a in audits])
        total_tokens = sum([a.get("total_tokens", 0) for a in audits])
        
        return {
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "failed_queries": failed_queries,
            "success_rate": successful_queries / total_queries if total_queries > 0 else 0,
            "intent_distribution": intent_counts,
            "avg_processing_time_ms": avg_processing_time,
            "total_cost_usd": total_cost,
            "total_tokens": total_tokens,
            "time_period_hours": hours
        }

# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None

def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger

def start_query_audit(user_query: str, source: str = "api") -> str:
    """Start a new query audit and return the query ID."""
    query_id = str(uuid.uuid4())
    get_audit_logger().start_audit(query_id, user_query, source)
    return query_id

def complete_query_audit(query_id: str) -> Optional[QueryAuditLog]:
    """Complete a query audit and return the audit log."""
    return get_audit_logger().complete_audit(query_id) 