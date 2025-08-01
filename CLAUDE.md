# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains a web scraper for mirroring the Historical and Colonial Census Data Archive (HCCDA) from the Wayback Machine. The project downloads census data tables from Australian states spanning from the 1830s to 1901.

## Architecture

- **Main Script**: `pull_data.py` - A recursive web crawler that downloads census data from the Wayback Machine
- **Downloaded Data**: Stored in `census_data_download/` directory, maintaining the original URL structure
- **Log File**: `hccda_mirror.log` - Tracks download progress and errors

## Key Components

1. **Web Crawler**: Uses BeautifulSoup to parse HTML and recursively crawl directories
2. **File Downloader**: Downloads individual census table HTML files with progress tracking
3. **Error Handling**: Comprehensive logging and error recovery mechanisms
4. **Rate Limiting**: Includes delays to be respectful to Wayback Machine servers

## Development Commands

### Setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install requests beautifulsoup4 tqdm
```

### Running the Script
```bash
# Run the mirror script (requires destination path)
python pull_data.py /path/to/destination

# The script is already configured to mirror from:
# https://web.archive.org/web/20250305014851/http://hccda.ada.edu.au/
```

### Monitoring Progress
```bash
# View real-time logs
tail -f hccda_mirror.log

# Check download progress
ls -la census_data_download/
```

## Important Notes

- The script includes recursion depth limits (max 15) to prevent infinite loops
- Downloaded files are skipped if they already exist locally
- The crawler respects a 0.2-second delay between subdirectory requests
- All errors are logged but don't stop the entire process
- The Wayback Machine base URL is hardcoded to a specific snapshot (20250305014851)

## Data Structure

Downloaded census data is organized by:
- State (NSW, QLD, SA, TAS, VIC, WA)
- Year (1833-1901)
- Type (Collated_Census_Tables/ or Individual_Census_Tables/)

Each census table is stored as an HTML file maintaining the original naming convention.