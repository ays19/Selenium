# Selenium Login & Data Extractor

Logs into a website, extracts data, and saves it to CSV and JSON.

## Features
- Secure login using credentials from a `.env` file (nothing hardcoded)
- Explicit waits (no `time.sleep`)
- Exports CSV + JSON with timestamps
- Screenshot after success, and on error
- Run log in `output/run.log`
- Headless mode option
- Selectors kept in one place, so it is easy to adapt to another site

## Setup
```
python -m pip install -r requirements.txt
copy .env.example .env
python scraper.py
```

Demo target: [saucedemo.com](https://www.saucedemo.com) (public practice site).

## Tech
Python, Selenium 4, python-dotenv