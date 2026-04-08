import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
from pathlib import Path
from typing import List, Dict, Tuple
import time
import json
import csv
import zipfile
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image as RLImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self, url: str, output_dir: str = "scraped_content", max_pages: int = 5, custom_urls: List[str] = None):
        self.url = url
        self.output_dir = output_dir
        self.max_pages = max_pages
        self.custom_urls = custom_urls or []
        self.visited_urls = set()
        self.pages_data = {}
        self.failed_downloads = []  # Queue for failed downloads
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self._setup_directories()

    def _setup_directories(self):
        """Create necessary directories for storing content."""
        Path(self.output_dir).mkdir(exist_ok=True)
        Path(f"{self.output_dir}/images").mkdir(exist_ok=True)
        Path(f"{self.output_dir}/videos").mkdir(exist_ok=True)
        Path(f"{self.output_dir}/text").mkdir(exist_ok=True)
        Path(f"{self.output_dir}/pages").mkdir(exist_ok=True)

    def _normalize_url(self, url: str, page_url: str = None) -> str:
        """Normalize and fix malformed URLs."""
        if not url:
            return url
        
        # If URL is already absolute, return as-is
        if url.startswith(('http://', 'https://')):
            return url
        
        # Get the base URL context
        base_url = page_url or self.url
        base_parsed = urlparse(base_url)
        base_domain = base_parsed.scheme + "://" + base_parsed.netloc
        
        # Common issue: /assets/ instead of /web/assets/ 
        # Detect and fix path inconsistencies
        if url.startswith('/assets/'):
            # Check if the page is under /web/ path
            if '/web/' in base_parsed.path:
                # Correct the URL to include /web/
                url = '/web' + url
                logger.info(f"  Fixed malformed URL: {url}")
        
        # Convert relative to absolute
        absolute_url = urljoin(base_url, url)
        return absolute_url
        """Check if URL is from the same domain."""
        base_domain = urlparse(self.url).netloc
        check_domain = urlparse(url).netloc
        return base_domain == check_domain
    
    def get_page_links(self, html: str) -> List[str]:
        """Extract all links from a page (excluding media files)."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            links = []
            
            # Media file extensions to exclude from page crawling
            media_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico',
                              '.mp4', '.webm', '.mov', '.avi', '.mkv', '.flv', '.pdf',
                              '.zip', '.rar', '.exe', '.dmg']
            
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href and not href.startswith('#'):
                    # Skip media files
                    if any(href.lower().endswith(ext) for ext in media_extensions):
                        logger.info(f"  Skipping media file: {href}")
                        continue
                    
                    # Convert relative URLs to absolute
                    absolute_url = urljoin(self.url, href)
                    
                    # Filter to same domain and valid structure
                    if self.is_same_domain(absolute_url) and absolute_url not in self.visited_urls:
                        # Remove fragments and query params for cleaner URLs
                        clean_url = absolute_url.split('#')[0]
                        if clean_url not in links:
                            links.append(clean_url)
                            logger.info(f"  Found page link: {clean_url}")
            
            logger.info(f"Total page links found: {len(links)}")
            return links
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
            return []

    def _get_page_name_from_url(self, url: str) -> str:
        """Extract a safe page name from URL for folder naming."""
        try:
            parsed = urlparse(url)
            path = parsed.path.strip('/')
            
            # If no path (root URL), use 'home'
            if not path:
                return 'home'
            
            # Get the last part of the path
            page_name = path.split('/')[-1]
            
            # Remove query parameters and fragments if any
            page_name = page_name.split('?')[0].split('#')[0]
            
            # Replace common separators with underscores and make filesystem-safe
            page_name = page_name.replace('-', '_').replace(' ', '_')
            
            # Remove special characters
            page_name = ''.join(c for c in page_name if c.isalnum() or c == '_')
            
            # Limit length to reasonable size
            page_name = page_name[:50] if page_name else 'page'
            
            return page_name or 'page'
        except Exception as e:
            logger.error(f"Error extracting page name from {url}: {e}")
            return 'page'
    
    def fetch_page(self, url: str = None) -> str:
        """Fetch the webpage content."""
        target_url = url or self.url
        try:
            logger.info(f"Fetching page: {target_url}")
            response = self.session.get(target_url, timeout=10)
            response.raise_for_status()
            logger.info("Page fetched successfully")
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching page: {e}")
            return None
    
    def crawl_pages(self) -> Dict:
        """Crawl all pages from the website."""
        try:
            all_results = {
                'pages': [],
                'total_images': [],
                'total_videos': [],
                'all_headers': {f'h{i}': [] for i in range(1, 7)},
                'seo_analysis': {},
                'categorized_text': []
            }
            
            # Use custom URLs if provided, otherwise auto-discover
            if self.custom_urls:
                to_visit = self.custom_urls.copy()
                logger.info(f"Using {len(self.custom_urls)} custom URLs")
            else:
                to_visit = [self.url]
                logger.info("Auto-discovering pages from site")
            
            page_count = 0
            original_output_dir = self.output_dir  # Store original before any modifications
            
            while to_visit:
                # Check if we've hit the limit
                if page_count >= self.max_pages:
                    logger.info(f"Reached max pages limit: {self.max_pages}")
                    break
                
                current_url = to_visit.pop(0)
                
                if current_url in self.visited_urls:
                    continue
                
                self.visited_urls.add(current_url)
                logger.info(f"Scraping page {page_count + 1}: {current_url}")
                
                html = self.fetch_page(current_url)
                if not html:
                    continue
                
                # Create page-specific folder with descriptive name
                page_name = self._get_page_name_from_url(current_url)
                page_folder = f"{self.output_dir}/pages/page_{page_count + 1}_{page_name}"
                Path(page_folder).mkdir(parents=True, exist_ok=True)
                Path(f"{page_folder}/images").mkdir(exist_ok=True)
                Path(f"{page_folder}/videos").mkdir(exist_ok=True)
                
                # Temporarily override output_dir for this page
                self.output_dir = page_folder
                
                # Extract page-specific data
                page_images = self.extract_and_download_images(html, current_url)
                page_videos = self.extract_and_download_videos(html, current_url)
                page_seo = self.extract_seo_headers(html)
                page_text = self.extract_text(html)
                page_categorized_text = self.extract_text_by_category(html, current_url, page_count + 1, page_name)
                
                # Save page-specific SEO analysis
                seo_file = f"{page_folder}/seo_analysis.txt"
                with open(seo_file, 'w', encoding='utf-8') as f:
                    seo_analysis = page_seo.get('seo_analysis', {})
                    f.write(f"Page URL: {current_url}\n")
                    f.write(f"H1 Status: {seo_analysis.get('h1_status', 'Unknown')}\n")
                    f.write(f"Content Score: {seo_analysis.get('content_structure_score', 0)}/100\n\n")
                    for level in range(1, 7):
                        headers = page_seo.get('headers', {}).get(f'h{level}', [])
                        if headers:
                            f.write(f"\nH{level} Tags ({len(headers)}):\n")
                            for h in headers:
                                f.write(f"  • {h.get('text', 'N/A')}\n")
                
                logger.info(f"Saved page data to {page_folder}")
                
                # Restore original output_dir
                self.output_dir = original_output_dir
                
                page_data = {
                    'url': current_url,
                    'page_number': page_count + 1,
                    'page_folder': page_folder,
                    'images': page_images,
                    'videos': page_videos,
                    'seo': page_seo
                }
                
                all_results['pages'].append(page_data)
                all_results['total_images'].extend(page_images)
                all_results['total_videos'].extend(page_videos)
                all_results['categorized_text'].append(page_categorized_text)
                
                # Merge headers
                for level in range(1, 7):
                    headers = page_seo.get('headers', {}).get(f'h{level}', [])
                    all_results['all_headers'][f'h{level}'].extend(headers)
                
                # Only discover new links if not using custom URLs
                if not self.custom_urls:
                    new_links = self.get_page_links(html)
                    for link in new_links:
                        if link not in self.visited_urls and link not in to_visit:
                            to_visit.append(link)
                
                page_count += 1
                time.sleep(1)  # Respectful delay between requests
            
            # Aggregate SEO analysis
            all_results['seo_analysis'] = self._aggregate_seo_data(all_results)
            
            logger.info(f"Crawling complete. Scraped {page_count} pages")
            
            # Restore the original output directory
            self.output_dir = original_output_dir
            
            return all_results
        except Exception as e:
            logger.error(f"Error during crawling: {e}")
            self.output_dir = original_output_dir  # Restore in case of error
            return None

    def extract_seo_headers(self, html: str) -> Dict:
        """Extract header hierarchy for SEO analysis."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            headers = {
                'h1': [],
                'h2': [],
                'h3': [],
                'h4': [],
                'h5': [],
                'h6': []
            }
            
            # Extract all headers
            for level in range(1, 7):
                tag_name = f'h{level}'
                for idx, tag in enumerate(soup.find_all(tag_name), 1):
                    text = tag.get_text(strip=True)
                    headers[tag_name].append({
                        'text': text,
                        'order': idx,
                        'html_id': tag.get('id', 'N/A'),
                        'class': tag.get('class', [])
                    })
            
            # Generate SEO report
            seo_analysis = self._analyze_header_seo(headers)
            
            # Save headers hierarchy
            self._save_header_hierarchy(headers, seo_analysis)
            
            logger.info("SEO header analysis complete")
            return {
                'headers': headers,
                'seo_analysis': seo_analysis
            }
        except Exception as e:
            logger.error(f"Error extracting headers: {e}")
            return {'headers': {}, 'seo_analysis': {}}
    
    def _analyze_header_seo(self, headers: Dict) -> Dict:
        """Analyze header structure for SEO best practices."""
        analysis = {
            'h1_count': len(headers['h1']),
            'h1_status': '',
            'hierarchy_issues': [],
            'recommendations': [],
            'content_structure_score': 0
        }
        
        # Check H1 count (SEO best practice: exactly 1 H1)
        if analysis['h1_count'] == 0:
            analysis['h1_status'] = 'CRITICAL: No H1 tag found'
            analysis['recommendations'].append('Add exactly one H1 tag to the page')
        elif analysis['h1_count'] == 1:
            analysis['h1_status'] = 'GOOD: Single H1 tag present'
        else:
            analysis['h1_status'] = f'WARNING: Multiple H1 tags ({analysis["h1_count"]})'
            analysis['recommendations'].append('Use only one H1 tag per page')
        
        # Check hierarchy structure
        hierarchy_order = []
        for level in range(1, 7):
            if headers[f'h{level}']:
                hierarchy_order.append(level)
        
        # Check for proper hierarchy (no skipping levels)
        for i in range(len(hierarchy_order) - 1):
            if hierarchy_order[i+1] - hierarchy_order[i] > 1:
                analysis['hierarchy_issues'].append(
                    f'Hierarchy jump from H{hierarchy_order[i]} to H{hierarchy_order[i+1]}'
                )
                analysis['recommendations'].append('Maintain proper header hierarchy without skipping levels')
        
        # Calculate content structure score (0-100)
        score = 100
        if analysis['h1_count'] != 1:
            score -= 30
        if len(analysis['hierarchy_issues']) > 0:
            score -= min(20, len(analysis['hierarchy_issues']) * 5)
        if len(headers['h2']) == 0:
            score -= 20
        
        analysis['content_structure_score'] = max(0, score)
        
        return analysis
    
    def _save_header_hierarchy(self, headers: Dict, seo_analysis: Dict):
        """Save detailed header hierarchy report."""
        report_file = f"{self.output_dir}/text/seo_header_analysis.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("SEO HEADER HIERARCHY ANALYSIS\n")
            f.write("="*70 + "\n\n")
            
            # SEO Analysis Summary
            f.write("SEO ANALYSIS SUMMARY\n")
            f.write("-" * 70 + "\n")
            f.write(f"H1 Status: {seo_analysis['h1_status']}\n")
            f.write(f"Content Structure Score: {seo_analysis['content_structure_score']}/100\n")
            
            if seo_analysis['hierarchy_issues']:
                f.write("\nHierarchy Issues:\n")
                for issue in seo_analysis['hierarchy_issues']:
                    f.write(f"  ⚠ {issue}\n")
            
            if seo_analysis['recommendations']:
                f.write("\nRecommendations:\n")
                for rec in seo_analysis['recommendations']:
                    f.write(f"  ✓ {rec}\n")
            
            f.write("\n" + "="*70 + "\n")
            f.write("HEADER STRUCTURE\n")
            f.write("="*70 + "\n\n")
            
            # Detailed header breakdown
            for level in range(1, 7):
                tag_name = f'h{level}'
                header_list = headers[tag_name]
                if header_list:
                    f.write(f"\n{tag_name.upper()} TAGS ({len(header_list)} found)\n")
                    f.write("-" * 70 + "\n")
                    for idx, header in enumerate(header_list, 1):
                        f.write(f"\n{idx}. {header['text']}\n")
                        if header['html_id'] != 'N/A':
                            f.write(f"   ID: {header['html_id']}\n")
                        if header['class']:
                            f.write(f"   Classes: {', '.join(header['class'])}\n")
            
            f.write("\n" + "="*70 + "\n")
            f.write("HIERARCHY TREE\n")
            f.write("="*70 + "\n\n")
            
            # Visual hierarchy tree
            f.write(self._generate_hierarchy_tree(headers))
        
        logger.info(f"SEO analysis saved to {report_file}")
    
    def _generate_hierarchy_tree(self, headers: Dict) -> str:
        """Generate visual hierarchy tree."""
        tree = ""
        
        for h1 in headers['h1']:
            tree += f"├─ H1: {h1['text']}\n"
            # Find H2s that follow this H1
            for h2 in headers['h2']:
                tree += f"│  ├─ H2: {h2['text']}\n"
                # Find H3s that follow this H2
                for h3 in headers['h3']:
                    tree += f"│  │  ├─ H3: {h3['text']}\n"
                    for h4 in headers['h4']:
                        tree += f"│  │  │  ├─ H4: {h4['text']}\n"
        
        # If no H1s, show all headers
        if not headers['h1'] and (headers['h2'] or headers['h3'] or headers['h4']):
            tree += "⚠ WARNING: No H1 found. Showing available headers:\n"
            for h2 in headers['h2']:
                tree += f"├─ H2: {h2['text']}\n"
            for h3 in headers['h3']:
                tree += f"├─ H3: {h3['text']}\n"
            for h4 in headers['h4']:
                tree += f"├─ H4: {h4['text']}\n"
        
        return tree

    def _aggregate_seo_data(self, crawl_results: Dict) -> Dict:
        """Aggregate SEO data from all pages."""
        all_headers = crawl_results.get('all_headers', {})
        
        aggregate_analysis = {
            'total_pages': len(crawl_results.get('pages', [])),
            'total_h1': len(all_headers.get('h1', [])),
            'total_h2': len(all_headers.get('h2', [])),
            'all_headers': all_headers,
            'h1_status': 'GOOD' if len(all_headers.get('h1', [])) >= 1 else 'WARNING',
            'recommendations': []
        }
        
        if aggregate_analysis['total_h1'] == 0:
            aggregate_analysis['recommendations'].append('Add H1 tags to all pages')
        if aggregate_analysis['total_h2'] == 0:
            aggregate_analysis['recommendations'].append('Add H2 tags for proper hierarchy')
        
        aggregate_analysis['recommendations'].append(
            f'Reviewed {aggregate_analysis["total_pages"]} pages with headers: '
            f'{aggregate_analysis["total_h1"]} H1, {aggregate_analysis["total_h2"]} H2'
        )
        
        return aggregate_analysis

    def extract_text_by_category(self, html: str, page_url: str = None, page_number: int = 1, page_name: str = "page") -> List[Dict]:
        """Extract text organized by HTML tag categories (h1, h2, h3, p, li, etc.)."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            categorized_text = []
            
            # Tags to extract with their category names
            tag_categories = {
                'h1': 'Heading 1',
                'h2': 'Heading 2',
                'h3': 'Heading 3',
                'h4': 'Heading 4',
                'h5': 'Heading 5',
                'h6': 'Heading 6',
                'p': 'Paragraph',
                'li': 'List Item',
                'strong': 'Bold Text',
                'em': 'Italic Text',
                'span': 'Span Text',
                'div': 'Section',
                'blockquote': 'Quote'
            }
            
            # Extract text from each category
            for tag, category_name in tag_categories.items():
                elements = soup.find_all(tag)
                for idx, element in enumerate(elements, 1):
                    text = element.get_text(strip=True)
                    if text and len(text.strip()) > 0:  # Only include non-empty text
                        categorized_text.append({
                            'page_number': page_number,
                            'page_name': page_name,
                            'page_url': page_url or self.url,
                            'category': category_name,
                            'tag': tag,
                            'order': idx,
                            'text': text[:500]  # Limit text length
                        })
            
            logger.info(f"Extracted {len(categorized_text)} categorized text elements from page {page_number}")
            return categorized_text
        except Exception as e:
            logger.error(f"Error extracting categorized text: {e}")
            return []

    def export_categorized_text_to_csv(self, all_pages_data: List[List[Dict]]) -> str:
        """Export categorized text from all pages to CSV format."""
        try:
            if not all_pages_data:
                logger.warning("No categorized text data to export")
                return None
            
            Path(f"{self.output_dir}/reports").mkdir(exist_ok=True)
            csv_file = f"{self.output_dir}/reports/categorized_text_content.csv"
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Page Number', 'Page Name', 'Page URL', 'Category', 'HTML Tag', 'Order', 'Text Content'])
                
                # all_pages_data is a list of lists of categorized text items
                total_rows = 0
                for page_items in all_pages_data:
                    if page_items:  # Only process non-empty page data
                        for item in page_items:
                            writer.writerow([
                                item.get('page_number', ''),
                                item.get('page_name', ''),
                                item.get('page_url', ''),
                                item.get('category', ''),
                                item.get('tag', ''),
                                item.get('order', ''),
                                item.get('text', '')
                            ])
                            total_rows += 1
            
            logger.info(f"✓ Categorized text CSV exported: {csv_file} ({total_rows} rows)")
            return csv_file
        except Exception as e:
            logger.error(f"Error exporting categorized text to CSV: {e}")
            return None

    def create_zip_export(self) -> str:
        """Create a zip file with all scraped content."""
        try:
            zip_filename = f"{self.output_dir}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Walk through the output directory and add all files
                for root, dirs, files in os.walk(self.output_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Create archive name (relative path from parent of output_dir)
                        arcname = os.path.relpath(file_path, os.path.dirname(self.output_dir))
                        zipf.write(file_path, arcname)
                        logger.info(f"  Added to zip: {arcname}")
            
            logger.info(f"✓ Zip export created: {zip_filename}")
            return zip_filename
        except Exception as e:
            logger.error(f"Error creating zip export: {e}")
            return None

    def export_to_json(self, results: Dict) -> str:
        """Export scraping results to JSON format."""
        try:
            json_file = f"{self.output_dir}/reports/report.json"
            Path(f"{self.output_dir}/reports").mkdir(exist_ok=True)
            
            export_data = {
                'metadata': {
                    'url': self.url,
                    'scraped_at': datetime.now().isoformat(),
                    'total_images': len(results.get('images', [])),
                    'total_videos': len(results.get('videos', []))
                },
                'seo_analysis': results.get('seo_analysis', {}),
                'images': results.get('images', []),
                'videos': [
                    {
                        'url': v['url'],
                        'type': v['type'],
                        'title': v.get('title', 'N/A'),
                        'filepath': v.get('filepath', 'N/A')
                    } for v in results.get('videos', [])
                ]
            }
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"JSON report exported to {json_file}")
            return json_file
        except Exception as e:
            logger.error(f"Error exporting JSON: {e}")
            return None

    def export_to_csv(self, results: Dict) -> Tuple[str, str]:
        """Export headers and assets to CSV format."""
        try:
            Path(f"{self.output_dir}/reports").mkdir(exist_ok=True)
            
            # Export headers CSV
            headers_file = f"{self.output_dir}/reports/headers.csv"
            if results.get('seo_analysis', {}).get('headers'):
                headers_data = results['seo_analysis']['headers']
                with open(headers_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Header Level', 'Order', 'Text', 'HTML ID', 'Classes'])
                    
                    for level in range(1, 7):
                        for header in headers_data.get(f'h{level}', []):
                            writer.writerow([
                                f'H{level}',
                                header['order'],
                                header['text'],
                                header.get('html_id', ''),
                                ', '.join(header.get('class', []))
                            ])
            
            logger.info(f"Headers CSV exported to {headers_file}")
            
            # Export assets CSV (images and videos)
            assets_file = f"{self.output_dir}/reports/assets.csv"
            with open(assets_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Type', 'URL', 'Local Path', 'Metadata'])
                
                # Write images
                for img in results.get('images', []):
                    writer.writerow([
                        'Image',
                        img['url'],
                        img.get('filepath', ''),
                        img.get('alt_text', '')
                    ])
                
                # Write videos
                for vid in results.get('videos', []):
                    writer.writerow([
                        'Video',
                        vid['url'],
                        vid.get('filepath', ''),
                        vid.get('title', '')
                    ])
            
            logger.info(f"Assets CSV exported to {assets_file}")
            return headers_file, assets_file
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            return None, None

    def export_to_html(self, results: Dict) -> str:
        """Export comprehensive HTML report."""
        try:
            Path(f"{self.output_dir}/reports").mkdir(exist_ok=True)
            html_file = f"{self.output_dir}/reports/report.html"
            
            seo_data = results.get('seo_analysis', {})
            seo_analysis = seo_data.get('seo_analysis', {})
            headers_data = seo_data.get('headers', {})
            
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Scraping & SEO Analysis Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; }}
        .container {{ max-width: 1000px; margin: 0 auto; padding: 20px; }}
        header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; }}
        header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .metadata {{ font-size: 0.9em; opacity: 0.9; }}
        .section {{ background: white; padding: 25px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .section h2 {{ color: #667eea; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #667eea; }}
        .section h3 {{ color: #555; margin-top: 15px; margin-bottom: 10px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 15px 0; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-card .number {{ font-size: 2em; font-weight: bold; }}
        .stat-card .label {{ font-size: 0.9em; opacity: 0.9; }}
        .seo-score {{ font-size: 3em; font-weight: bold; color: #667eea; }}
        .good {{ color: #27ae60; background: #d5f4e6; padding: 10px; border-radius: 4px; margin: 5px 0; }}
        .warning {{ color: #e67e22; background: #fef5e7; padding: 10px; border-radius: 4px; margin: 5px 0; }}
        .critical {{ color: #e74c3c; background: #fadbd8; padding: 10px; border-radius: 4px; margin: 5px 0; }}
        .recommendation {{ background: #ecf0f1; padding: 10px; margin: 8px 0; border-left: 4px solid #667eea; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        table th, table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        table th {{ background: #667eea; color: white; }}
        table tr:hover {{ background: #f5f5f5; }}
        .hierarchy-tree {{ background: #f9f9f9; padding: 15px; border-radius: 4px; font-family: 'Courier New', monospace; white-space: pre-wrap; word-break: break-all; }}
        .footer {{ text-align: center; color: #666; margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔍 Web Scraping & SEO Analysis Report</h1>
            <div class="metadata">
                <p><strong>URL:</strong> {self.url}</p>
                <p><strong>Analyzed:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </header>

        <div class="section">
            <h2>📊 SEO Analysis Summary</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="number">{seo_analysis.get('content_structure_score', 0)}</div>
                    <div class="label">Content Score</div>
                </div>
                <div class="stat-card">
                    <div class="number">{seo_analysis.get('h1_count', 0)}</div>
                    <div class="label">H1 Tags</div>
                </div>
                <div class="stat-card">
                    <div class="number">{len(headers_data.get('h2', []))}</div>
                    <div class="label">H2 Tags</div>
                </div>
                <div class="stat-card">
                    <div class="number">{len(results.get('images', []))}</div>
                    <div class="label">Images</div>
                </div>
            </div>
            
            <h3>H1 Status</h3>
            <div class="{'critical' if 'CRITICAL' in seo_analysis.get('h1_status', '') else 'warning' if 'WARNING' in seo_analysis.get('h1_status', '') else 'good'}">
                {seo_analysis.get('h1_status', 'Unknown')}
            </div>
            
            {f'<h3>Issues Found</h3><div>' + ''.join([f'<div class="critical">{issue}</div>' for issue in seo_analysis.get('hierarchy_issues', [])]) + '</div>' if seo_analysis.get('hierarchy_issues') else ''}
            
            {f'<h3>Recommendations</h3><div>' + ''.join([f'<div class="recommendation">✓ {rec}</div>' for rec in seo_analysis.get('recommendations', [])]) + '</div>' if seo_analysis.get('recommendations') else ''}
        </div>

        <div class="section">
            <h2>📋 Header Hierarchy</h2>
            <table>
                <tr>
                    <th>Level</th>
                    <th>Count</th>
                    <th>First Header</th>
                </tr>
                {"".join([f'<tr><td>H{i}</td><td>{len(headers_data.get(f"h{i}", []))}</td><td>{headers_data.get(f"h{i}", [{}])[0].get("text", "N/A")}</td></tr>' for i in range(1, 7)])}
            </table>
        </div>

        <div class="section">
            <h2>🎯 Content Statistics</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="number">{len(results.get('images', []))}</div>
                    <div class="label">Images Downloaded</div>
                </div>
                <div class="stat-card">
                    <div class="number">{len(results.get('videos', []))}</div>
                    <div class="label">Videos Found</div>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Report files: JSON | CSV | HTML</p>
        </div>
    </div>
</body>
</html>
            """
            
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"HTML report exported to {html_file}")
            return html_file
        except Exception as e:
            logger.error(f"Error exporting HTML: {e}")
            return None

    def export_to_pdf(self, results: Dict) -> str:
        """Export comprehensive PDF report."""
        try:
            Path(f"{self.output_dir}/reports").mkdir(exist_ok=True)
            pdf_file = f"{self.output_dir}/reports/report.pdf"
            
            doc = SimpleDocTemplate(pdf_file, pagesize=letter,
                                    rightMargin=0.75*inch, leftMargin=0.75*inch,
                                    topMargin=0.75*inch, bottomMargin=0.75*inch)
            
            story = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#667eea'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            story.append(Paragraph("Web Scraping & SEO Analysis Report", title_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Metadata
            metadata_style = ParagraphStyle(
                'Metadata',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
            story.append(Paragraph(f"URL: {self.url}", metadata_style))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", metadata_style))
            story.append(Spacer(1, 0.3*inch))
            
            # Executive Summary
            story.append(Paragraph("Executive Summary", styles['Heading2']))
            
            mode = results.get('mode', 'single-page')
            if mode == 'multi-page':
                pages = results.get('pages', [])
                total_img = len(results.get('total_images', []))
                total_vid = len(results.get('total_videos', []))
                
                summary_text = f"""
                <b>Scraping Mode:</b> Multi-Page<br/>
                <b>Pages Scraped:</b> {len(pages)}<br/>
                <b>Total Images:</b> {total_img}<br/>
                <b>Total Videos:</b> {total_vid}<br/>
                """
            else:
                total_img = len(results.get('images', []))
                total_vid = len(results.get('videos', []))
                
                summary_text = f"""
                <b>Scraping Mode:</b> Single Page<br/>
                <b>Images Downloaded:</b> {total_img}<br/>
                <b>Videos Found:</b> {total_vid}<br/>
                """
            
            story.append(Paragraph(summary_text, styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            # SEO Analysis
            story.append(Paragraph("SEO Analysis", styles['Heading2']))
            
            seo_data = results.get('seo_analysis', {})
            seo_analysis = seo_data.get('seo_analysis', {})
            headers_data = seo_data.get('headers', {})
            
            if mode == 'multi-page':
                seo_text = f"""
                <b>Total Pages Analyzed:</b> {seo_analysis.get('total_pages', 0)}<br/>
                <b>Total H1 Tags:</b> {seo_analysis.get('total_h1', 0)}<br/>
                <b>Total H2 Tags:</b> {seo_analysis.get('total_h2', 0)}<br/>
                """
            else:
                seo_text = f"""
                <b>H1 Status:</b> {seo_analysis.get('h1_status', 'Unknown')}<br/>
                <b>Content Structure Score:</b> {seo_analysis.get('content_structure_score', 0)}/100<br/>
                """
            
            story.append(Paragraph(seo_text, styles['Normal']))
            
            # Header Hierarchy Table
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("Header Distribution", styles['Heading3']))
            
            header_data = [['Header Level', 'Count', 'Examples']]
            for level in range(1, 7):
                headers_list = headers_data.get(f'h{level}', [])
                count = len(headers_list)
                # Get first 2 examples
                examples = ', '.join([str(h.get('text', 'N/A') if isinstance(h, dict) else h)[:30] 
                                    for h in headers_list[:2]])
                if len(headers_list) > 2:
                    examples += f"... +{len(headers_list)-2} more"
                
                header_data.append([f'H{level}', str(count), examples])
            
            header_table = Table(header_data, colWidths=[1.5*inch, 1*inch, 3.5*inch])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
            ]))
            story.append(header_table)
            
            # Recommendations
            if seo_analysis.get('recommendations'):
                story.append(Spacer(1, 0.3*inch))
                story.append(Paragraph("SEO Recommendations", styles['Heading3']))
                rec_text = '<br/>'.join([f"• {rec}" for rec in seo_analysis.get('recommendations', [])])
                story.append(Paragraph(rec_text, styles['Normal']))
            
            # Images Section
            story.append(Spacer(1, 0.3*inch))
            story.append(PageBreak())
            story.append(Paragraph("Assets Summary", styles['Heading2']))
            
            if mode == 'multi-page':
                total_img = len(results.get('total_images', []))
                total_vid = len(results.get('total_videos', []))
            else:
                total_img = len(results.get('images', []))
                total_vid = len(results.get('videos', []))
            
            assets_text = f"""
            <b>Total Images:</b> {total_img}<br/>
            <b>Total Videos:</b> {total_vid}<br/>
            """
            story.append(Paragraph(assets_text, styles['Normal']))
            
            # Page Details (for multi-page)
            if mode == 'multi-page':
                story.append(Spacer(1, 0.3*inch))
                story.append(Paragraph("Detailed Page Analysis", styles['Heading2']))
                
                pages = results.get('pages', [])
                for page_data in pages:
                    page_text = f"""
                    <b>Page {page_data.get('page_number')}:</b> {page_data.get('url', 'N/A')}<br/>
                    Images: {len(page_data.get('images', []))} | 
                    Videos: {len(page_data.get('videos', []))} | 
                    H1: {page_data.get('seo', {}).get('seo_analysis', {}).get('h1_count', 0)}<br/>
                    """
                    story.append(Paragraph(page_text, styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
            
            # Footer
            story.append(Spacer(1, 0.5*inch))
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
            story.append(Paragraph(f"Generated by Web Scraper on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))
            
            # Build PDF
            doc.build(story)
            logger.info(f"PDF report exported to {pdf_file}")
            return pdf_file
        except Exception as e:
            logger.error(f"Error exporting PDF: {e}")
            return None

    def export_all_formats(self, results: Dict) -> Dict:
        """Export results to all available formats."""
        exports = {
            'json': self.export_to_json(results),
            'csv': self.export_to_csv(results),
            'html': self.export_to_html(results),
            'pdf': self.export_to_pdf(results),
            'txt': f"{self.output_dir}/text/seo_header_analysis.txt"
        }
        
        # Export categorized text to CSV
        categorized_text = results.get('categorized_text', [])
        if categorized_text:
            categorized_csv = self.export_categorized_text_to_csv(categorized_text)
            if categorized_csv:
                exports['categorized_text_csv'] = categorized_csv
        
        # Create zip export of all scraped content
        zip_file = self.create_zip_export()
        if zip_file:
            exports['zip_export'] = zip_file
        
        return exports

    def extract_text(self, html: str) -> str:
        """Extract all text content from the page."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text(separator='\n', strip=True)
            
            # Save text
            output_file = f"{self.output_dir}/text/content.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            logger.info(f"Text extracted and saved to {output_file}")
            return text
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return None

    def extract_and_download_images(self, html: str, page_url: str = None) -> List[Dict]:
        """Extract and download all images from the page."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            images = soup.find_all('img')
            
            logger.info(f"Extracting images from: {page_url or self.url}")
            logger.info(f"Saving to folder: {self.output_dir}/images/")
            
            downloaded_images = []
            for idx, img in enumerate(images, 1):
                img_url = img.get('src') or img.get('data-src')
                if not img_url:
                    continue
                
                # Normalize and fix malformed URLs
                img_url = self._normalize_url(img_url, page_url)
                
                alt_text = img.get('alt', 'No description')
                
                try:
                    response = self.session.get(img_url, timeout=10)
                    response.raise_for_status()
                    
                    # Determine filename
                    parsed_url = urlparse(img_url)
                    filename = parsed_url.path.split('/')[-1] or f"image_{idx}.jpg"
                    
                    filepath = f"{self.output_dir}/images/{filename}"
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    logger.info(f"✓ Downloaded: {filename} → {filepath}")
                    
                    # Convert to webp
                    webp_filepath = self._convert_to_webp(filepath, filename)
                    logger.info(f"✓ Converted to WebP: {webp_filepath}")
                    
                    downloaded_images.append({
                        'url': img_url,
                        'filepath': webp_filepath,
                        'original_filepath': filepath,
                        'alt_text': alt_text
                    })
                except Exception as e:
                    logger.warning(f"✗ Failed to download image {img_url}: {e}")
                    # Queue for retry
                    self.failed_downloads.append({
                        'url': img_url,
                        'type': 'image',

                        'alt_text': alt_text
                    })
            
            logger.info(f"Completed: Downloaded {len(downloaded_images)} images from this page")
            return downloaded_images
        except Exception as e:
            logger.error(f"Error extracting images: {e}")
            return []
    
    def _convert_to_webp(self, filepath: str, original_filename: str) -> str:
        """Convert image to webp format."""
        try:
            from PIL import Image
            
            # Open the image
            img = Image.open(filepath)
            
            # Create webp filename
            webp_filename = original_filename.rsplit('.', 1)[0] + '.webp'
            webp_filepath = f"{self.output_dir}/images/{webp_filename}"
            
            # Convert and save as webp
            img.save(webp_filepath, 'WEBP', quality=85)
            logger.info(f"  → Converted to WebP: {webp_filename} ({webp_filepath})")
            
            # Delete original file
            try:
                os.remove(filepath)
                logger.info(f"  → Deleted original: {original_filename}")
            except:
                pass
            
            return webp_filepath
        except Exception as e:
            logger.warning(f"Could not convert {original_filename} to WebP: {e}")
            return filepath

    def extract_and_download_videos(self, html: str, page_url: str = None) -> List[Dict]:
        """Extract video sources and download direct video files."""
        try:
            logger.info(f"Extracting videos from: {page_url or self.url}")
            logger.info(f"Saving to folder: {self.output_dir}/videos/")
            
            soup = BeautifulSoup(html, 'html.parser')
            videos = []
            video_extensions = ['.mp4', '.webm', '.mov', '.avi', '.mkv', '.flv']
            
            # Find video tags with direct file links
            for video in soup.find_all('video'):
                sources = video.find_all('source')
                for source in sources:
                    video_url = source.get('src')
                    if video_url:
                        # Normalize URL
                        video_url = self._normalize_url(video_url, page_url)
                        video_info = {
                            'url': video_url,
                            'type': 'direct_video',
                            'title': video.get('title', 'Video')
                        }
                        videos.append(video_info)
                        
                        # Try to download direct video links
                        if any(ext in video_url.lower() for ext in video_extensions):
                            self._download_video(video_url, video_info)
            
            # Find iframes (YouTube, Vimeo, etc.) - these are typically embedded
            for iframe in soup.find_all('iframe'):
                iframe_url = iframe.get('src')
                if iframe_url and any(x in iframe_url for x in ['youtube', 'vimeo', 'dailymotion']):
                    videos.append({
                        'url': iframe_url,
                        'type': 'embedded_iframe',
                        'title': iframe.get('title', 'Embedded video')
                    })
            
            # Find all anchor tags that point to video files
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if any(ext in href.lower() for ext in video_extensions):
                    href = self._normalize_url(href, page_url)
                    videos.append({
                        'url': href,
                        'type': 'video_link',
                        'title': link.get_text(strip=True) or 'Download'
                    })
                    self._download_video(href, {'url': href, 'title': link.get_text(strip=True)})
            
            logger.info(f"Found {len(videos)} video sources")
            
            # Save video URLs to file
            with open(f"{self.output_dir}/videos/video_urls.txt", 'w', encoding='utf-8') as f:
                for idx, video in enumerate(videos, 1):
                    f.write(f"{idx}. Type: {video['type']}\n")
                    f.write(f"   Title: {video.get('title', 'N/A')}\n")
                    f.write(f"   URL: {video['url']}\n\n")
            
            return videos
        except Exception as e:
            logger.error(f"Error extracting videos: {e}")
            return []
    
    def _download_video(self, video_url: str, video_info: Dict) -> bool:
        """Download video file from URL."""
        try:
            logger.info(f"Attempting to download video: {video_url}")
            response = self.session.get(video_url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Get filename from URL
            parsed_url = urlparse(video_url)
            filename = parsed_url.path.split('/')[-1]
            if not any(ext in filename.lower() for ext in ['.mp4', '.webm', '.mov', '.avi', '.mkv', '.flv']):
                filename = f"video_{int(time.time())}.mp4"
            
            filepath = f"{self.output_dir}/videos/{filename}"
            
            # Download with progress
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size:
                            progress = (downloaded / total_size) * 100
                            logger.info(f"  Download progress: {progress:.1f}%")
            
            logger.info(f"✓ Video downloaded: {filename} → {filepath}")
            video_info['filepath'] = filepath
            video_info['size'] = os.path.getsize(filepath)
            return True
        except Exception as e:
            logger.warning(f"✗ Failed to download video {video_url}: {e}")
            # Queue for retry
            self.failed_downloads.append({
                'url': video_url,
                'type': 'video',
                'title': video_info.get('title', 'Unknown')
            })
            return False

    def scrape(self, multi_page: bool = False) -> Dict:
        """Main scraping method.
        
        Args:
            multi_page: If True, scrape multiple pages. If False, scrape only the main page.
        """
        if multi_page:
            # Multi-page crawling
            crawl_results = self.crawl_pages()
            if not crawl_results:
                return {'success': False}
            
            results = {
                'success': True,
                'mode': 'multi-page',
                'pages': crawl_results.get('pages', []),
                'total_images': crawl_results.get('total_images', []),
                'total_videos': crawl_results.get('total_videos', []),
                'categorized_text': crawl_results.get('categorized_text', []),
                'seo_analysis': {
                    'headers': crawl_results.get('all_headers', {}),
                    'seo_analysis': crawl_results.get('seo_analysis', {})
                }
            }
        else:
            # Single page scraping
            html = self.fetch_page()
            if not html:
                return {'success': False}
            
            page_categorized_text = self.extract_text_by_category(html, self.url, 1, 'home')
            
            results = {
                'success': True,
                'mode': 'single-page',
                'text': self.extract_text(html),
                'seo_analysis': self.extract_seo_headers(html),
                'images': self.extract_and_download_images(html, self.url),
                'videos': self.extract_and_download_videos(html, self.url),
                'categorized_text': [page_categorized_text]
            }
        
        # Retry failed downloads
        logger.info(f"Retrying {len(self.failed_downloads)} failed downloads...")
        self._retry_failed_downloads()
        
        # Export to all formats
        results['exports'] = self.export_all_formats(results)
        results['failed_downloads'] = self.failed_downloads
        
        logger.info(f"Scraping complete. Images: {len(results.get('total_images', results.get('images', [])))}, Videos: {len(results.get('total_videos', results.get('videos', [])))}")
        logger.info(f"Failed downloads (unable to recover): {len(self.failed_downloads)}")
        return results
    
    def _retry_failed_downloads(self):
        """Retry downloading failed images and videos."""
        if not self.failed_downloads:
            return
        
        # Deduplicate by URL
        unique_failed = {}
        for item in self.failed_downloads:
            url = item['url']
            if url not in unique_failed:
                unique_failed[url] = item
        
        logger.info(f"Retrying {len(unique_failed)} unique failed downloads with retry strategy...")
        
        retry_queue = list(unique_failed.values())
        max_retries = 3
        retry_count = 0
        
        while retry_queue and retry_count < max_retries:
            retry_count += 1
            logger.info(f"Retry attempt {retry_count}/{max_retries}")
            time.sleep(2)  # Wait before retry
            
            newly_failed = []
            
            for item in retry_queue:
                url = item['url']
                item_type = item['type']
                
                try:
                    logger.info(f"  Retrying {item_type}: {url}")
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    
                    if item_type == 'image':
                        # Save image
                        parsed_url = urlparse(url)
                        filename = parsed_url.path.split('/')[-1] or f"image_{int(time.time())}.jpg"
                        filepath = f"{self.output_dir}/images/{filename}"
                        
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        
                        # Convert to webp
                        webp_filepath = self._convert_to_webp(filepath, filename)
                        logger.info(f"    ✓ Successfully recovered image: {filename}")
                    
                    elif item_type == 'video':
                        # Save video
                        parsed_url = urlparse(url)
                        filename = parsed_url.path.split('/')[-1] or f"video_{int(time.time())}.mp4"
                        filepath = f"{self.output_dir}/videos/{filename}"
                        
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        
                        logger.info(f"    ✓ Successfully recovered video: {filename}")
                
                except Exception as e:
                    logger.warning(f"    ✗ Still failed: {str(e)}")
                    newly_failed.append(item)
            
            retry_queue = newly_failed
        
        # Update failed_downloads with items that couldn't be recovered
        self.failed_downloads = retry_queue
        
        if retry_queue:
            logger.warning(f"Could not recover {len(retry_queue)} downloads after {max_retries} retries")
        else:
            logger.info("✓ All failed downloads recovered successfully!")

    def create_full_directory_structure(self) -> bool:
        """Create the complete directory structure for the scraping project."""
        try:
            # Directory structure to create
            directories = [
                # cwcwake_requested_run structure
                "cwcwake_requested_run/default/landing-pages",
                "cwcwake_requested_run/downloaded_images/web",
                "cwcwake_requested_run/downloaded_images/web_booking.php",
                "cwcwake_requested_run/downloaded_images/web_gallery-caramoan.php",
                "cwcwake_requested_run/downloaded_images/web_gallery-cwc.php",
                "cwcwake_requested_run/downloaded_images/web_gallery-events-halloween.php",
                "cwcwake_requested_run/downloaded_images/web_gallery-events.php",
                "cwcwake_requested_run/downloaded_images/web_gallery-lifestyle.php",
                "cwcwake_requested_run/downloaded_images/web_gallery-ridingshots.php",
                "cwcwake_requested_run/downloaded_images/web_gallery.php",
                "cwcwake_requested_run/downloaded_images/web_room-dwell.php",
                
                # scraped_content structure
                "scraped_content/images",
                "scraped_content/pages/page_1_web",
                "scraped_content/pages/page_10_gallery_cwcphp",
                "scraped_content/pages/page_11_gallery_events_adcongressphp",
                "scraped_content/pages/page_12_gallery_events_asian_tournaments_1stphp",
                "scraped_content/pages/page_13_gallery_events_asian_tournaments_2ndphp",
                "scraped_content/pages/page_14_gallery_events_asian_tournamentsphp",
                "scraped_content/pages/page_15_gallery_events_camsur_marathon_2010php",
                "scraped_content/pages/page_16_gallery_events_halloweenphp",
                "scraped_content/pages/page_17_gallery_events_halloween_costumesphp",
                "scraped_content/pages/page_18_gallery_events_marathonphp",
                "scraped_content/pages/page_19_gallery_events_nationals_awardingphp",
                "scraped_content/pages/page_2_about_us",
                "scraped_content/pages/page_20_gallery_events_nationals_lifestylephp",
                "scraped_content/pages/page_21_gallery_events_nationals_ridingshotsphp",
                "scraped_content/pages/page_22_gallery_events_nationalsphp",
                "scraped_content/pages/page_23_gallery_events_uwc2011_blacklightphp",
                "scraped_content/pages/page_24_gallery_events_uwc2011_comicstripphp",
                "scraped_content/pages/page_25_gallery_events_wwa2009_retrodancephp",
                "scraped_content/pages/page_26_gallery_eventsphp",
                "scraped_content/pages/page_27_gallery_lifestyle_feb2015php",
                "scraped_content/pages/page_28_gallery_lifestyle_jan2015php",
                "scraped_content/pages/page_29_gallery_lifestyle_june2015php",
                "scraped_content/pages/page_3_amenities",
                "scraped_content/pages/page_30_gallery_lifestyle_mar2015php",
                "scraped_content/pages/page_31_gallery_lifestyle_may2015php",
                "scraped_content/pages/page_32_gallery_lifestyle_sept2015php",
                "scraped_content/pages/page_33_gallery_lifestylephp",
                "scraped_content/pages/page_34_gallery_ridingshots_2018php",
                "scraped_content/pages/page_35_gallery_ridingshots_jan2015php",
                "scraped_content/pages/page_36_gallery_ridingshots_june2015php",
                "scraped_content/pages/page_37_gallery_ridingshots_may2015php",
                "scraped_content/pages/page_38_gallery_ridingshots_prophp",
                "scraped_content/pages/page_39_gallery_ridingshots_sept2015php",
                "scraped_content/pages/page_4_booking",
                "scraped_content/pages/page_40_gallery_ridingshotsphp",
                "scraped_content/pages/page_41_galleryphp",
                "scraped_content/pages/page_42_getting_aroundphp",
                "scraped_content/pages/page_43_rates",
                "scraped_content/pages/page_44_room_cabana",
                "scraped_content/pages/page_45_room_cabanaphp",
                "scraped_content/pages/page_46_room_dwell",
                "scraped_content/pages/page_47_room_dwellphp",
                "scraped_content/reports",
                "scraped_content/text",
                "scraped_content/videos",
                
                # web-scraper structure
                "web-scraper",
            ]
            
            # Create all directories
            created_count = 0
            for directory in directories:
                dir_path = Path(directory)
                dir_path.mkdir(parents=True, exist_ok=True)
                created_count += 1
            
            logger.info(f"✓ Directory structure created successfully! ({created_count} directories)")
            return True
        except Exception as e:
            logger.error(f"Error creating directory structure: {e}")
            return False


if __name__ == "__main__":
    # Example usage
    URL = "https://cwcwake.com/"
    scraper = WebScraper(URL)
    results = scraper.scrape()
    
    print(f"\n{'='*70}")
    print("SCRAPING & SEO ANALYSIS RESULTS")
    print(f"{'='*70}")
    
    # SEO Analysis
    if results.get('seo_analysis'):
        seo = results['seo_analysis']['seo_analysis']
        print(f"\n📊 SEO ANALYSIS")
        print(f"   H1 Status: {seo['h1_status']}")
        print(f"   Content Score: {seo['content_structure_score']}/100")
        if seo['recommendations']:
            print(f"   Recommendations:")
            for rec in seo['recommendations']:
                print(f"     • {rec}")
    
    print(f"\n📷 Images downloaded: {len(results.get('images', []))}")
    print(f"🎥 Videos found: {len(results.get('videos', []))}")
    print(f"\n✅ Content saved to: {scraper.output_dir}")
    print(f"   📄 SEO Report: {scraper.output_dir}/text/seo_header_analysis.txt")
