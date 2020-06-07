# fccid-parse

Use this script to send webhooks to Discord when the fccid.io site has changes from the specified FCC id.

## Setup
```bash
git clone git@github.com:jonbloom/fccid-parse.git
cd fccid-parse
python3 -m virtualenv venv
. venv/bin/activate
pip install -r requirements.txt
```

Specify a `DISCORD_WEBHOOK_URL` and `FCCID` in a .env file, then run `python3 scrape.py`.
