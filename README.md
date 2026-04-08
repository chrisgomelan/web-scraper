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
- **Single Page**: Analyze one URL in detail
- **Multi-Page Auto-discovery**: The app finds and scrapes linked pages automatically
- **Custom URL List**: Load URLs from `sample_urls.txt` or your own file

### Key Functions

#### **Single Page Mode**
1. Enter a URL
2. Click "Start Scraping"
3. Review results and export reports

#### **Multi-Page Mode**
1. Enter the starting URL
2. Set the maximum number of pages to scrape
3. The app discovers links and scrapes them automatically

#### **Custom URL Mode**
1. Prepare a text file with one URL per line
2. Click "Load URLs from File"
3. Click "Start Scraping"

### Exporting Data

After scraping, you can export in multiple formats:
- **JSON**: Structured data with metadata
- **CSV**: Spreadsheet-compatible format (headers, assets, categorized text)
- **HTML**: Interactive visual report
- **PDF**: Professional downloadable report
- **ZIP**: Complete archive of all content

## Directory Structure

Generated content is organized as follows:

```
scraped_content/
├── images/           # Downloaded images
├── videos/           # Downloaded videos
├── text/             # Extracted text content
├── pages/            # Individual page HTML/data
└── reports/          # Exported reports (JSON, CSV, HTML, PDF)
```

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

### User Agent
The app uses a standard browser user agent to avoid blocking:
```
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
```

### Timeouts & Retries
- Connection timeout: 30 seconds
- Max retries for failed downloads: 3
- Automatic retry with backoff for network issues

## Advanced Usage

### Using as a Module

```python
from scraper import WebScraper

# Single page scraping
scraper = WebScraper(url="https://example.com")
results = scraper.scrape_page(url="https://example.com")

# Export to different formats
scraper.export_to_json(results)
scraper.export_to_csv(results)
scraper.export_to_html(results)
scraper.export_to_pdf(results)

# Create directory structure
scraper.create_full_directory_structure()
```

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
