"""
repository/agent/llm_adapter.py

Thin adapter that wraps the Groq SDK client and makes it compatible
with the LLMClient Protocol expected by AgentRunner.

AgentRunner calls:
    response = self.llm.invoke([system_message] + state.messages)

Then uses:
    response.tool_calls      — for tool dispatch
    response.content         — for the final text answer
    response.usage           — for token tracking
    response.model           — for cost calculation
"""

import logging
import os
from typing import Any

from groq import Groq

from repository.agent.state.models import ChatMessage

logger = logging.getLogger(__name__)


class GroqAgentLLM:
    """
    Implements the LLMClient Protocol required by AgentRunner.

    Converts our internal ChatMessage list → Groq SDK message dicts,
    calls the Groq chat completions API with tool support enabled,
    and returns the raw Groq response object.

    AgentRunner._extract_tool_calls() and _extract_content() already
    know how to parse this response object.
    """

    def __init__(
        self,
        model_name: str | None = None,
        tools: list[Any] | None = None,
    ) -> None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set.")

        self.model_name = (
            model_name
            or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        )
        self.tools = tools or []
        self.client = Groq(api_key=api_key)

    def invoke(self, messages: list[ChatMessage]) -> Any:
        """
        Convert ChatMessage list to Groq format and call the API.

        Groq requires:
          - assistant messages that dispatched tools: include 'tool_calls' array
          - tool-result messages: include 'tool_call_id' matching the call
        We reconstruct these from the ChatMessage list in order.
        """
        import json as _json

        groq_messages = []
        # Ids from the most recent assistant tool_calls block, consumed in order
        # as we encounter tool-result messages.
        pending_ids: list[str] = []
        id_index = 0

        for msg in messages:
            role = msg.role.value if hasattr(msg.role, "value") else msg.role

            if role == "assistant" and msg.tool_calls:
                # Reset pending ids for the new batch of tool calls.
                pending_ids = [tc.id for tc in msg.tool_calls]
                id_index = 0
                groq_messages.append({
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": _json.dumps(tc.arguments),
                            },
                        }
                        for tc in msg.tool_calls
                    ],
                })

            elif role == "tool":
                # Match this result to the next pending tool call id.
                tcid = (
                    pending_ids[id_index]
                    if id_index < len(pending_ids)
                    else f"tool_result_{id_index}"
                )
                id_index += 1
                groq_messages.append({
                    "role": "tool",
                    "tool_call_id": tcid,
                    "content": msg.content or "",
                })

            else:
                groq_messages.append({
                    "role": role,
                    "content": msg.content or "",
                })

        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "messages": groq_messages,
        }

        if self.tools:
            groq_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": (
                            tool.args_schema.model_json_schema()
                            if hasattr(tool, "args_schema") and tool.args_schema
                            else {"type": "object", "properties": {}}
                        ),
                    },
                }
                for tool in self.tools
            ]
            kwargs["tools"] = groq_tools
            kwargs["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**kwargs)
        return _GroqResponse(response)



class _GroqResponse:
    """
    Adapter that makes the Groq completion look like what
    AgentRunner._extract_tool_calls() and _extract_content() expect.

    AgentRunner accesses:
        response.tool_calls  → list of objects with .id, .name, .arguments
        response.content     → str final text (when no tool calls)
        response.usage       → object with .prompt_tokens, .completion_tokens
        response.model       → str model name
    """

    def __init__(self, completion) -> None:
        self._completion = completion
        self._message = completion.choices[0].message

    @property
    def tool_calls(self):
        raw = getattr(self._message, "tool_calls", None)
        if not raw:
            return None
        return [_ToolCallWrapper(tc) for tc in raw]

    @property
    def content(self) -> str | None:
        return self._message.content

    @property
    def usage(self):
        return self._completion.usage

    @property
    def model(self) -> str:
        return self._completion.model


class _ToolCallWrapper:
    """Wraps a single Groq tool call to match AgentRunner's expectations."""

    def __init__(self, raw_tool_call) -> None:
        self._raw = raw_tool_call

    @property
    def id(self) -> str:
        return self._raw.id

    @property
    def name(self) -> str:
        return self._raw.function.name

    @property
    def arguments(self) -> dict:
        import json
        args = self._raw.function.arguments
        if isinstance(args, str):
            try:
                return json.loads(args)
            except json.JSONDecodeError:
                return {}
        return args or {}
