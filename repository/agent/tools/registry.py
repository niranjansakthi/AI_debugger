from typing import Any, Dict

class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, tool: Any):
        """Register a tool by its name attribute."""
        if not hasattr(tool, 'name'):
            raise ValueError("Tool must have a 'name' attribute.")
        self._tools[tool.name] = tool

    def execute(self, tool_name: str, **kwargs) -> Any:
        """Find a tool, validate inputs, and execute it."""
        if tool_name not in self._tools:
            raise ValueError(f"Unknown tool: '{tool_name}'")

        tool = self._tools[tool_name]
        
        if hasattr(tool, 'args_schema') and tool.args_schema is not None:
            # Validate input arguments against Pydantic schema
            validated_args = tool.args_schema(**kwargs)
            # Pass validated arguments to the execute method
            return tool.execute(**validated_args.model_dump())
        else:
            return tool.execute(**kwargs)
