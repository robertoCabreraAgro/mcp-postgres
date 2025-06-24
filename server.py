from __future__ import annotations

"""FastMCP server exposing simple Postgres operations."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from mcp.server.fastmcp import FastMCP

from db import init_db


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Initialize the database on startup."""
    init_db()
    yield


mcp = FastMCP("Postgres GPT Server", lifespan=lifespan)

# Register tool implementations
import tool  # noqa: E402

if __name__ == "__main__":
    mcp.run()
