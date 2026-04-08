# Web Scraper & SEO Analyzer

A powerful, easy-to-use desktop application for scraping websites and analyzing their SEO performance. Built with Python and Tkinter, it provides a user-friendly GUI for extracting content, downloading media, and generating comprehensive reports.

## Features

### 🔍 **Web Scraping Capabilities**
- **Single Page Scraping**: Extract content from a specific URL
- **Multi-Page Scraping**: Auto-discover and scrape linked pages across a domain
- **Custom URL Lists**: Scrape a batch of URLs from a file
- **Smart Media Download**: Automatically download and organize images and videos

### 📊 **SEO Analysis**
- **Header Hierarchy Analysis**: Validate H1-H6 tag structure and best practices
- **Content Structure Scoring**: Evaluate page organization and SEO compliance
- **Meta Tag Detection**: Extract and analyze meta information
- **Link Analysis**: Identify internal and external links
- **Accessibility Recommendations**: Get actionable SEO improvements

### 📁 **Content Organization**
- **Automatic Directory Structure**: Create organized folders for content and media
- **Categorized Storage**: Separate images, videos, text, and pages
- **Metadata Preservation**: Keep track of URLs and context

### 📈 **Comprehensive Reports**
- **Multiple Export Formats**: JSON, CSV, HTML, and PDF reports
- **Header Reports**: Detailed header hierarchy documentation
- **Asset Reports**: Complete inventory of images and videos
- **Text Extraction**: Categorized text content from all pages
- **ZIP Export**: Package all content for easy sharing

## Installation

### Requirements
- Python 3.7+
- pip (Python package manager)

### Setup

1. **Clone the repository**
   ```bash
   git clone git@github.com:chrisgomelan/web-scraper.git
   cd web-scraper
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the GUI Application

```bash
python gui_app.py
```

This launches the user-friendly desktop interface. Choose from three scraping modes:
- **Single Page**: Extract content from one specific URL only
- **Multi-Page Auto-discovery**: The app finds and scrapes linked pages within the same domain
- **Custom URL List**: Scrape multiple URLs from a file (`sample_urls.txt` or your own)

⚠️ **Important**: `sample_urls.txt` is **ONLY used in Custom URL List mode**. Single Page and Auto-discovery modes ignore it.

### Scraping Modes Comparison

| Feature | Single Page | Auto-Discovery | Custom URLs |
|---------|-------------|----------------|------------|
| **Input** | One URL above | One starting URL | File with multiple URLs |
| **Discovers links?** | ❌ No | ✅ Yes (same domain only) | ❌ No |
| **Uses sample_urls.txt?** | ❌ No | ❌ No | ✅ Yes |
| **Best for** | Single page analysis | Full website crawl | Multiple unrelated sites |
| **Domain constraint** | N/A | ✅ Yes (only same domain) | ❌ No (any domain) |
| **Example** | Analyze 1 page | Scrape all pages of a website | Scrape 10 different websites |

### Key Functions

#### **Single Page Mode**
- Scrapes only the URL you enter
- `sample_urls.txt` is ignored
- Perfect for detailed analysis of one page
1. Enter a URL
2. Click "Start Scraping"
3. Review results and export reports

#### **Multi-Page Auto-discovery Mode**
- Starts from your URL and automatically discovers linked pages
- **Only follows links within the same domain** (e.g., bps.edu.ph → stays on bps.edu.ph)
- `sample_urls.txt` is ignored
1. Enter the starting URL
2. Click "Start Scraping"
3. The app discovers and scrapes linked pages automatically

#### **Custom URL List Mode** ✓ Uses sample_urls.txt
- Scrapes multiple URLs from a file
- One URL per line
- Useful for scraping multiple unrelated websites
1. Switch to "Custom URL List" mode
2. Click "📋 Load URLs from File" and select your file
3. Or paste URLs directly in the text area
4. Click "Start Scraping"

### Exporting Data

After scraping, you can export in multiple formats:
- **JSON**: Structured data with metadata
- **CSV**: Spreadsheet-compatible format (headers, assets, categorized text)
- **HTML**: Interactive visual report
- **PDF**: Professional downloadable report
- **ZIP**: Complete archive of all content

## Directory Structure

Each scraping session creates an **isolated folder per website** to prevent content mixing:

```
scraped_content/
├── bps.edu.ph_2026-04-08_14-05-23/    # Isolated folder for BPS
│   ├── pages/
│   │   ├── page_1_home/
│   │   │   ├── images/
│   │   │   ├── videos/
│   │   │   └── seo_analysis.txt
│   │   ├── page_2_about/
│   │   └── ...
│   ├── images/
│   ├── videos/
│   ├── text/
│   └── reports/
│       ├── report.json
│       ├── report.html
│       ├── report.pdf
│       └── headers.csv
│
└── cwcwake.com_2026-04-08_15-30-12/   # Isolated folder for CWC Wake
    ├── pages/
    ├── images/
    ├── videos/
    ├── text/
    └── reports/
