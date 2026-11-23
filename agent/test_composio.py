"""Minimal verification script for Composio API Key."""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

key = sys.argv[1] if len(sys.argv) > 1 else os.getenv("COMPOSIO_API_KEY")

if not key:
    print("Error: No COMPOSIO_API_KEY provided.")
    sys.exit(1)

print(f"Testing Composio API Key: {key[:8]}...{key[-4:] if len(key)>12 else ''}")

try:
    from composio import Composio
    client = Composio(api_key=key)
    res = client.connected_accounts.list()
    print("SUCCESS: Composio API Key is valid and authenticated!")
    print(f"Connected accounts count: {len(res.items)}")
except Exception as e:
    print(f"FAILED: Composio authentication error: {e}")
    sys.exit(1)
