import argparse
import asyncio

from app.bootstrap.bot_runner import run_bot_component


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the JobMonitor Telegram bot component")
    parser.add_argument(
        "--with-scraper",
        action="store_true",
        help="also start the Telethon scraper",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(run_bot_component(with_scraper=args.with_scraper))


if __name__ == "__main__":
    main()