```

**Benefits of isolated folders:**
- ✅ No content mixing from different websites
- ✅ Each scrape is independent and timestamped
- ✅ ZIP exports only contain the current scrape
- ✅ Easy to manage and delete old scrapes

## File Structure

- `gui_app.py` - Main application with GUI interface
- `scraper.py` - Core scraping engine and utilities
- `requirements.txt` - Python dependencies
- `sample_urls.txt` - Example URLs for batch processing

## Requirements

See `requirements.txt` for complete dependencies. Key packages:
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `reportlab` - PDF generation
- `pillow` - Image processing
- `tkinter` - GUI (included with Python)

## Configuration

### Domain Filtering
When using **Auto-discovery mode**, the scraper is smart about staying on the same domain:
- Starts from your provided URL (e.g., `https://bps.edu.ph/`)
- Only follows internal links that belong to the same domain
- Ignores external links to other websites
- Ensures clean, focused scrapes without mixing content

### User Agent
The app uses a standard browser user agent to avoid blocking:
```
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
```

### Timeouts & Retries
- Connection timeout: 30 seconds
- Max retries for failed downloads: 3
- Automatic retry with backoff for network issues

### Image Format Conversion
- All JPG/PNG images are automatically converted to **WebP** format
- Provides better compression and faster loading
- Original files are deleted after conversion

## Advanced Usage

### Using as a Module

```python
from scraper import WebScraper

# Single page scraping (sample_urls.txt is IGNORED)
scraper = WebScraper(url="https://example.com", max_pages=1)
results = scraper.scrape(multi_page=False)

# Auto-discovery mode (sample_urls.txt is IGNORED, only discovers from the starting URL)
scraper = WebScraper(url="https://example.com", max_pages=5)
results = scraper.scrape(multi_page=True)

# Custom URL mode (uses sample_urls.txt or provided custom_urls)
urls = ["https://site1.com", "https://site2.com"]
scraper = WebScraper(url="https://site1.com", max_pages=999, custom_urls=urls)
results = scraper.scrape(multi_page=True)

# Export to different formats
scraper.export_to_json(results)
scraper.export_to_csv(results)
scraper.export_to_html(results)
scraper.export_to_pdf(results)
```

### Output Folder Structure

Each scrape creates an isolated folder with the domain name and timestamp:
```
{output_dir}/{domain}_{YYYY-MM-DD_HH-MM-SS}/
```

Example: `scraped_content/bps.edu.ph_2026-04-08_14-05-23/`

This ensures:
- No accidental mixing of content from different websites
- Easy cleanup of old scrapes
- ZIP exports contain only current content
- Multiple simultaneous scrapes won't conflict

### Batch Processing

```python
urls = ["https://example1.com", "https://example2.com"]
scraper = WebScraper(url="https://example1.com", custom_urls=urls)
```

## Error Handling

The app includes robust error handling:
- Network timeout recovery with automatic retries
- Invalid URL detection
- Missing dependencies alerts
- Detailed logging of all operations

## Output Examples

### Generated Reports
- **Categorized Text CSV**: Organized text content by page
- **Headers CSV**: All heading tags with hierarchy information
- **Assets CSV**: Image and video inventory
- **HTML Report**: Visual dashboard with statistics
- **PDF Report**: Professional formatted document

## Tips & Best Practices

1. **Start Small**: Test with a single page before scraping large sites
2. **Check robots.txt**: Respect website scraping policies
3. **Reasonable Delays**: Don't overwhelm servers with rapid requests
4. **Use Filters**: Limit pages to prevent excessive data collection
5. **Monitor Progress**: Watch the GUI output window for real-time updates

## Troubleshooting

### "Module not found" Error
```bash
pip install -r requirements.txt
```

### Connection Timeouts
- Check your internet connection
- The app automatically retries failed downloads
- Try scraping fewer pages

### Permission Denied Errors
- Ensure the output directory is writable
- Check file permissions in `scraped_content/`

### Large File Size
- Use the ZIP export to compress all content
- Remove unnecessary media files before archiving

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License.

## Support

For issues, feature requests, or questions, please open an issue on GitHub.

---

**Happy Scraping!** 🚀
