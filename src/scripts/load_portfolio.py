import argparse
import logging

from dotenv import load_dotenv

from scripts.portfolio.portfolio_ingestion import PortfolioIngest

logging.basicConfig(
    level=logging.INFO,  # Use INFO level to see all sync progress logs
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

load_dotenv()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synchronize portfolio data from Notion")
    parser.add_argument(
        "--since",
        type=str,
        help="ISO 8601 date to sync from (e.g. 2024-01-01T00:00:00.000Z). If not provided, uses last sync date.",
    )
    args = parser.parse_args()

    orchestrator = PortfolioIngest()
    orchestrator.sync(args.since)
