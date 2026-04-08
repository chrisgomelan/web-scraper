import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
from scraper import WebScraper
import os
from datetime import datetime
import webbrowser

class WebScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Scraper & SEO Analyzer")
        self.root.geometry("900x750")
        self.root.configure(bg="#f0f0f0")
        
        self.scraper = None
        self.results = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the GUI interface."""
        
        # Header Frame
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(header_frame, text="🔍 Web Scraper & SEO Analyzer", font=("Arial", 16, "bold")).pack(anchor=tk.W)
        
        # URL Input Frame
        url_frame = ttk.LabelFrame(self.root, text="URL Settings", padding=10)
        url_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(url_frame, text="Enter URL:").grid(row=0, column=0, sticky=tk.W)
        self.url_entry = ttk.Entry(url_frame, width=50)
        self.url_entry.grid(row=0, column=1, sticky=tk.EW, padx=5)
        self.url_entry.insert(0, "https://cwcwake.com/")
        url_frame.columnconfigure(1, weight=1)
        
        # Scraping Mode Frame
        mode_frame = ttk.LabelFrame(self.root, text="Scraping Mode", padding=10)
        mode_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.mode_var = tk.StringVar(value="single")
        ttk.Radiobutton(mode_frame, text="Single Page", variable=self.mode_var, value="single", command=self.update_mode).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Multiple Pages (Auto-discover)", variable=self.mode_var, value="multi", command=self.update_mode).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Custom URL List", variable=self.mode_var, value="custom", command=self.update_mode).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(mode_frame, text="📋 Load URLs from File", command=self.load_urls_file).pack(side=tk.LEFT, padx=10)
        
        # Custom URLs Frame (initially hidden)
        self.custom_urls_frame = ttk.LabelFrame(self.root, text="Custom URLs (one per line)", padding=10)
        self.custom_urls_text = scrolledtext.ScrolledText(self.custom_urls_frame, height=6, width=80)
        self.custom_urls_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # URL count label
        self.url_count_label = ttk.Label(self.custom_urls_frame, text="0 URLs loaded")
        self.url_count_label.pack(anchor=tk.W, padx=5, pady=5)
        self.custom_urls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Control Buttons Frame
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="▶ Start Scraping", command=self.start_scraping)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="⏹ Stop", command=self.stop_scraping, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = ttk.Button(button_frame, text="🗑 Clear", command=self.clear_output)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        self.open_folder_button = ttk.Button(button_frame, text="📂 Open Folder", command=self.open_output_folder, state=tk.DISABLED)
        self.open_folder_button.pack(side=tk.LEFT, padx=5)
        
        # Progress Frame
        progress_frame = ttk.LabelFrame(self.root, text="Progress", padding=10)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(progress_frame, text="Ready", foreground="blue")
        self.status_label.pack(anchor=tk.W)
        
        # Output Tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Summary Tab
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text="Summary")
        self.summary_text = scrolledtext.ScrolledText(summary_frame, height=15, width=80, wrap=tk.WORD)
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # SEO Analysis Tab
        seo_frame = ttk.Frame(notebook)
        notebook.add(seo_frame, text="SEO Analysis")
        self.seo_text = scrolledtext.ScrolledText(seo_frame, height=15, width=80, wrap=tk.WORD)
        self.seo_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Reports Tab
        reports_frame = ttk.Frame(notebook)
        notebook.add(reports_frame, text="Reports")
        
        reports_button_frame = ttk.Frame(reports_frame)
        reports_button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(reports_button_frame, text="📄 View HTML Report", command=self.open_html_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(reports_button_frame, text="📊 View JSON Report", command=self.open_json_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(reports_button_frame, text="📋 View CSV Headers", command=self.open_csv_headers).pack(side=tk.LEFT, padx=5)
        ttk.Button(reports_button_frame, text="📑 View PDF Report", command=self.open_pdf_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(reports_button_frame, text="📈 View Text CSV", command=self.open_categorized_text_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(reports_button_frame, text="📦 Open ZIP Export", command=self.open_zip_export).pack(side=tk.LEFT, padx=5)
        
        self.reports_text = scrolledtext.ScrolledText(reports_frame, height=20, width=80, wrap=tk.WORD)
        self.reports_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Log Tab
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="Logs")
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Initialize mode-based UI state
        self.update_mode()
    
    def log(self, message, level="INFO"):
        """Add message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {level}: {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def update_mode(self):
        """Update UI based on selected mode."""
        mode = self.mode_var.get()
        
        if mode == "custom":
            # Enable custom URLs input for custom mode
            self.custom_urls_text.config(state=tk.NORMAL)
            self.custom_urls_frame.config(text="✓ Custom URLs (REQUIRED - one per line)")
        else:
            # Disable custom URLs input for auto-discovery and single-page modes
            if mode == "single":
                self.custom_urls_frame.config(text="✗ Custom URLs DISABLED - Single page mode uses only the URL above")
            else:
                self.custom_urls_frame.config(text="✗ Custom URLs DISABLED - Auto-discover mode does not use sample_urls.txt")
            self.custom_urls_text.config(state=tk.DISABLED)
    
    def load_urls_file(self):
        """Load URLs from a text file."""
        # Only allow loading URLs in custom mode
        if self.mode_var.get() != "custom":
            messagebox.showwarning("Warning", "Switch to 'Custom URL List' mode first to load URLs from file.\n\n"
                                           "Single Page and Auto-discover modes do NOT use custom URLs.")
            return
        
        file_path = filedialog.askopenfilename(
            title="Select URL file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    urls = f.read()
                
                self.custom_urls_text.config(state=tk.NORMAL)
                self.custom_urls_text.delete(1.0, tk.END)
                self.custom_urls_text.insert(tk.END, urls)
                
                # Count URLs
                url_list = [line.strip() for line in urls.split('\n') if line.strip()]
                self.url_count_label.config(text=f"{len(url_list)} URLs loaded")
                
                messagebox.showinfo("Success", f"Loaded {len(url_list)} URLs")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")
    
    def get_custom_urls(self) -> list:
        """Get custom URLs from text widget."""
        urls_text = self.custom_urls_text.get(1.0, tk.END)
        urls = [line.strip() for line in urls_text.split('\n') if line.strip()]
        return urls
    
    def start_scraping(self):
        """Start scraping in a separate thread."""
        url = self.url_entry.get().strip()
        
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
        
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)
        
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.clear_output()
        
        thread = threading.Thread(target=self.scrape_thread, args=(url,), daemon=True)
        thread.start()
    
    def scrape_thread(self, url):
        """Perform scraping in background thread."""
        try:
            mode = self.mode_var.get()
            
            if mode == "custom":
                custom_urls = self.get_custom_urls()
                if not custom_urls:
                    self.status_label.config(text="✗ No URLs provided", foreground="red")
                    self.log("Error: No URLs in custom list", "ERROR")
                    messagebox.showerror("Error", "Please paste or load URLs first")
                    return
                
                self.log(f"Starting custom URL scrape with {len(custom_urls)} pages")
                multi_page = True
                max_pages = 999999
            elif mode == "multi":
                self.log(f"Starting auto-discovery scrape of {url}")
                custom_urls = None
                multi_page = True
                max_pages = 999999
            else:
                self.log(f"Starting single-page scrape of {url}")
                custom_urls = None
                multi_page = False
                max_pages = 1
            
            self.status_label.config(text="Fetching page...", foreground="blue")
            self.progress_var.set(10)
            self.root.update()
            
            self.scraper = WebScraper(url, max_pages=max_pages, custom_urls=custom_urls)
            
            self.status_label.config(text="Extracting content...")
            self.progress_var.set(30)
            self.root.update()
            
            self.results = self.scraper.scrape(multi_page=multi_page)
            
            self.progress_var.set(100)
            self.status_label.config(text="✓ Scraping completed successfully!", foreground="green")
            
            self.display_results()
            self.log("Scraping completed successfully", "SUCCESS")
            self.open_folder_button.config(state=tk.NORMAL)
            
            if mode == "custom":
                pages_done = len(self.results.get('pages', []))
                messagebox.showinfo("Success", f"Scraping completed!\nPages scraped: {pages_done}")
            else:
                messagebox.showinfo("Success", "Scraping completed! Check the Summary tab for results.")
        
        except Exception as e:
            self.status_label.config(text="✗ Error during scraping", foreground="red")
            self.log(f"Error: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Scraping failed: {str(e)}")
        
        finally:
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
    
    def display_results(self):
        """Display scraping results in the Summary tab."""
        if not self.results or not self.results.get('success'):
            self.summary_text.insert(tk.END, "No results available")
            return
        
        mode = self.results.get('mode', 'single-page')
        
        if mode == 'multi-page':
            summary = self._display_multipage_results()
        else:
            summary = self._display_singlepage_results()
        
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, summary)
        
        # Display SEO Analysis
        self.display_seo_analysis()
        
        # Display Export Information
        self.display_export_info()
    
    def _display_singlepage_results(self) -> str:
        """Display single-page scraping results."""
        failed_downloads = self.results.get('failed_downloads', [])
        
        summary = f"""
{'='*70}
SCRAPING RESULTS SUMMARY (Single Page)
{'='*70}

URL: {self.scraper.url}
Scraped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*70}
CONTENT STATISTICS
{'='*70}

Images Downloaded: {len(self.results.get('images', []))}
Videos Found: {len(self.results.get('videos', []))}
Failed Downloads (unrecoverable): {len(failed_downloads)}

Image List:
"""
        for idx, img in enumerate(self.results.get('images', []), 1):
            summary += f"\n  {idx}. {img.get('filepath', 'N/A').split(chr(92))[-1]}"
            summary += f"\n     Alt: {img.get('alt_text', 'N/A')}"
        
        summary += f"\n\nVideo List:\n"
        for idx, vid in enumerate(self.results.get('videos', []), 1):
            summary += f"\n  {idx}. {vid.get('type', 'Unknown')}"
            summary += f"\n     Title: {vid.get('title', 'N/A')}"
            if vid.get('filepath'):
                summary += f"\n     Local: {vid.get('filepath').split(chr(92))[-1]}"
        
        if failed_downloads:
            summary += f"\n\n{'='*70}\nFAILED DOWNLOADS (Could not recover)\n{'='*70}\n"
            for item in failed_downloads[:10]:  # Show first 10
                summary += f"\n• {item['type'].upper()}: {item['url'][:60]}..."
            
            if len(failed_downloads) > 10:
                summary += f"\n\n... and {len(failed_downloads) - 10} more\n"
            
            summary += "\n\nNote: These are typically 404 errors (files not found on server)."
            summary += "\n      The scraper retried these 3 times automatically."
        
        summary += f"\n\nOutput Directory: {self.scraper.output_dir}"
        return summary
    
    def _display_multipage_results(self) -> str:
        """Display multi-page scraping results."""
        pages = self.results.get('pages', [])
        total_images = self.results.get('total_images', [])
        total_videos = self.results.get('total_videos', [])
        failed_downloads = self.results.get('failed_downloads', [])
        
        summary = f"""
{'='*70}
SCRAPING RESULTS SUMMARY (Multi-Page)
{'='*70}

Base URL: {self.scraper.url}
Scraped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*70}
OVERALL STATISTICS
{'='*70}

Total Pages Scraped: {len(pages)}
Total Images Downloaded: {len(total_images)}
Total Videos Found: {len(total_videos)}
Failed Downloads (unrecoverable): {len(failed_downloads)}

{'='*70}
PAGES SCRAPED (with individual folders)
{'='*70}
"""
        for page_data in pages:
            summary += f"\n\nPage {page_data.get('page_number')}:"
            summary += f"\n  URL: {page_data.get('url')}"
            summary += f"\n  Folder: {page_data.get('page_folder', 'N/A')}"
            summary += f"\n  Images: {len(page_data.get('images', []))}"
            summary += f"\n  Videos: {len(page_data.get('videos', []))}"
            seo = page_data.get('seo', {}).get('seo_analysis', {})
            summary += f"\n  H1 Tags: {seo.get('h1_count', 0)}"
            summary += f"\n  Score: {seo.get('content_structure_score', 0)}/100"
        
        if failed_downloads:
            summary += f"\n\n{'='*70}\nFAILED DOWNLOADS (Could not recover)\n{'='*70}\n"
            for item in failed_downloads[:10]:  # Show first 10
                summary += f"\n• {item['type'].upper()}: {item['url'][:60]}..."
            
            if len(failed_downloads) > 10:
                summary += f"\n\n... and {len(failed_downloads) - 10} more\n"
            
            summary += "\n\nNote: These are typically 404 errors (files not found on server)."
            summary += "\n      The scraper retried these 3 times automatically."
        
        summary += f"\n\nOutput Directory: {self.scraper.output_dir}"
        return summary
    
    def display_seo_analysis(self):
        """Display SEO analysis results."""
        if not self.results:
            return
        
        mode = self.results.get('mode', 'single-page')
        seo_data = self.results.get('seo_analysis', {})
        seo_analysis = seo_data.get('seo_analysis', {})
        headers_data = seo_data.get('headers', {})
        
        if mode == 'multi-page':
            seo_text = f"""
{'='*70}
SEO ANALYSIS REPORT (Multi-Page)
{'='*70}

Total Pages Analyzed: {seo_analysis.get('total_pages', 0)}
Total H1 Tags: {seo_analysis.get('total_h1', 0)}
Total H2 Tags: {seo_analysis.get('total_h2', 0)}

{'='*70}
HEADER DISTRIBUTION ACROSS PAGES
{'='*70}
"""
            for level in range(1, 7):
                count = len(headers_data.get(f'h{level}', []))
                seo_text += f"H{level} Tags: {count}\n"
        else:
            seo_text = f"""
{'='*70}
SEO ANALYSIS REPORT (Single Page)
{'='*70}

H1 Status: {seo_analysis.get('h1_status', 'Unknown')}
Content Structure Score: {seo_analysis.get('content_structure_score', 0)}/100

{'='*70}
HEADER COUNTS
{'='*70}
"""
            for level in range(1, 7):
                count = len(headers_data.get(f'h{level}', []))
                seo_text += f"H{level} Tags: {count}\n"
        
        if seo_analysis.get('hierarchy_issues'):
            seo_text += f"\n{'='*70}\nHIERARCHY ISSUES\n{'='*70}\n"
            for issue in seo_analysis['hierarchy_issues']:
                seo_text += f"⚠ {issue}\n"
        
        if seo_analysis.get('recommendations'):
            seo_text += f"\n{'='*70}\nRECOMMENDATIONS\n{'='*70}\n"
            for rec in seo_analysis['recommendations']:
                seo_text += f"✓ {rec}\n"
        
        seo_text += f"\n{'='*70}\nDETAILED HEADERS\n{'='*70}\n"
        
        for level in range(1, 7):
            headers_list = headers_data.get(f'h{level}', [])
            if headers_list:
                seo_text += f"\nH{level} TAGS ({len(headers_list)} found):\n"
                for idx, header in enumerate(headers_list[:10], 1):  # Show first 10
                    text = header.get('text', 'N/A') if isinstance(header, dict) else str(header)
                    seo_text += f"  {idx}. {text[:60]}...\n" if len(str(text)) > 60 else f"  {idx}. {text}\n"
                if len(headers_list) > 10:
                    seo_text += f"  ... and {len(headers_list) - 10} more\n"
        
        self.seo_text.config(state=tk.NORMAL)
        self.seo_text.delete(1.0, tk.END)
        self.seo_text.insert(tk.END, seo_text)
    
    def display_export_info(self):
        """Display export file information."""
        if not self.results or not self.results.get('exports'):
            return
        
        exports = self.results.get('exports', {})
        mode = self.results.get('mode', 'single-page')
        
        export_text = f"""
{'='*70}
EXPORTED REPORTS ({mode.upper()})
{'='*70}

The following files have been generated:

"""
        
        if exports.get('json'):
            export_text += f"✓ JSON Report: {exports['json']}\n"
        if exports.get('csv'):
            export_text += f"✓ CSV Headers: {exports['csv'][0]}\n"
            export_text += f"✓ CSV Assets: {exports['csv'][1]}\n"
        if exports.get('categorized_text_csv'):
            export_text += f"✓ Categorized Text CSV: {exports['categorized_text_csv']}\n"
        if exports.get('html'):
            export_text += f"✓ HTML Report: {exports['html']}\n"
        if exports.get('pdf'):
            export_text += f"✓ PDF Report: {exports['pdf']}\n"
        if exports.get('txt'):
            export_text += f"✓ Text Report: {exports['txt']}\n"
        if exports.get('zip_export'):
            export_text += f"✓ ZIP Export: {exports['zip_export']}\n"
        
        export_text += f"""

{'='*70}
OUTPUT DIRECTORY STRUCTURE
{'='*70}

{self.scraper.output_dir}/
├── text/
│   ├── content.txt (if single-page)
│   └── seo_header_analysis.txt
├── images/
│   └── [downloaded images]
├── videos/
│   ├── video_urls.txt
│   └── [downloaded videos]
├── pages/
│   ├── page_1_home/
│   │   ├── images/      [page-specific images]
│   │   ├── videos/      [page-specific videos]
│   │   ├── content.txt
│   │   └── seo_analysis.txt
│   ├── page_2_about/
│   │   ├── images/
│   │   ├── videos/
│   │   ├── content.txt
│   │   └── seo_analysis.txt
│   └── ...
└── reports/
    ├── report.pdf                      [Professional PDF Report]
    ├── report.json
    ├── report.html
    ├── headers.csv
    ├── assets.csv
    └── categorized_text_content.csv    [Text by H1-H6, paragraphs, etc.]

{'='*70}
SUMMARY
{'='*70}

Mode: {self.results.get('mode', 'unknown').upper()}
"""
        
        if mode == 'multi-page':
            pages = self.results.get('pages', [])
            total_img = len(self.results.get('total_images', []))
            total_vid = len(self.results.get('total_videos', []))
            export_text += f"""
Pages Scraped: {len(pages)}
Total Images: {total_img}
Total Videos: {total_vid}
"""
        else:
            export_text += f"""
Images: {len(self.results.get('images', []))}
Videos: {len(self.results.get('videos', []))}
"""
        
        self.reports_text.config(state=tk.NORMAL)
        self.reports_text.delete(1.0, tk.END)
        self.reports_text.insert(tk.END, export_text)
    
    def stop_scraping(self):
        """Stop scraping (placeholder for future enhancement)."""
        messagebox.showinfo("Info", "Stopping current operation...")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
    
    def clear_output(self):
        """Clear all output fields."""
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        self.seo_text.config(state=tk.NORMAL)
        self.seo_text.delete(1.0, tk.END)
        self.reports_text.config(state=tk.NORMAL)
        self.reports_text.delete(1.0, tk.END)
        self.progress_var.set(0)
        self.status_label.config(text="Ready", foreground="blue")
    
    def open_output_folder(self):
        """Open the output folder in file explorer."""
        if self.scraper:
            output_dir = os.path.abspath(self.scraper.output_dir)
            if os.path.exists(output_dir):
                os.startfile(output_dir)
            else:
                messagebox.showerror("Error", "Output folder not found")
    
    def open_html_report(self):
        """Open HTML report in default browser."""
        if self.results and self.results.get('exports', {}).get('html'):
            html_file = self.results['exports']['html']
            if os.path.exists(html_file):
                webbrowser.open(f"file://{os.path.abspath(html_file)}")
            else:
                messagebox.showerror("Error", "HTML report not found")
        else:
            messagebox.showerror("Error", "No HTML report generated yet. Start scraping first.")
    
    def open_json_report(self):
        """Open JSON report in default text editor."""
        if self.results and self.results.get('exports', {}).get('json'):
            json_file = self.results['exports']['json']
            if os.path.exists(json_file):
                os.startfile(json_file)
            else:
                messagebox.showerror("Error", "JSON report not found")
        else:
            messagebox.showerror("Error", "No JSON report generated yet. Start scraping first.")
    
    def open_csv_headers(self):
        """Open CSV headers in default spreadsheet app."""
        if self.results and self.results.get('exports', {}).get('csv'):
            csv_file = self.results['exports']['csv'][0]
            if os.path.exists(csv_file):
                os.startfile(csv_file)
            else:
                messagebox.showerror("Error", "CSV report not found")
        else:
            messagebox.showerror("Error", "No CSV report generated yet. Start scraping first.")
    
    def open_pdf_report(self):
        """Open PDF report in default PDF viewer."""
        if self.results and self.results.get('exports', {}).get('pdf'):
            pdf_file = self.results['exports']['pdf']
            if os.path.exists(pdf_file):
                os.startfile(pdf_file)
            else:
                messagebox.showerror("Error", "PDF report not found")
        else:
            messagebox.showerror("Error", "No PDF report generated yet. Start scraping first.")
    
    def open_categorized_text_csv(self):
        """Open categorized text CSV in default spreadsheet app."""
        if self.results and self.results.get('exports', {}).get('categorized_text_csv'):
            csv_file = self.results['exports']['categorized_text_csv']
            if os.path.exists(csv_file):
                os.startfile(csv_file)
            else:
                messagebox.showerror("Error", "Categorized text CSV not found")
        else:
            messagebox.showerror("Error", "No categorized text CSV generated yet. Start scraping first.")
    
    def open_zip_export(self):
        """Open folder location of zip export."""
        if self.results and self.results.get('exports', {}).get('zip_export'):
            zip_file = self.results['exports']['zip_export']
            if os.path.exists(zip_file):
                # Open the folder containing the zip file
                folder = os.path.dirname(os.path.abspath(zip_file))
                os.startfile(folder)
            else:
                messagebox.showerror("Error", "Zip export not found")
        else:
            messagebox.showerror("Error", "No zip export generated yet. Start scraping first.")


if __name__ == "__main__":
    root = tk.Tk()
    app = WebScraperGUI(root)
    root.mainloop()
