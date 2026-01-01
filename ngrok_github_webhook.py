import time
import requests
from pyngrok import ngrok, conf

# ===== CONFIG =====
# Configuration is loaded from environment variables. For local development,
# create a `.env` file (see `.env.example`) and install `python-dotenv`.
# Required environment variables:
#   NGROK_AUTH_TOKEN, LOCAL_PORT, WEBHOOK_PATH,
#   GITHUB_TOKEN, REPO_OWNER, REPO_NAME, WEBHOOK_ID

import os
import logging
from dotenv import load_dotenv

load_dotenv()

NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN")
LOCAL_PORT = int(os.getenv("LOCAL_PORT", "8000"))
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/github-webhook")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")
WEBHOOK_ID = os.getenv("WEBHOOK_ID")

# Basic validation
required = ["NGROK_AUTH_TOKEN", "GITHUB_TOKEN", "REPO_OWNER", "REPO_NAME", "WEBHOOK_ID"]
missing = [v for v in required if not os.getenv(v)]
if missing:
    raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")
# ==================

import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


def start_ngrok():
    conf.get_default().auth_token = NGROK_AUTH_TOKEN
    tunnel = ngrok.connect(LOCAL_PORT, "http")
    public_url = getattr(tunnel, 'public_url', None)
    if not public_url:
        logging.error("Failed to start ngrok tunnel")
        raise SystemExit("ngrok did not return a public URL")
    logging.info(f"Ngrok public URL: {public_url}")
    return public_url


def update_github_webhook(public_url):
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/hooks/{WEBHOOK_ID}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    payload = {
        "config": {
            "url": f"{public_url}{WEBHOOK_PATH}",
            "content_type": "json"
        }
    }

    r = requests.patch(api_url, headers=headers, json=payload)

    if r.status_code == 200:
        logging.info("GitHub webhook updated")
    else:
        logging.error("Failed to update webhook: %s %s", r.status_code, r.text)
        r.raise_for_status()


def main():
    public_url = start_ngrok()

    update_github_webhook(public_url)

    logging.info("Ready to receive GitHub webhooks")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logging.info("Shutting down ngrok tunnel")
        ngrok.kill()


if __name__ == "__main__":
    main()
