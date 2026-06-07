"""CLI entry point."""

from __future__ import annotations

import argparse
import logging
import sys

import uvicorn

from wallet_intelligence.core.config import settings


def main():
    parser = argparse.ArgumentParser(description="Wallet Intelligence CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start the API server")
    serve_parser.add_argument("--host", default=settings.host, help="Bind host")
    serve_parser.add_argument("--port", type=int, default=settings.port, help="Bind port")
    serve_parser.add_argument("--reload", action="store_true", help="Auto-reload on changes")
    serve_parser.add_argument("--workers", type=int, default=1, help="Number of workers")

    # Init DB command
    subparsers.add_parser("init-db", help="Initialize database tables")

    args = parser.parse_args()

    if args.command == "serve":
        logging.basicConfig(level=logging.INFO)
        uvicorn.run(
            "wallet_intelligence.app:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers,
        )
    elif args.command == "init-db":
        import asyncio
        from wallet_intelligence.core.database import init_db
        asyncio.run(init_db())
        print("Database initialized.")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
