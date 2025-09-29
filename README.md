# Kia Parts Scraper

Small scraper that uses Playwright (sync API) to load pages and BeautifulSoup to parse Kia parts pages.

Quick setup (macOS, zsh):

1. Install pyenv (optional but recommended) and a recent Python. Example:

   brew install pyenv
   pyenv install 3.12.3
   pyenv local 3.12.3

2. Create and activate a virtualenv in the project root:

   python -m venv .venv
   source .venv/bin/activate

3. Install dependencies and Playwright browsers:

   pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt
   python -m playwright install

Run:

   python scrape_kia_parts.py

Files:
- `scrape_kia_parts.py` — scrapes a parts page and writes `kia_parts.json`.
- `extract_kia_links.py`, `navigate_kia_parts.py` — helper scripts for navigation and link extraction.

Notes:
- The scripts use a Playwright persistent profile directory named `.pw_user`. Remove it to start fresh.
- Add any additional dependencies to `requirements.txt`.
# Kia Parts Scraper

A collection of Python scripts for scraping Kia parts data using Playwright. Supports both single-page scraping and bulk assembly processing with various proxy options.

## Scripts Overview

- `scrape_kia_parts.py`: Basic script for scraping parts from a single assembly page. Uses direct connection without proxies.

- `scrape_kia_parts_free_proxies.py`: Single-page scraper using free proxies from free-proxy-list.net with automatic proxy rotation.

- `scrape_kia_parts_swiftshadow_proxy.py`: Single-page scraper using SwiftShadow proxy service with auto-rotation (requires SwiftShadow credentials).

- `scrape_kia_parts_bulk.py`: Bulk scraper that processes multiple assembly URLs from a file. Includes logging, error handling, and progress tracking. Saves data to CSV.

- `extract_kia_links.py`: Helper script to extract assembly page URLs from category/model pages.

- `navigate_kia_parts.py`: Example script to crowl through the parts website.

## Setup

1. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

3. Install Playwright browsers:
```bash
python -m playwright install
```

## Usage

### Basic Scraping
```bash
python scrape_kia_parts.py
```

### Bulk Scraping with Progress Tracking
```bash
python scrape_kia_parts_bulk.py
```
This will:
- Read URLs from `assembly_urls.txt`
- Save progress every 5 URLs
- Create timestamped CSV and log files
- Track failed URLs in `failed_urls.txt`

### Using Proxies

With free proxies:
```bash
python scrape_kia_parts_free_proxies.py
```

With SwiftShadow (requires subscription):
```bash
python scrape_kia_parts_swiftshadow_proxy.py
```

## Output Files

- `kia_parts.json`: Output from single-page scrapers
- `kia_parts_data_[timestamp].csv`: Output from bulk scraper
- `kia_parts_scraper_[timestamp].log`: Detailed logging from bulk scraper
- `failed_urls.txt`: URLs that failed during bulk scraping
- `assembly_urls.txt`: List of assembly URLs to scrape
- `proxies.txt`: Free proxy list (used by free proxies script)

## Notes

- Scripts use a persistent Playwright profile directory (`.pw_user`) to maintain session data
- The bulk scraper includes error recovery and progress tracking
- Proxy scripts include automatic rotation and retry logic
- All scripts handle timeouts and common errors gracefully

## Requirements

See `requirements.txt` for full list of dependencies:
- playwright
- beautifulsoup4
- requests
- pandas (for bulk scraping)
- rotating-free-proxies (for free proxy version)
- swiftshadow (optional, for premium proxies)

## Contributing

Feel free to open issues or submit pull requests.

## License

MIT License

Copyright (c) 2025 Lahiru

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
