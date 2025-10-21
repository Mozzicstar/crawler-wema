# enhanced_crawler.py
"""
Enhanced crawler with better content extraction for JS-heavy sites
"""
import json
import time
from urllib.parse import urljoin, urlparse, urldefrag
from collections import deque
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

START_URL = "https://wemabank.com/your-responsibility"
MAX_PAGES = 100
MAX_DEPTH = 2
DELAY = 2.0
OUTPUT_FILE = "wema_enhanced.json"

def clean_url(base, href):
    """Clean URL"""
    if not href or not isinstance(href, str):
        return None
    href = href.strip()
    if href.startswith(('mailto:', 'tel:', 'javascript:', '#')):
        return None
    try:
        full = urljoin(base, href)
        full = urldefrag(full)[0]
        if not full.startswith(('http://', 'https://')):
            return None
        return full
    except:
        return None

def same_domain(url, base_domain):
    """Check same domain"""
    try:
        return urlparse(url).netloc == base_domain
    except:
        return False

def extract_content(page):
    """Enhanced content extraction with better JS handling"""
    content = {
        "title": "",
        "meta_description": "",
        "headings": [],
        "paragraphs": [],
        "lists": [],
        "text": "",
        "links": []
    }
    
    try:
        content["title"] = page.title() or ""
    except Exception as e:
        logger.debug(f"Title extraction error: {e}")
    
    # Meta description
    try:
        meta = page.query_selector("meta[name='description']")
        if meta:
            content["meta_description"] = meta.get_attribute("content") or ""
    except Exception as e:
        logger.debug(f"Meta description error: {e}")
    
    # Headings - more robust extraction
    try:
        for tag in ['h1', 'h2', 'h3', 'h4']:
            elements = page.query_selector_all(tag)
            for el in elements[:30]:
                try:
                    text = el.text_content().strip()
                    if text and len(text) > 2:
                        content["headings"].append({
                            "tag": tag,
                            "text": text
                        })
                except:
                    continue
    except Exception as e:
        logger.debug(f"Headings extraction error: {e}")
    
    # Paragraphs - use text_content instead of inner_text
    try:
        paragraphs = page.query_selector_all("p")
        for p in paragraphs[:200]:
            try:
                text = p.text_content().strip()
                if text and len(text) > 20:  # Only meaningful paragraphs
                    content["paragraphs"].append(text)
            except:
                continue
    except Exception as e:
        logger.debug(f"Paragraphs extraction error: {e}")
    
    # List items
    try:
        list_items = page.query_selector_all("li")
        for li in list_items[:100]:
            try:
                text = li.text_content().strip()
                if text and len(text) > 10:
                    content["lists"].append(text)
            except:
                continue
    except Exception as e:
        logger.debug(f"List items extraction error: {e}")
    
    # Divs with substantial text (fallback for content-heavy sites)
    try:
        divs = page.query_selector_all("div.content, div.main, article, section")
        for div in divs[:50]:
            try:
                text = div.text_content().strip()
                if text and len(text) > 100 and len(text) < 5000:
                    # Check if it's not already captured
                    if text not in content["paragraphs"]:
                        content["paragraphs"].append(text)
            except:
                continue
    except Exception as e:
        logger.debug(f"Div extraction error: {e}")
    
    # Links
    try:
        links = page.query_selector_all("a[href]")
        for link in links[:300]:
            try:
                href = link.get_attribute("href")
                if href:
                    content["links"].append(href)
            except:
                continue
    except Exception as e:
        logger.debug(f"Link extraction error: {e}")
    
    # Build comprehensive text blob
    text_parts = []
    
    if content["title"]:
        text_parts.append(content["title"])
    
    if content["meta_description"]:
        text_parts.append(content["meta_description"])
    
    # Add headings
    for h in content["headings"]:
        text_parts.append(h["text"])
    
    # Add paragraphs
    text_parts.extend(content["paragraphs"])
    
    # Add list items
    text_parts.extend(content["lists"])
    
    content["text"] = "\n\n".join(text_parts)
    
    return content

