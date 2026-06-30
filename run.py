"""
Entry point for the MSE tweet scraper.

Usage:
  # One-time historical pull from Jan 2024 onward:
  python run.py historical --since 2024-01-01

  # Incremental update (pick up from last run):
  python run.py update

Setup:
  pip install scweet
  $env:X_AUTH_TOKEN="<your_auth_token>"   # PowerShell
  export X_AUTH_TOKEN="<your_auth_token>" # bash/zsh

  To get auth_token: log into x.com → DevTools → Application →
  Cookies → https://x.com → copy the `auth_token` value.
  Use a throwaway account — heavy scraping can get an account restricted.
"""

import argparse
from scraper import historical_pull, incremental_update

parser = argparse.ArgumentParser(description="MSE tweet scraper")
sub = parser.add_subparsers(dest="mode", required=True)

hist = sub.add_parser("historical", help="Pull all tweets from a start date to today")
hist.add_argument(
    "--since",
    default="2024-01-01",
    help="Start date in YYYY-MM-DD format (default: 2024-01-01)",
)

sub.add_parser("update", help="Pull new tweets since the last recorded run")

args = parser.parse_args()

if args.mode == "historical":
    historical_pull(since=args.since)
elif args.mode == "update":
    incremental_update()
