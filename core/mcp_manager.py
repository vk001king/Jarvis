"""MCP server configuration, connections, and Gemini tool dispatch."""
from __future__ import annotations

import asyncio
import json
import os
import re
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{1,48}$")
_MAX_TOOL_RESULT = 30_000
_BASE_ENV_KEYS = {
    "APPDATA", "COMSPEC", "HOME", "LANG", "LC_ALL", "LC_CTYPE",
    "LOCALAPPDATA", "PATH", "PATHEXT", "PROGRAMDATA", "PROGRAMFILES",
    "PROGRAMFILES(X86)", "SYSTEMROOT", "TEMP", "TMP", "TMPDIR", "USERPROFILE",
    "WINDIR", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_RUNTIME_DIR",
}


def _gemini_schema(schema: Any) -> dict:
    """Convert MCP JSON Schema into the subset accepted by Gemini tools."""
    if not isinstance(schema, dict):
        return {"type": "OBJECT", "properties": {}}

    def convert(node: Any) -> dict:
        if not isinstance(node, dict):
            return {"type": "STRING"}
        out: dict[str, Any] = {}
        schema_type = node.get("type")
        if isinstance(schema_type, str):
            out["type"] = schema_type.upper()
        if isinstance(node.get("description"), str):
            out["description"] = node["description"]
        if isinstance(node.get("enum"), list):
            out["enum"] = node["enum"]
        if isinstance(node.get("properties"), dict):
            out["properties"] = {
                str(key): convert(value)
                for key, value in node["properties"].items()
            }
        if isinstance(node.get("items"), dict):
            out["items"] = convert(node["items"])
        if isinstance(node.get("required"), list):
            out["required"] = [str(item) for item in node["required"]]
        if "type" not in out:
            out["type"] = "OBJECT" if "properties" in out else "STRING"
        return out

    converted = convert(schema)
    if converted.get("type") != "OBJECT":
        return {"type": "OBJECT", "properties": {}}
    return converted


