"""
AWIP — AI Data Science Team
Base Agent Architecture

Defines the foundational structures for the multi-agent system:
- AgentMessage: A structured message sent between agents.
- MessageBus: A central communication log for inter-agent coordination.
- BaseAgent: The abstract base class for all specialized agents.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable

@dataclass
class AgentMessage:
    """A single structured message passed between agents."""
    sender: str
    recipient: str  # e.g., "All", "Orchestrator", "ModelAgent"
    content: str
    confidence: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "content": self.content,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }

class MessageBus:
    """Central communication hub for agents."""
    
    def __init__(self):
        self.messages: List[AgentMessage] = []
        self._listeners: List[Callable[[AgentMessage], None]] = []

    def subscribe(self, listener: Callable[[AgentMessage], None]):
        """Register a callback invoked on every new message (for SSE streaming)."""
        self._listeners.append(listener)

    def publish(self, message: AgentMessage):
        """Publish a new message to the bus."""
        self.messages.append(message)
        for listener in self._listeners:
            try:
                listener(message)
            except Exception:
                pass
        
    def get_all(self) -> List[AgentMessage]:
        """Get all messages in chronological order."""
        return self.messages
        
    def get_by_sender(self, sender: str) -> List[AgentMessage]:
        """Get messages from a specific agent."""
        return [m for m in self.messages if m.sender == sender]
        
    def get_recent(self, n: int = 5) -> List[AgentMessage]:
        """Get the most recent N messages."""
        return self.messages[-n:]
        
    def clear(self):
        """Clear the message bus."""
        self.messages = []

class BaseAgent:
    """Abstract base class for all specialized AI Data Science agents."""
    
    def __init__(self, name: str, message_bus: MessageBus):
        self.name = name
        self.message_bus = message_bus
        
    def broadcast(self, content: str, confidence: float = 1.0, metadata: Dict[str, Any] = None):
        """Send a message to all agents."""
        msg = AgentMessage(
            sender=self.name,
            recipient="All",
            content=content,
            confidence=confidence,
            metadata=metadata or {}
        )
        self.message_bus.publish(msg)
        
    def send_to(self, recipient: str, content: str, confidence: float = 1.0, metadata: Dict[str, Any] = None):
        """Send a message to a specific agent."""
        msg = AgentMessage(
            sender=self.name,
            recipient=recipient,
            content=content,
            confidence=confidence,
            metadata=metadata or {}
        )
        self.message_bus.publish(msg)
        
    def execute(self, *args, **kwargs) -> Any:
        """Main execution loop for the agent. Must be implemented by subclasses."""
        raise NotImplementedError("Agents must implement the execute method.")
