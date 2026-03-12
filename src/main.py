"""Main entry point — run the FastAPI server."""

import uvicorn

from .config import settings


def main():
    uvicorn.run(
        "src.api.server:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
