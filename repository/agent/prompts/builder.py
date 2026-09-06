from typing import Any, Dict, List

from repository.agent.prompts.system import SYSTEM_PROMPT, TOOL_USAGE_TEMPLATE
from repository.agent.state.models import ChatMessage


class PromptBuilder:
    """Builds and manages prompts for the Agent."""

    @staticmethod
    def build(goal: str, tools: List[Any] = None, conversation: List[ChatMessage] = None) -> str:
        """
        Constructs the complete prompt including system directives,
        tool descriptions, the current goal, and conversation history.
        """
        # 1. System Prompt
        prompt = SYSTEM_PROMPT.strip()

        # 2. Tool Usage
        if tools:
            tool_descriptions = PromptBuilder._format_tools(tools)
            tool_section = TOOL_USAGE_TEMPLATE.format(tool_descriptions=tool_descriptions)
            prompt += f"\n\n{tool_section.strip()}"

        # 3. Goal
        prompt += f"\n\n# Goal\n{goal}"

        # 4. Conversation History
        if conversation:
            prompt += "\n\n# Conversation History"
            for msg in conversation:
                role_label = msg.role.value.upper() if hasattr(msg.role, "value") else str(msg.role).upper()
                content = msg.content or ""
                prompt += f"\n**{role_label}**:\n{content}"

        return prompt.strip()

    @staticmethod
    def _format_tools(tools: List[Any]) -> str:
        """Formats a list of tool objects into a readable string."""
        formatted = []
        for tool in tools:
            name = getattr(tool, "name", "UnknownTool")
            desc = getattr(tool, "description", "No description provided.")
            
            args_str = ""
            if hasattr(tool, "args_schema") and tool.args_schema:
                schema_props = tool.args_schema.model_json_schema().get("properties", {})
                args = [f"{k} ({v.get('type', 'any')})" for k, v in schema_props.items()]
                args_str = f"\n  Arguments: {', '.join(args)}"

            formatted.append(f"- **{name}**: {desc}{args_str}")
            
        return "\n".join(formatted)
