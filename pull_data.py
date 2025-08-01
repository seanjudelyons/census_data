#!/usr/bin/env python3
"""
hccda_mirror.py

mirror the entire historical and colonial census data archive snapshot
(wayback id 20250305014851) to a local folder

usage:
    python hccda_mirror.py /path/to/destination

requirements:
    pip install requests beautifulsoup4 tqdm
"""
import os
import sys
import time
import urllib.parse
import logging
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# base url of the archived site
WAYBACK_BASE = "https://web.archive.org/web/20250305014851/http://hccda.ada.edu.au/"

# set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hccda_mirror.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def is_directory_link(tag):
    href = tag.get("href")
    if not href:
        return False
    # a link ending in slash is treated as a directory and we ignore the parent link
    return href.endswith("/") and href != "../"

def is_file_link(tag):
    href = tag.get("href")
    if not href:
        return False
    return not href.endswith("/")

def sanitize_path(url_path: str) -> str:
    """turn a url path into a safe local filesystem path"""
    return urllib.parse.unquote(url_path.lstrip("/"))

def fetch(url: str, session: requests.Session, dest_path: Path):
    """fetch a single file and write to dest_path"""
    try:
        logger.info(f"downloading file: {url}")
        resp = session.get(url, stream=True, timeout=60)
        resp.raise_for_status()
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        logger.info(f"successfully downloaded: {dest_path}")
    except Exception as e:
        logger.error(f"failed to download {url}: {e}")
        raise

def crawl(url: str, session: requests.Session, dest_root: Path, visited: set = None, depth: int = 0, max_depth: int = 15):
    """crawl with recursion depth and visited url tracking"""
    if visited is None:
        visited = set()
    
    # prevent infinite recursion
    if depth > max_depth:
        logger.warning(f"max depth {max_depth} reached for url: {url}")
        return
    
    # normalize url to prevent duplicate visits
    normalized_url = url.rstrip('/')
    if normalized_url in visited:
        logger.debug(f"already visited: {url}")
        return
    
    visited.add(normalized_url)
    logger.info(f"crawling (depth {depth}): {url}")
    
    try:
        resp = session.get(url, timeout=60)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # derive local directory path that mirrors the remote hierarchy
        rel_path = urllib.parse.urlparse(url).path.replace(
            "/web/20250305014851/http://hccda.ada.edu.au", ""
        )
        current_dir = dest_root / sanitize_path(rel_path)
        logger.info(f"processing directory: {current_dir}")

        # separate file and directory links
        links = soup.find_all("a")
        directories = [tag for tag in links if is_directory_link(tag)]
        files = [tag for tag in links if is_file_link(tag)]
        
        logger.info(f"found {len(files)} files and {len(directories)} directories in {rel_path or '/'}")

        # download every file in the current directory
        for tag in tqdm(files, desc=f"files in {rel_path or '/'}"):
            href = tag.get("href")
            file_url = urllib.parse.urljoin(url, href)
            local_file = current_dir / sanitize_path(href)
            
            if local_file.exists():
                logger.debug(f"file already exists, skipping: {local_file}")
                continue
                
            try:
                fetch(file_url, session, local_file)
            except Exception as e:
                logger.error(f"failed to download {file_url}: {e}")
                # continue with other files instead of stopping

        # recurse into subdirectories
        for tag in directories:
            href = tag.get("href")
            sub_url = urllib.parse.urljoin(url, href)
            
            # additional safety check for problematic urls
            if sub_url == url or sub_url in visited:
                logger.warning(f"skipping circular or duplicate url: {sub_url}")
                continue
                
            logger.info(f"entering subdirectory: {sub_url}")
            try:
                crawl(sub_url, session, dest_root, visited, depth + 1, max_depth)
                time.sleep(0.2)  # be polite to wayback servers
            except RecursionError:
                logger.error(f"recursion error at depth {depth} for url: {sub_url}")
                break
            except Exception as e:
                logger.error(f"error crawling {sub_url}: {e}")
                # continue with other directories

    except Exception as e:
        logger.error(f"error processing {url} at depth {depth}: {e}")
        return

def main():
    if len(sys.argv) < 2:
        print("usage: python hccda_mirror.py /path/to/destination")
        sys.exit(1)
        
    dest_root = Path(sys.argv[1]).expanduser().resolve()
    logger.info(f"starting mirror to {dest_root}")
    
    session = requests.Session()
    session.headers.update({"User-Agent": "hccda mirror script"})
    
    try:
        crawl(WAYBACK_BASE, session, dest_root)
        logger.info("mirror completed successfully")
    except KeyboardInterrupt:
        logger.info("mirror interrupted by user")
    except Exception as e:
        logger.error(f"mirror failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

