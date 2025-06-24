from dotenv import load_dotenv
load_dotenv()

from mcp.server.fastmcp import FastMCP
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from db import init_db

@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    init_db()
    yield

mcp = FastMCP("Postgres GPT Server", lifespan=lifespan)
