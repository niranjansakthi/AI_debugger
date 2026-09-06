from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IterationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_TOOL = "awaiting_tool"
    COMPLETED = "completed"
    FAILED = "failed"
class MessageRole(str, Enum):
    USER = "user"
    SYSTEM = "system"
    TOOL = "tool"
    ASSISTANT = "assistant"
class ToolCall(BaseModel):
    id: str = Field(description="unique identifier for tool")
    name: str = Field(description="name of the tool called")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="the keyword arguments")


class Observation(BaseModel):
    tool_call_id: str = Field(description="Matches the specific tool_call id this observation answers.")
    content: str = Field(description="The raw output or string representation of the tool execution.")
    is_error: bool = Field(default=False, description="Flag indicating if the tool execution failed.")


class ChatMessage(BaseModel):
    """A individual entry in the conversation history."""
    role: MessageRole
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None


class AgentState(BaseModel):
    """The central state machine tracking an active agent execution loop."""
    goal: str = Field(description="primary objective")
    messages: List[ChatMessage] = Field(default_factory=list, description="ordered log of messages")
    tool_calls: List[ToolCall] = Field(default_factory=list, description="id to tool call mapping")
    observations: List[Observation] = Field(default_factory=list, description="observations from tools")
    iteration: int = Field(default=0)
    status: IterationStatus = Field(default=IterationStatus.PENDING)

    def add_message(self, message: ChatMessage):
        self.messages.append(message)

    def add_tool_call(self, tool_call: ToolCall):
        self.tool_calls.append(tool_call)

    def add_observation(self, observation: Observation):
        self.observations.append(observation)

    def increment_iteration(self):
        self.iteration += 1