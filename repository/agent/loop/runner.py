from typing import Any, Protocol

from repository.agent.state.models import (
    AgentState,
    ChatMessage,
    IterationStatus,
    Observation,
    ToolCall,
)
from repository.agent.tools.registry import ToolRegistry


class LLMClient(Protocol):
    """Minimal interface required by AgentRunner."""

    def invoke(
        self,
        messages: list[ChatMessage],
    ) -> Any:
        ...


class AgentRunner:
    """Orchestrates the LLM -> tool -> observation loop."""

    def __init__(
        self,
        llm: LLMClient,
        tool_registry: ToolRegistry,
        max_iterations: int = 5,
    ) -> None:
        self.llm = llm
        self.tool_registry = tool_registry
        self.max_iterations = max_iterations

    def run(self, goal: str) -> AgentState:
        state = AgentState(
            goal=goal,
            status=IterationStatus.RUNNING,
        )

        state.messages.append(
            ChatMessage(
                role="user",
                content=goal,
            )
        )

        while state.iteration < self.max_iterations:
            state.iteration += 1

            try:
                response = self.llm.invoke(
                    state.messages
                )
            except Exception as exc:
                state.status = IterationStatus.FAILED

                state.observations.append(
                    Observation(
                        tool_call_id="llm_error",
                        content=str(exc),
                        is_error=True,
                    )
                )

                return state

            tool_calls = self._extract_tool_calls(response)

            if not tool_calls:
                final_content = self._extract_content(response)

                state.messages.append(
                    ChatMessage(
                        role="assistant",
                        content=final_content,
                    )
                )

                state.status = IterationStatus.COMPLETED

                return state

            state.status = IterationStatus.AWAITING_TOOL

            for tool_call in tool_calls:
                state.tool_calls.append(tool_call)

                try:
                    tool_result = self.tool_registry.execute(
                        tool_call.id,
                        tool_call.name,
                        **tool_call.arguments
                    )

                    observation = Observation(
                        tool_call_id=tool_result.tool_call_id,
                        content=tool_result.content if tool_result.success else str(tool_result.error),
                        is_error=not tool_result.success,
                    )

                except Exception as exc:
                    observation = Observation(
                        tool_call_id=tool_call.id,
                        content=str(exc),
                        is_error=True,
                    )

                state.observations.append(observation)

                state.messages.append(
                    ChatMessage(
                        role="tool",
                        content=observation.content,
                    )
                )

            state.status = IterationStatus.RUNNING

        state.status = IterationStatus.FAILED

        state.observations.append(
            Observation(
                tool_call_id="max_iterations",
                content=(
                    f"Agent stopped after reaching "
                    f"the maximum of {self.max_iterations} iterations."
                ),
                is_error=True,
            )
        )

        return state

    def _extract_tool_calls(
        self,
        response: Any,
    ) -> list[ToolCall]:
        """
        Convert the provider-specific response into our
        internal ToolCall representation.
        """

        raw_tool_calls = getattr(
            response,
            "tool_calls",
            None,
        )

        if not raw_tool_calls:
            return []

        tool_calls = []

        for index, raw_call in enumerate(raw_tool_calls):
            tool_calls.append(
                ToolCall(
                    id=getattr(
                        raw_call,
                        "id",
                        f"tool_call_{index}",
                    ),
                    name=raw_call.name,
                    arguments=raw_call.arguments or {},
                )
            )

        return tool_calls

    def _extract_content(
        self,
        response: Any,
    ) -> str:
        """Extract final textual content from the LLM response."""

        content = getattr(
            response,
            "content",
            response,
        )

        return str(content)