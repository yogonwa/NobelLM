"""
Prompt Builder for NobelLM RAG Pipeline

This module provides intelligent, metadata-aware prompt construction with citation
scaffolding, explainable formatting, and intent-specific templates.

Author: Joe Gonwa
Date: 2025-01-XX
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplate:
    """Represents a prompt template with metadata and configuration."""
    name: str
    template: str
    intent: str
    tags: List[str]
    chunk_count: int = 5
    citation_style: str = "inline"
    tone_preference: Optional[str] = None
    version: str = "1.0"


class PromptBuilder:
    """
    Intelligent prompt builder with metadata awareness, citation scaffolding,
    and intent-specific templates.
    """
    
    def __init__(self, template_path: Optional[str] = None):
        """
        Initialize the prompt builder with template configuration.
        
        Args:
            template_path: Path to prompt templates JSON file. If None, uses default.
        """
        self.template_path = template_path or "config/prompt_templates.json"
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_templates()
    
    def _load_templates(self) -> None:
        """Load prompt templates from configuration file."""
        try:
            template_file = Path(self.template_path)
            if template_file.exists():
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                
                for template_name, template_info in template_data.items():
                    self.templates[template_name] = PromptTemplate(
                        name=template_name,
                        template=template_info["template"],
                        intent=template_info["intent"],
                        tags=template_info.get("tags", []),
                        chunk_count=template_info.get("chunk_count", 5),
                        citation_style=template_info.get("citation_style", "inline"),
                        tone_preference=template_info.get("tone_preference"),
                        version=template_info.get("version", "1.0")
                    )
                logger.info(f"Loaded {len(self.templates)} prompt templates")
            else:
                logger.warning(f"Template file {self.template_path} not found, using defaults")
                self._load_default_templates()
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")
            self._load_default_templates()
    
    def _load_default_templates(self) -> None:
        """Load default templates when configuration file is not available."""
        default_templates = {
            "qa_factual": PromptTemplate(
                name="qa_factual",
                template="Answer the following question about Nobel Literature laureates: {query}\n\nContext:\n{context}",
                intent="qa",
                tags=["qa", "factual"],
                chunk_count=5,
                citation_style="inline"
            ),
            "qa_analytical": PromptTemplate(
                name="qa_analytical",
                template="Analyze the following question about Nobel Literature laureates: {query}\n\nContext:\n{context}\n\nPlease provide a detailed analysis with specific citations.",
                intent="qa",
                tags=["qa", "analytical"],
                chunk_count=8,
                citation_style="footnote"
            ),
            "generative_email": PromptTemplate(
                name="generative_email",
                template="You are a Nobel laureate. {query}\n\nUse the following excerpts as inspiration for your response:\n{context}\n\nWrite in the style of a Nobel laureate with appropriate humility and gratitude.",
                intent="generative",
                tags=["generative", "email", "laureate-style"],
                chunk_count=10,
                citation_style="inline",
                tone_preference="humble"
            ),
            "thematic_exploration": PromptTemplate(
                name="thematic_exploration",
                template="Explore the theme of '{query}' using the following Nobel laureate perspectives:\n{context}\n\nProvide a comprehensive analysis with diverse viewpoints.",
                intent="thematic",
                tags=["thematic", "exploration"],
                chunk_count=12,
                citation_style="inline"
            )
        }
        self.templates.update(default_templates)
        logger.info("Loaded default prompt templates")
    
    def build_qa_prompt(self, query: str, chunks: List[Dict], intent: str = "qa") -> str:
        """
        Build a QA prompt with appropriate formatting and citations.
        
        Args:
            query: The user's question
            chunks: List of retrieved chunks with metadata
            intent: Query intent (qa, analytical, etc.)
            
        Returns:
            Formatted prompt string
        """
        template = self._get_template_for_intent(intent, "qa")
        formatted_chunks = self._format_chunks_with_metadata(chunks, template.citation_style)
        
        return template.template.format(
            query=query,
            context=formatted_chunks
        )
    
    def build_generative_prompt(self, task_description: str, chunks: List[Dict], intent: str = "generative") -> str:
        """
        Build a generative prompt for creative tasks.
        
        Args:
            task_description: Description of the creative task
            chunks: List of retrieved chunks with metadata
            intent: Query intent (email, speech, etc.)
            
        Returns:
            Formatted prompt string
        """
        template = self._get_template_for_intent(intent, "generative")
        formatted_chunks = self._format_chunks_with_metadata(chunks, template.citation_style)
        
        return template.template.format(
            query=task_description,
            context=formatted_chunks
        )
    
    def build_thematic_prompt(self, query: str, chunks: List[Dict], theme: str) -> str:
        """
        Build a thematic exploration prompt.
        
        Args:
            query: The thematic query
            chunks: List of retrieved chunks with metadata
            theme: The theme being explored
            
        Returns:
            Formatted prompt string
        """
        template = self._get_template_for_intent("thematic", "thematic")
        formatted_chunks = self._format_chunks_with_metadata(chunks, template.citation_style)
        
        return template.template.format(
            query=query,
            context=formatted_chunks
        )
    
    def build_scoped_prompt(self, query: str, chunks: List[Dict], laureate: str) -> str:
        """
        Build a scoped prompt for specific laureate queries.
        
        Args:
            query: The user's question
            chunks: List of retrieved chunks with metadata
            laureate: The specific laureate being queried
            
        Returns:
            Formatted prompt string
        """
        template = self._get_template_for_intent("scoped", "qa")
        formatted_chunks = self._format_chunks_with_metadata(chunks, template.citation_style)
        
        return template.template.format(
            query=query,
            context=formatted_chunks,
            laureate=laureate
        )
    
    def _get_template_for_intent(self, intent: str, base_type: str) -> PromptTemplate:
        """Get the appropriate template for the given intent."""
        # Try to find a specific template for the intent
        for template in self.templates.values():
            if template.intent == intent or intent in template.tags:
                return template
        
        # Fallback to base type
        for template in self.templates.values():
            if template.intent == base_type:
                return template
        
        # Final fallback to qa_factual
        return self.templates.get("qa_factual", self.templates[list(self.templates.keys())[0]])
    
    def _format_chunks_with_metadata(self, chunks: List[Dict], citation_style: str = "inline") -> str:
        """
        Format chunks with metadata and citations.
        
        Args:
            chunks: List of chunk dictionaries
            citation_style: Citation style (inline, footnote, full)
            
        Returns:
            Formatted chunks string
        """
        formatted_chunks = []
        
        for i, chunk in enumerate(chunks, 1):
            # Extract metadata
            metadata = chunk.get("metadata", {})
            laureate = metadata.get("laureate", "Unknown")
            year = metadata.get("year", "Unknown")
            speech_type = metadata.get("speech_type", "speech")
            category = metadata.get("category", "Literature")
            
            # Create visual marker
            if speech_type == "lecture":
                marker = "🎓"
            elif speech_type == "ceremony":
                marker = "🏅"
            else:
                marker = "📚"
            
            # Format citation based on style
            if citation_style == "inline":
                citation = f"({laureate}, {year})"
            elif citation_style == "footnote":
                citation = f"[{i}] {laureate}, {category} {year}"
            else:  # full
                citation = f"{laureate}, Nobel Prize in {category}, {year}"
            
            # Format the chunk
            chunk_text = chunk.get("text", "").strip()
            formatted_chunk = f"[{marker} {speech_type.title()} — {laureate}, {year}] {chunk_text}"
            
            if citation_style == "inline":
                formatted_chunk += f" {citation}"
            
            formatted_chunks.append(formatted_chunk)
        
        # Add footnotes if using footnote style
        if citation_style == "footnote":
            footnotes = []
            for i, chunk in enumerate(chunks, 1):
                metadata = chunk.get("metadata", {})
                laureate = metadata.get("laureate", "Unknown")
                year = metadata.get("year", "Unknown")
                category = metadata.get("category", "Literature")
                footnotes.append(f"[{i}] {laureate}, Nobel Prize in {category}, {year}")
            
            formatted_chunks.append("\n--- FOOTNOTES ---")
            formatted_chunks.extend(footnotes)
        
        return "\n\n".join(formatted_chunks)
    
    def get_template_info(self, template_name: str) -> Optional[PromptTemplate]:
        """Get information about a specific template."""
        return self.templates.get(template_name)
    
    def list_templates(self) -> List[str]:
        """List all available template names."""
        return list(self.templates.keys())
    
    def validate_template(self, template_name: str) -> bool:
        """Validate that a template exists and is properly configured."""
        return template_name in self.templates 