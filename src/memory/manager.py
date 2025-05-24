import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import networkx as nx
from pathlib import Path
import aiofiles
import gzip
import shutil
from fastapi.encoders import jsonable_encoder

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(
        self,
        retention_days: int = 365,  # 1 year active retention
        archive_days: int = 730,    # 2 years total retention
        max_conversation_history: int = 1000,
        compression_threshold: int = 1024 * 50,  # 50KB
        importance_threshold: float = 0.5
    ):
        # Initialize directories
        self.data_dir = Path("/app/data/memory")
        self.archive_dir = Path("/app/data/memory_archive")
        self.important_dir = Path("/app/data/memory_important")  # New directory for important memories
        
        # Create directories
        for directory in [self.data_dir, self.archive_dir, self.important_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.retention_days = retention_days
        self.archive_days = archive_days
        self.max_conversation_history = max_conversation_history
        self.compression_threshold = compression_threshold
        self.importance_threshold = importance_threshold
        
        # Initialize memory graph
        self.memory_graph = nx.DiGraph()
        
        # Background task
        self.cleanup_task = None
        
        # Load existing memories
        self._load_memories()
        
        # Start background cleanup task
        self.cleanup_task = asyncio.create_task(self._periodic_cleanup())

    async def store_interaction(
        self,
        conversation_id: str,
        user_message: str,
        ai_response: str,
        context: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Store a new interaction in memory"""
        try:
            if timestamp is None:
                timestamp = datetime.utcnow()

            # Create memory entry
            memory_entry = {
                "conversation_id": conversation_id,
                "user_message": user_message,
                "ai_response": ai_response,
                "context": context or {},
                "timestamp": timestamp.isoformat(),
            }

            # Convert to JSON-serializable format
            memory_entry = jsonable_encoder(memory_entry)

            # Save to file system
            conversation_file = self.data_dir / f"conversation_{conversation_id}.json"
            
            existing_entries = []
            if conversation_file.exists():
                async with aiofiles.open(conversation_file, "r") as f:
                    content = await f.read()
                    existing_entries = json.loads(content)
            
            # Enforce maximum history limit
            existing_entries = existing_entries[-(self.max_conversation_history - 1):]
            existing_entries.append(memory_entry)
            
            # Check if compression is needed
            content = json.dumps(existing_entries, indent=2)
            if len(content.encode()) > self.compression_threshold:
                # Save compressed file
                compressed_file = conversation_file.with_suffix('.json.gz')
                with gzip.open(compressed_file, 'wt', encoding='utf-8') as f:
                    f.write(content)
                # Remove original if it exists
                if conversation_file.exists():
                    conversation_file.unlink()
            else:
                # Save uncompressed
                async with aiofiles.open(conversation_file, "w") as f:
                    await f.write(content)

            # Update memory graph
            await self._update_memory_graph(memory_entry)
            
            logger.debug(f"Successfully stored interaction for conversation {conversation_id}")
        except Exception as e:
            logger.error(f"Error storing interaction: {str(e)}", exc_info=True)
            raise

    async def get_context(
        self,
        conversation_id: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """Retrieve relevant context for a conversation"""
        try:
            context = {
                "recent_interactions": [],
                "related_memories": []
            }

            # Get recent interactions from the same conversation
            conversation_file = self.data_dir / f"conversation_{conversation_id}.json"
            compressed_file = conversation_file.with_suffix('.json.gz')
            
            if compressed_file.exists():
                with gzip.open(compressed_file, 'rt', encoding='utf-8') as f:
                    interactions = json.load(f)
                    context["recent_interactions"] = interactions[-limit:]
            elif conversation_file.exists():
                async with aiofiles.open(conversation_file, "r") as f:
                    content = await f.read()
                    interactions = json.loads(content)
                    context["recent_interactions"] = interactions[-limit:]

            # Get related memories from the graph
            if conversation_id in self.memory_graph:
                # Get most relevant related conversations using PageRank
                pagerank = nx.pagerank(self.memory_graph)
                related_nodes = sorted(
                    [(node, pagerank[node]) for node in nx.neighbors(self.memory_graph, conversation_id)],
                    key=lambda x: x[1],
                    reverse=True
                )
                
                for node, _ in related_nodes[:limit]:
                    node_file = self.data_dir / f"conversation_{node}.json"
                    compressed_node_file = node_file.with_suffix('.json.gz')
                    
                    if compressed_node_file.exists():
                        with gzip.open(compressed_node_file, 'rt', encoding='utf-8') as f:
                            memories = json.load(f)
                            context["related_memories"].extend(memories[-1:])
                    elif node_file.exists():
                        async with aiofiles.open(node_file, "r") as f:
                            content = await f.read()
                            memories = json.loads(content)
                            context["related_memories"].extend(memories[-1:])

            return context
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}", exc_info=True)
            raise

    async def _load_memories(self) -> None:
        """Load existing memories into the graph"""
        try:
            # Load regular JSON files
            for memory_file in self.data_dir.glob("conversation_*.json"):
                async with aiofiles.open(memory_file, "r") as f:
                    content = await f.read()
                    memories = json.loads(content)
                    for memory in memories:
                        await self._update_memory_graph(memory)
            
            # Load compressed files
            for compressed_file in self.data_dir.glob("conversation_*.json.gz"):
                with gzip.open(compressed_file, 'rt', encoding='utf-8') as f:
                    memories = json.load(f)
                    for memory in memories:
                        await self._update_memory_graph(memory)
            
            logger.info(f"Loaded {len(self.memory_graph.nodes)} conversations into memory graph")
        except Exception as e:
            logger.error(f"Error loading memories: {str(e)}", exc_info=True)
            raise

    async def _update_memory_graph(self, memory_entry: Dict[str, Any]) -> None:
        """Update the memory graph with new information"""
        try:
            conversation_id = memory_entry["conversation_id"]
            
            # Add node if it doesn't exist
            if conversation_id not in self.memory_graph:
                self.memory_graph.add_node(
                    conversation_id,
                    timestamp=memory_entry["timestamp"]
                )

            # Extract key topics or entities from the interaction
            topics = await self._extract_topics(memory_entry)
            
            # Create edges between related conversations
            for existing_node in list(self.memory_graph.nodes):  # Create a list to avoid modification during iteration
                if existing_node != conversation_id:
                    existing_topics = self.memory_graph.nodes[existing_node].get("topics", set())
                    common_topics = topics.intersection(existing_topics)
                    if common_topics:
                        # Calculate similarity score based on common topics
                        similarity = len(common_topics) / len(topics.union(existing_topics))
                        self.memory_graph.add_edge(
                            conversation_id,
                            existing_node,
                            weight=similarity
                        )

            # Update node attributes
            self.memory_graph.nodes[conversation_id]["topics"] = topics
            self.memory_graph.nodes[conversation_id]["last_updated"] = memory_entry["timestamp"]
        except Exception as e:
            logger.error(f"Error updating memory graph: {str(e)}", exc_info=True)
            raise

    async def _extract_topics(self, memory_entry: Dict[str, Any]) -> set:
        """Extract key topics from an interaction using simple NLP"""
        try:
            topics = set()
            
            # Extract words from user message and AI response
            text = f"{memory_entry['user_message']} {memory_entry['ai_response']}"
            
            # Use spaCy for better topic extraction (you'll need to add spaCy to requirements.txt)
            import spacy
            
            # Load the appropriate language model based on content
            if any(char in text for char in 'áéíóúñ¿¡'):
                nlp = spacy.load('es_core_news_sm')
            elif any(char in text for char in 'äöüß'):
                nlp = spacy.load('de_core_news_sm')
            else:
                nlp = spacy.load('en_core_web_sm')
            
            doc = nlp(text)
            
            # Extract named entities
            for ent in doc.ents:
                topics.add(ent.text.lower())
            
            # Extract noun phrases
            for chunk in doc.noun_chunks:
                topics.add(chunk.text.lower())
            
            # Extract important words (nouns, verbs, adjectives)
            important_pos = {'NOUN', 'VERB', 'ADJ'}
            topics.update(token.text.lower() for token in doc if token.pos_ in important_pos)
            
            return topics
        except Exception as e:
            logger.error(f"Error extracting topics: {str(e)}", exc_info=True)
            # Fallback to simple word extraction
            text = f"{memory_entry['user_message']} {memory_entry['ai_response']}"
            words = text.lower().split()
            stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
            return {word for word in words if word not in stopwords and len(word) > 3}

    async def forget_conversation(self, conversation_id: str) -> None:
        """Remove a conversation from memory"""
        try:
            # Remove files
            conversation_file = self.data_dir / f"conversation_{conversation_id}.json"
            compressed_file = conversation_file.with_suffix('.json.gz')
            
            for file in [conversation_file, compressed_file]:
                if file.exists():
                    file.unlink()
            
            # Remove from graph
            if conversation_id in self.memory_graph:
                self.memory_graph.remove_node(conversation_id)
            
            logger.info(f"Successfully removed conversation {conversation_id}")
        except Exception as e:
            logger.error(f"Error removing conversation: {str(e)}", exc_info=True)
            raise

    async def cleanup_old_conversations(self) -> None:
        """
        Sophisticated cleanup of conversations with importance-based retention
        """
        try:
            current_time = datetime.utcnow()
            active_cutoff = current_time - timedelta(days=self.retention_days)
            archive_cutoff = current_time - timedelta(days=self.archive_days)
            
            # Process conversations in the graph
            nodes_to_archive = []
            nodes_to_remove = []
            
            for node in self.memory_graph.nodes:
                node_data = self.memory_graph.nodes[node]
                last_updated = datetime.fromisoformat(
                    node_data["last_updated"].replace('Z', '+00:00')
                )
                
                # Calculate importance score
                importance_score = await self._calculate_conversation_importance(node)
                
                if last_updated < archive_cutoff:
                    if importance_score >= self.importance_threshold:
                        # Keep important conversations in special storage
                        await self._preserve_important_conversation(node)
                    else:
                        nodes_to_remove.append(node)
                elif last_updated < active_cutoff:
                    if importance_score < self.importance_threshold:
                        nodes_to_archive.append(node)
            
            # Archive conversations
            for node in nodes_to_archive:
                await self._archive_conversation(node)
            
            # Remove old conversations
            for node in nodes_to_remove:
                await self.forget_conversation(node)
            
            # Process files in directories
            await self._process_directory_cleanup(
                active_cutoff,
                archive_cutoff
            )
            
            logger.info(
                f"Memory cleanup complete: "
                f"Archived {len(nodes_to_archive)} conversations, "
                f"Removed {len(nodes_to_remove)} conversations"
            )
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}", exc_info=True)
            raise

    async def _calculate_conversation_importance(self, node_id: str) -> float:
        """
        Calculate importance score for a conversation based on multiple factors:
        - Interaction frequency
        - Topic significance
        - User engagement
        - Reference count from other conversations
        """
        try:
            importance_score = 0.0
            node_data = self.memory_graph.nodes[node_id]
            
            # Factor 1: Topic significance (based on topic weights)
            topics = node_data.get("topics", set())
            topic_score = sum(self._get_topic_weight(topic) for topic in topics) / max(len(topics), 1)
            importance_score += topic_score * 0.3  # 30% weight
            
            # Factor 2: Reference count (how many other conversations link to this)
            reference_count = len(list(self.memory_graph.predecessors(node_id)))
            reference_score = min(reference_count / 10.0, 1.0)  # Normalize to 0-1
            importance_score += reference_score * 0.25  # 25% weight
            
            # Factor 3: Interaction depth (based on conversation length)
            conv_file = self.data_dir / f"conversation_{node_id}.json"
            conv_file_gz = conv_file.with_suffix('.json.gz')
            
            interaction_count = 0
            if conv_file.exists():
                async with aiofiles.open(conv_file, 'r') as f:
                    content = await f.read()
                    interaction_count = len(json.loads(content))
            elif conv_file_gz.exists():
                with gzip.open(conv_file_gz, 'rt') as f:
                    interaction_count = len(json.loads(f.read()))
            
            interaction_score = min(interaction_count / 20.0, 1.0)  # Normalize to 0-1
            importance_score += interaction_score * 0.25  # 25% weight
            
            # Factor 4: Recency of references
            recent_refs = 0
            current_time = datetime.utcnow()
            for pred in self.memory_graph.predecessors(node_id):
                pred_time = datetime.fromisoformat(
                    self.memory_graph.nodes[pred]["last_updated"].replace('Z', '+00:00')
                )
                if (current_time - pred_time).days < 90:  # References in last 90 days
                    recent_refs += 1
            
            recency_score = min(recent_refs / 5.0, 1.0)  # Normalize to 0-1
            importance_score += recency_score * 0.2  # 20% weight
            
            return importance_score
            
        except Exception as e:
            logger.error(f"Error calculating importance score: {str(e)}", exc_info=True)
            return 0.0

    def _get_topic_weight(self, topic: str) -> float:
        """
        Calculate weight/importance of a topic
        This could be enhanced with a proper topic importance database
        """
        # Example weights for different topic categories
        topic_weights = {
            'personal': 0.9,
            'project': 0.8,
            'technical': 0.7,
            'business': 0.7,
            'meeting': 0.6,
            'general': 0.4
        }
        
        # Simple matching - could be enhanced with NLP
        for category, weight in topic_weights.items():
            if category in topic.lower():
                return weight
        
        return 0.5  # Default weight

    async def _preserve_important_conversation(self, node_id: str) -> None:
        """Save important conversations to special storage"""
        try:
            source_file = self.data_dir / f"conversation_{node_id}.json"
            source_file_gz = source_file.with_suffix('.json.gz')
            target_file = self.important_dir / f"conversation_{node_id}.json.gz"
            
            # Compress and move to important storage
            if source_file.exists() or source_file_gz.exists():
                content = None
                if source_file.exists():
                    async with aiofiles.open(source_file, 'r') as f:
                        content = await f.read()
                elif source_file_gz.exists():
                    with gzip.open(source_file_gz, 'rt') as f:
                        content = f.read()
                
                if content:
                    with gzip.open(target_file, 'wt') as f:
                        f.write(content)
                    
                    # Remove original files
                    if source_file.exists():
                        source_file.unlink()
                    if source_file_gz.exists():
                        source_file_gz.unlink()
                    
                    logger.info(f"Preserved important conversation {node_id}")
        
        except Exception as e:
            logger.error(f"Error preserving important conversation: {str(e)}", exc_info=True)

    async def _archive_conversation(self, node_id: str) -> None:
        """Archive a conversation"""
        try:
            source_file = self.data_dir / f"conversation_{node_id}.json"
            source_file_gz = source_file.with_suffix('.json.gz')
            target_file = self.archive_dir / f"conversation_{node_id}.json.gz"
            
            if source_file.exists() or source_file_gz.exists():
                content = None
                if source_file.exists():
                    async with aiofiles.open(source_file, 'r') as f:
                        content = await f.read()
                elif source_file_gz.exists():
                    with gzip.open(source_file_gz, 'rt') as f:
                        content = f.read()
                
                if content:
                    with gzip.open(target_file, 'wt') as f:
                        f.write(content)
                    
                    # Remove original files
                    if source_file.exists():
                        source_file.unlink()
                    if source_file_gz.exists():
                        source_file_gz.unlink()
                    
                    logger.info(f"Archived conversation {node_id}")
        
        except Exception as e:
            logger.error(f"Error archiving conversation: {str(e)}", exc_info=True)

    async def _process_directory_cleanup(
        self,
        active_cutoff: datetime,
        archive_cutoff: datetime
    ) -> None:
        """Process cleanup of files in directories"""
        try:
            # Process each directory
            for dir_path in [self.data_dir, self.archive_dir]:
                for file_pattern in ["*.json", "*.json.gz"]:
                    for file in dir_path.glob(file_pattern):
                        try:
                            # Get file modification time
                            mod_time = datetime.fromtimestamp(file.stat().st_mtime)
                            
                            # Calculate importance if needed
                            importance = 0.0
                            if mod_time < archive_cutoff:
                                conversation_id = file.stem.replace('conversation_', '')
                                importance = await self._calculate_conversation_importance(conversation_id)
                            
                            # Process based on age and importance
                            if mod_time < archive_cutoff:
                                if importance >= self.importance_threshold:
                                    # Preserve important conversations
                                    await self._preserve_important_conversation(
                                        file.stem.replace('conversation_', '')
                                    )
                                else:
                                    # Remove old unimportant conversations
                                    file.unlink()
                            elif mod_time < active_cutoff:
                                # Archive older conversations
                                await self._archive_conversation(
                                    file.stem.replace('conversation_', '')
                                )
                            
                        except Exception as e:
                            logger.error(f"Error processing file {file}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error in directory cleanup: {str(e)}", exc_info=True)

    async def _periodic_cleanup(self) -> None:
        """Run periodic cleanup of conversations"""
        while True:
            try:
                # Run cleanup daily
                await asyncio.sleep(24 * 60 * 60)
                
                # Run cleanup with error handling
                try:
                    await self.cleanup_old_conversations()
                except Exception as e:
                    logger.error(f"Error during cleanup: {str(e)}", exc_info=True)
                
                # Optional: Run deep analysis less frequently
                if datetime.utcnow().day == 1:  # First day of month
                    await self._run_deep_analysis()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {str(e)}", exc_info=True)
                await asyncio.sleep(60)  # Wait before retrying

    async def _run_deep_analysis(self) -> None:
        """
        Monthly deep analysis of conversation patterns and importance
        """
        try:
            # Analyze conversation patterns
            total_conversations = len(self.memory_graph.nodes)
            important_conversations = sum(
                1 for node in self.memory_graph.nodes
                if await self._calculate_conversation_importance(node) >= self.importance_threshold
            )
            
            # Calculate usage patterns
            usage_patterns = await self._analyze_usage_patterns()
            
            # Log analysis results
            logger.info(
                f"Monthly Analysis:\n"
                f"Total Conversations: {total_conversations}\n"
                f"Important Conversations: {important_conversations}\n"
                f"Usage Patterns: {usage_patterns}"
            )
            
        except Exception as e:
            logger.error(f"Error in deep analysis: {str(e)}", exc_info=True)

    async def _analyze_usage_patterns(self) -> Dict[str, Any]:
        """
        Analyze conversation patterns and usage statistics
        """
        try:
            patterns = {
                "total_conversations": len(self.memory_graph.nodes),
                "active_users": set(),
                "popular_topics": {},
                "avg_conversation_length": 0,
                "peak_usage_times": {}
            }
            
            total_messages = 0
            conversations_analyzed = 0
            
            for node in self.memory_graph.nodes:
                try:
                    conv_file = self.data_dir / f"conversation_{node_id}.json"
                    conv_file_gz = conv_file.with_suffix('.json.gz')
                    
                    content = None
                    if conv_file.exists():
                        async with aiofiles.open(conv_file, 'r') as f:
                            content = await f.read()
                    elif conv_file_gz.exists():
                        with gzip.open(conv_file_gz, 'rt') as f:
                            content = f.read()
                    
                    if content:
                        conversations = json.loads(content)
                        total_messages += len(conversations)
                        conversations_analyzed += 1
                        
                        # Analyze topics
                        for topic in self.memory_graph.nodes[node].get("topics", set()):
                            patterns["popular_topics"][topic] = patterns["popular_topics"].get(topic, 0) + 1
                        
                except Exception as e:
                    logger.error(f"Error analyzing conversation {node}: {str(e)}")
            
            # Calculate averages
            if conversations_analyzed > 0:
                patterns["avg_conversation_length"] = total_messages / conversations_analyzed
            
            # Sort and limit popular topics
            patterns["popular_topics"] = dict(
                sorted(
                    patterns["popular_topics"].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            )
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing usage patterns: {str(e)}", exc_info=True)
            return {}