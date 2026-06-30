"""
Scweet connectivity + MSE-volume test.
Run locally (NOT in a sandbox — needs to reach x.com).

Setup:
  pip install scweet
  Get auth_token: log into x.com on a THROWAWAY account ->
    devtools -> Application -> Cookies -> https://x.com -> copy `auth_token` value.
  Set it as an env var so it isn't hardcoded:
    Mac/Linux:  export X_AUTH_TOKEN="your_auth_token_here"
    PowerShell: $env:X_AUTH_TOKEN="your_auth_token_here"

Then: python3 scweet_test.py
"""
import os
import sys
sys.stdout.reconfigure(encoding="utf-8")
from Scweet import Scweet  # v5.3+: top-level export. NOT Scweet.scweet

AUTH = os.environ.get("X_AUTH_TOKEN")
if not AUTH:
    raise SystemExit("Set X_AUTH_TOKEN env var first.")

# manifest_scrape_on_init self-heals doc_ids/feature flags from X's main.js at startup
s = Scweet(auth_token=AUTH, manifest_scrape_on_init=True)


def run(label, **kwargs):
    print(f"\n=== {label} ===")
    try:
        tweets = s.search(display_type="Latest", limit=5, **kwargs)
        print(f"  returned: {len(tweets)} tweets")
        if tweets:
            t = tweets[0]
            print("  sample keys:", list(t.keys()))
            print("  sample text:", str(t.get("text") or t.get("content"))[:120])
        return len(tweets)
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {e}")
        return None


# STAGE 1 — control. High global volume. Proves auth + pipe work.
control = run("CONTROL: bitcoin", query="bitcoin")

# STAGE 2 — MSE. Company name in Cyrillic, not raw ticker.
mse_cyr = run("MSE: АПУ ХК", query="АПУ ХК")

# STAGE 3 — MSE with disambiguator, English.
mse_en = run("MSE: APU Mongolia", query="APU Mongolia")

# STAGE 4 — Mongolia geo + language filter (any finance chatter at all?)
mse_geo = run("MONGOLIA lang=mn", query="хувьцаа", lang="mn")

print("\n----- VERDICT -----")
if control is None or control == 0:
    print("Setup BROKEN — control query failed. Check auth_token / account not locked / proxy.")
elif (mse_cyr or 0) + (mse_en or 0) + (mse_geo or 0) == 0:
    print("Setup WORKS but MSE volume ~0 on X. Twitter is the wrong source. Pivot to Facebook.")
else:
    print("Setup works AND there's MSE signal. Worth building the full loop.")
