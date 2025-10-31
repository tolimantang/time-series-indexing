"""
Base class for all MCP tools.

Provides consistent interface and validation for financial analysis tools.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, date
import json
import logging

logger = logging.getLogger(__name__)


class BaseMCPTool(ABC):
    """Abstract base class for MCP tools."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Return the JSON schema for this tool's parameters.

        This schema will be provided to the LLM so it knows how to call the tool.
        """
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with the provided parameters.

        Args:
            **kwargs: Tool parameters validated against the schema

        Returns:
            Dict containing tool execution results
        """
        pass

    def validate_params(self, **kwargs) -> bool:
        """
        Validate parameters against the schema.

        Args:
            **kwargs: Parameters to validate

        Returns:
            True if valid, raises ValueError if invalid
        """
        # Basic validation - subclasses can override for more specific validation
        schema = self.get_schema()
        required_params = schema.get('required', [])

        for param in required_params:
            if param not in kwargs:
                raise ValueError(f"Missing required parameter: {param}")

        return True

    def _parse_date(self, date_str: str) -> date:
        """Parse date string in YYYY-MM-DD format."""
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD")

    def _format_result(self,
                      success: bool,
                      data: Any = None,
                      error: str = None,
                      metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Format tool execution result in consistent format."""
        result = {
            'tool_name': self.name,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }

        if success:
            result['data'] = data
            if metadata:
                result['metadata'] = metadata
        else:
            result['error'] = error

        return result


class ToolRegistry:
    """Registry for managing available MCP tools."""

    def __init__(self):
        self._tools: Dict[str, BaseMCPTool] = {}

    def register(self, tool: BaseMCPTool):
        """Register a tool."""
        self._tools[tool.name] = tool
        logger.info(f"Registered MCP tool: {tool.name}")

    def get_tool(self, name: str) -> Optional[BaseMCPTool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def get_all_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Get schemas for all registered tools."""
        return {name: tool.get_schema() for name, tool in self._tools.items()}


# Global tool registry
tool_registry = ToolRegistry()