def crawl_enhanced():
    """Enhanced crawler with better content extraction"""
    domain = urlparse(START_URL).netloc
    queue = deque([(START_URL, 0)])
    seen = {START_URL}
    results = []
    
    logger.info(f"Starting enhanced crawl: {START_URL}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True,
            java_script_enabled=True  # Ensure JS is enabled
        )
        
        pages_fetched = 0
        
        while queue and pages_fetched < MAX_PAGES:
            url, depth = queue.popleft()
            
            if depth > MAX_DEPTH:
                continue
            
            logger.info(f"[{pages_fetched + 1}/{MAX_PAGES}] Depth {depth}: {url}")
            
            page = None
            
            # Try multiple times
            for attempt in range(3):
                try:
                    page = context.new_page()
                    page.set_default_timeout(60000)
                    
                    logger.info(f"  Attempt {attempt + 1}...")
                    
                    # Navigate
                    response = page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    
                    # CRITICAL: Wait for content to load
                    # Try multiple strategies to ensure content is loaded
                    
                    # 1. Wait for network to be idle
                    try:
                        page.wait_for_load_state("networkidle", timeout=15000)
                    except:
                        logger.debug("Network idle timeout - continuing")
                    
                    # 2. Wait for body to have content
                    try:
                        page.wait_for_selector("body", timeout=10000)
                    except:
                        pass
                    
                    # 3. Wait for specific selectors that indicate content is loaded
                    try:
                        page.wait_for_selector("p, article, section, div.content", timeout=10000)
                    except:
                        pass
                    
                    # 4. Give extra time for lazy-loaded content
                    time.sleep(3)
                    
                    # 5. Scroll to load lazy content
                    try:
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                        time.sleep(1)
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(1)
                    except:
                        pass
                    
                    # Check status
                    if response and 200 <= response.status < 400:
                        # Extract content
                        content = extract_content(page)
                        
                        doc = {
                            "url": url,
                            "depth": depth,
                            "title": content["title"],
                            "meta_description": content["meta_description"],
                            "headings": content["headings"],
                            "paragraphs": content["paragraphs"][:100],  # Limit
                            "lists": content["lists"][:50],
                            "text": content["text"][:10000],  # Keep more text
                            "text_length": len(content["text"]),
                            "crawled_at": datetime.utcnow().isoformat() + "Z"
                        }
                        
                        results.append(doc)
                        
                        text_preview = content["text"][:200].replace("\n", " ")
                        logger.info(f"  ✓ Success! Text length: {len(content['text'])} chars")
                        logger.info(f"  Preview: {text_preview}...")
                        
                        # Process links
                        new_count = 0
                        for href in content["links"]:
                            clean = clean_url(url, href)
                            if clean and clean not in seen and same_domain(clean, domain):
                                seen.add(clean)
                                queue.append((clean, depth + 1))
                                new_count += 1
                        
                        logger.info(f"  ✓ Added {new_count} new URLs to queue")
                        pages_fetched += 1
                        break
                        
                    else:
                        status = response.status if response else "No response"
                        logger.warning(f"  Bad status: {status}")
                        
                except PlaywrightTimeout:
                    logger.warning(f"  Timeout on attempt {attempt + 1}")
                    
                except Exception as e:
                    logger.error(f"  Error on attempt {attempt + 1}: {e}")
                
                finally:
                    if page:
                        try:
                            page.close()
                        except:
                            pass
                
                # Wait before retry
                if attempt < 2:
                    time.sleep(5)
            
            # Delay between pages
            time.sleep(DELAY)
        
        browser.close()
    
    # Save results
    if results:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # Statistics
        total_text = sum(len(r["text"]) for r in results)
        avg_text = total_text / len(results) if results else 0
        pages_with_content = sum(1 for r in results if len(r["text"]) > 100)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✓✓✓ Crawl Complete!")
        logger.info(f"{'='*60}")
        logger.info(f"Total pages crawled: {len(results)}")
        logger.info(f"Pages with content: {pages_with_content}")
        logger.info(f"Total text extracted: {total_text:,} characters")
        logger.info(f"Average text per page: {avg_text:.0f} characters")
        logger.info(f"Output file: {OUTPUT_FILE}")
        logger.info(f"{'='*60}")
    else:
        logger.error("No pages were crawled successfully")

if __name__ == "__main__":
    try:
        crawl_enhanced()
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)