class MCPManager:
    """Maintain configured MCP connections and expose their tools to Gemini."""

    def __init__(self, config_path: Path, logger=print, reserved_names: set[str] | None = None):
        self._config_path = config_path
        self._logger = logger
        self._reserved_names = reserved_names or set()
        self._servers: list[dict] = self._load_config()
        self._connections: dict[str, dict] = {}
        self._tools: dict[str, tuple[str, str]] = {}
        self._states: dict[str, dict] = {}

    def _load_config(self) -> list[dict]:
        if not self._config_path.exists():
            return []
        try:
            data = json.loads(self._config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self._logger(f"[MCP] Could not read {self._config_path}: {exc}")
            return []
        servers = data.get("servers", []) if isinstance(data, dict) else []
        if not isinstance(servers, list):
            self._logger("[MCP] Invalid server configuration: 'servers' must be a list.")
            return []
        valid = []
        for server in servers:
            try:
                valid.append(self._validate_server(server))
            except ValueError as exc:
                name = server.get("name", "unknown") if isinstance(server, dict) else "unknown"
                self._logger(f"[MCP] Skipping server {name}: {exc}")
        return valid

    @staticmethod
    def _validate_server(server: Any) -> dict:
        if not isinstance(server, dict):
            raise ValueError("configuration must be an object")
        name = str(server.get("name", "")).strip()
        if not _NAME_RE.fullmatch(name):
            raise ValueError("name must contain 1-48 letters, digits, underscores, or hyphens")
        transport = str(server.get("transport", "")).strip().lower()
        if transport not in ("stdio", "http"):
            raise ValueError("transport must be 'stdio' or 'http'")
        enabled = bool(server.get("enabled", True))
        clean: dict[str, Any] = {"name": name, "transport": transport, "enabled": enabled}

        if transport == "stdio":
            command = server.get("command")
            args = server.get("args", [])
            env = server.get("env", {})
            if not isinstance(command, str) or not command.strip():
                raise ValueError("stdio servers require a command")
            if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
                raise ValueError("stdio args must be a list of strings")
            if not isinstance(env, dict) or not all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in env.items()
            ):
                raise ValueError("stdio env must be an object of string values")
            clean.update(command=command.strip(), args=args, env=env)
        else:
            url = server.get("url")
            headers = server.get("headers", {})
            if not isinstance(url, str) or urlparse(url).scheme not in ("http", "https"):
                raise ValueError("HTTP servers require an http:// or https:// URL")
            if not isinstance(headers, dict) or not all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in headers.items()
            ):
                raise ValueError("HTTP headers must be an object of string values")
            clean.update(url=url.strip(), headers=headers)
        return clean

    def list_for_ui(self) -> list[dict]:
        """Return server state without exposing configured environment or headers."""
        out = []
        for server in self._servers:
            state = self._states.get(server["name"], {})
            out.append({
                "name": server["name"],
                "transport": server["transport"],
                "enabled": server["enabled"],
                "connected": bool(state.get("connected")),
                "tools": int(state.get("tools", 0)),
                "error": str(state.get("error", "")),
            })
        return out

    def get_config(self) -> list[dict]:
        """Return a copy for the manager UI; secret fields stay in memory only."""
        return json.loads(json.dumps(self._servers))

    async def connect_all(self) -> None:
        for server in self._servers:
            if server["enabled"] and server["name"] not in self._connections:
                await self._connect(server)

    async def configure(self, servers: list[dict]) -> None:
        if not isinstance(servers, list):
            raise ValueError("MCP server configuration must be a list.")
        validated = [self._validate_server(server) for server in servers]
        names = [server["name"].casefold() for server in validated]
        if len(set(names)) != len(names):
            raise ValueError("MCP server names must be unique.")

        # Atomic, and readable only by this user: the file carries whatever
        # tokens the servers were given in their env blocks.
        from core.safe_io import write_json
        write_json(self._config_path, {"servers": validated}, indent=2)
        await self._disconnect_all()
        self._servers = validated
        self._states = {}
        await self.connect_all()

    async def _connect(self, server: dict) -> None:
        name = server["name"]
        stack = AsyncExitStack()
        try:
            await stack.__aenter__()
            if server["transport"] == "stdio":
                from mcp import StdioServerParameters
                from mcp.client.stdio import stdio_client

                params = StdioServerParameters(
                    command=server["command"],
                    args=server["args"],
                    env={
                        **{
                            key: value for key, value in os.environ.items()
                            if key.upper() in _BASE_ENV_KEYS
                        },
                        **server["env"],
                    },
                )
                read_stream, write_stream = await stack.enter_async_context(
                    stdio_client(params)
                )
            else:
                from mcp.client.streamable_http import streamablehttp_client

                read_stream, write_stream, _session_id = await stack.enter_async_context(
                    streamablehttp_client(
                        server["url"],
                        headers=server["headers"] or None,
                        timeout=15,
                    )
                )

            from mcp import ClientSession

            session = await stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await asyncio.wait_for(session.initialize(), timeout=20)
            response = await asyncio.wait_for(session.list_tools(), timeout=20)

            tools: dict[str, tuple[str, str]] = {}
            declarations = []
            for tool in response.tools:
                raw_name = str(tool.name)
                tool_name = re.sub(r"[^a-zA-Z0-9_]", "_", raw_name).strip("_")
                if not tool_name:
                    self._logger(f"[MCP] Ignoring unnamed tool from {name}.")
                    continue
                prefix = "mcp_" + re.sub(r"[^a-zA-Z0-9_]", "_", name)
                full_name = f"{prefix}_{tool_name}"
                full_name = full_name[:64]
                if (full_name in self._reserved_names
                        or full_name in self._tools or full_name in tools):
                    self._logger(f"[MCP] Ignoring colliding tool name {full_name}.")
                    continue
                tools[full_name] = (name, raw_name)
                description = str(tool.description or "").strip()
                declarations.append({
                    "name": full_name,
                    "description": (
                        f"MCP server '{name}' tool '{raw_name}'. {description}"
                    ).strip(),
                    "parameters": _gemini_schema(tool.inputSchema),
                })

            self._connections[name] = {
                "stack": stack,
                "session": session,
                "declarations": declarations,
                "tools": tools,
            }
            self._tools.update(tools)
            self._states[name] = {"connected": True, "tools": len(tools), "error": ""}
            self._logger(f"[MCP] Connected to {name}: {len(tools)} tool(s).")
        except Exception as exc:
            await stack.aclose()
            self._states[name] = {
                "connected": False,
                "tools": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            self._logger(f"[MCP] Could not connect to {name}: {exc}")

    async def _disconnect_all(self) -> None:
        connections = list(self._connections.values())
        self._connections.clear()
        self._tools.clear()
        for connection in connections:
            try:
                await connection["stack"].aclose()
            except Exception as exc:
                self._logger(f"[MCP] Error closing server connection: {exc}")

    def get_tool_declarations(self) -> list[dict]:
        return [
            declaration
            for connection in self._connections.values()
            for declaration in connection["declarations"]
        ]

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    async def call_tool(self, name: str, arguments: dict) -> str:
        target = self._tools.get(name)
        if target is None:
            return f"MCP tool '{name}' is not connected."
        server_name, tool_name = target
        connection = self._connections.get(server_name)
        if connection is None:
            return f"MCP server '{server_name}' is disconnected."
        try:
            result = await asyncio.wait_for(
                connection["session"].call_tool(tool_name, arguments),
                timeout=60,
            )
        except Exception as exc:
            self._logger(f"[MCP] Tool {name} failed: {exc}")
            self._states[server_name] = {
                **self._states.get(server_name, {}),
                "error": f"{type(exc).__name__}: {exc}",
            }
            return f"MCP tool '{name}' failed: {exc}"

        if getattr(result, "isError", False):
            content = getattr(result, "content", [])
            text = "\n".join(
                str(getattr(item, "text", ""))
                for item in content
                if getattr(item, "text", None)
            )
            return f"MCP tool error: {text or 'The server reported an error.'}"[:_MAX_TOOL_RESULT]

        structured = getattr(result, "structuredContent", None)
        if structured is not None:
            rendered = json.dumps(structured, ensure_ascii=False, default=str)
        else:
            parts = []
            for item in getattr(result, "content", []):
                text = getattr(item, "text", None)
                if text:
                    parts.append(str(text))
                elif getattr(item, "type", "") == "image":
                    parts.append("[An image was returned by the MCP server.]")
            rendered = "\n".join(parts) or "The MCP tool completed without text output."
        if len(rendered) > _MAX_TOOL_RESULT:
            rendered = rendered[:_MAX_TOOL_RESULT] + "\n[Output truncated.]"
        return rendered
