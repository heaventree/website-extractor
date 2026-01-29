import asyncio
import httpx
import os
import json
import re
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
import sys
import argparse
import html2text

console = Console()

class WebsiteExtractor:
    def __init__(self, base_url, output_dir=None, max_depth=None):
        self.base_url = base_url.rstrip("/")
        parsed_base = urlparse(base_url)
        self.domain = parsed_base.netloc
        self.output_dir = output_dir or f"{self.domain.replace('.', '_')}_extracted"
        self.max_depth = max_depth
        
        # Directory Structure
        self.website_dir = os.path.join(self.output_dir, "website")
        self.data_dir = os.path.join(self.output_dir, "data") # New home for JSON/MD
        self.markdown_dir = os.path.join(self.data_dir, "markdown")
        self.assets_dir = os.path.join(self.website_dir, "assets")
        self.images_dir = os.path.join(self.assets_dir, "images")
        self.css_dir = os.path.join(self.assets_dir, "css")
        self.js_dir = os.path.join(self.assets_dir, "js")
        
        self.visited_urls = {} # URL -> Depth
        self.url_to_path = {}
        self.data = []
        self.stats = {
            "total_pages": 0,
            "total_images": 0,
            "total_css": 0,
            "total_js": 0,
            "start_time": time.time(),
            "end_time": 0
        }
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # Markdown Converter Setup
        self.md_converter = html2text.HTML2Text()
        self.md_converter.ignore_links = False
        self.md_converter.bypass_tables = False
        self.md_converter.body_width = 0 # No wrapping
        
        self._setup_directories()

    def _setup_directories(self):
        dirs = [
            self.output_dir, self.website_dir, self.data_dir, 
            self.markdown_dir, self.assets_dir, self.images_dir, 
            self.css_dir, self.js_dir
        ]
        for d in dirs:
            if not os.path.exists(d):
                os.makedirs(d)

    def is_internal(self, url):
        parsed = urlparse(url)
        if parsed.netloc == '' or parsed.netloc == self.domain:
            return True
        if self.domain.startswith("www."):
            return parsed.netloc == self.domain[4:]
        if parsed.netloc == f"www.{self.domain}":
            return True
        return False

    def clean_filename(self, filename, default="index"):
        if not filename or filename == "/":
            return default
        clean = re.sub(r'[^\w\-_\.]', '_', filename)
        return clean if clean else default

    async def download_asset(self, client, url, target_dir, stat_key=None):
        try:
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path)
            if not filename:
                return None
            
            filename = self.clean_filename(filename)
            abs_local_path = os.path.join(target_dir, filename)
            
            if os.path.exists(abs_local_path):
                return filename

            resp = await client.get(url, follow_redirects=True, headers=self.headers)
            if resp.status_code == 200:
                with open(abs_local_path, "wb") as f:
                    f.write(resp.content)
                if stat_key:
                    self.stats[stat_key] += 1
                return filename
        except Exception:
            pass
        return None

    def get_local_path_for_url(self, url):
        parsed = urlparse(url)
        path = parsed.path
        if not path or path == "/":
            return "index.html"
        
        if path.endswith("/"):
            path = path[:-1]
            
        clean_name = self.clean_filename(path.lstrip("/"))
        if not clean_name.endswith(".html"):
            clean_name += ".html"
        return clean_name

    async def extract_page(self, client, url, depth):
        if url in self.visited_urls:
            return []
        
        try:
            response = await client.get(url, follow_redirects=True, headers=self.headers)
            if response.status_code != 200:
                return []

            # Sync domain on first request
            if url == self.base_url:
                new_domain = urlparse(str(response.url)).netloc
                if new_domain != self.domain:
                    self.domain = new_domain

            final_url = str(response.url).rstrip("/")
            if final_url in self.visited_urls and final_url != url:
                return []
            
            self.visited_urls[url] = depth
            self.visited_urls[final_url] = depth
            
            local_html_path = self.get_local_path_for_url(final_url)
            self.url_to_path[final_url] = local_html_path

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Metadata
            title = soup.title.string.strip() if soup.title else ""
            meta_desc = ""
            desc_tag = soup.find("meta", attrs={"name": "description"})
            if desc_tag:
                meta_desc = desc_tag.get("content", "").strip()
            
            # Header/Footer
            header = soup.find("header")
            header_html = str(header) if header else ""
            footer = soup.find("footer")
            footer_html = str(footer) if footer else ""

            # Assets
            page_images = []
            for img in soup.find_all("img"):
                src = img.get("src")
                if src:
                    abs_src = urljoin(final_url, src)
                    filename = await self.download_asset(client, abs_src, self.images_dir, "total_images")
                    if filename:
                        rel_path = f"assets/images/{filename}"
                        img["src"] = rel_path
                        page_images.append({"url": abs_src, "local": rel_path})

            for link in soup.find_all("link", rel="stylesheet"):
                href = link.get("href")
                if href:
                    abs_href = urljoin(final_url, href)
                    filename = await self.download_asset(client, abs_href, self.css_dir, "total_css")
                    if filename:
                        link["href"] = f"assets/css/{filename}"

            for script in soup.find_all("script", src=True):
                src = script.get("src")
                if src:
                    abs_src = urljoin(final_url, src)
                    filename = await self.download_asset(client, abs_src, self.js_dir, "total_js")
                    if filename:
                        script["src"] = f"assets/js/{filename}"

            # Links & Depth Control
            links_to_crawl = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                full_url = urljoin(final_url, href).split("#")[0].rstrip("/")
                parsed_href = urlparse(full_url)
                
                if parsed_href.scheme not in ["http", "https", ""]:
                    continue
                
                if self.is_internal(full_url):
                    if self.max_depth is None or depth < self.max_depth:
                        links_to_crawl.append((full_url, depth + 1))
                    a["href"] = self.get_local_path_for_url(full_url)

            # Markdown conversion
            content_tag = soup.find("main") or soup.find("article") or soup.find("body")
            content_html = str(content_tag) if content_tag else ""
            markdown_content = self.md_converter.handle(content_html)

            # Store JSON data
            self.data.append({
                "slug": urlparse(final_url).path or "/",
                "title": title,
                "meta_description": meta_desc,
                "header": header_html,
                "footer": footer_html,
                "content_html": content_html,
                "content_markdown": markdown_content,
                "images": page_images
            })

            # Save Files
            # 1. HTML
            with open(os.path.join(self.website_dir, local_html_path), "w") as f:
                f.write(soup.prettify())
            
            # 2. Markdown
            md_filename = local_html_path.replace(".html", ".md")
            with open(os.path.join(self.markdown_dir, md_filename), "w") as f:
                header_info = f"# {title}\n**URL:** {final_url}\n**Meta:** {meta_desc}\n\n---\n\n"
                f.write(header_info + markdown_content)

            self.stats["total_pages"] += 1
            return links_to_crawl

        except Exception as e:
            console.print(f"[red]Error extracting {url}: {e}[/red]")
            return []

    async def run(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            queue = [(self.base_url, 0)]
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                crawl_task = progress.add_task("Deconstructing Website...", total=None)
                
                while queue:
                    current_url, depth = queue.pop(0)
                    new_links = await self.extract_page(client, current_url, depth)
                    for link, next_depth in new_links:
                        if link not in self.visited_urls and not any(l[0] == link for l in queue):
                            queue.append((link, next_depth))
                    
                    progress.update(crawl_task, advance=1, description=f"Extracted: {current_url}")
                    progress.update(crawl_task, total=len(self.visited_urls) + len(queue))

        self.stats["end_time"] = time.time()
        duration = round(self.stats["end_time"] - self.stats["start_time"], 2)

        # Save Final Reports
        with open(os.path.join(self.data_dir, "data.json"), "w") as f:
            json.dump(self.data, f, indent=2)
        
        summary = {
            "domain": self.domain,
            "duration_seconds": duration,
            "pages_extracted": self.stats["total_pages"],
            "images_downloaded": self.stats["total_images"],
            "css_files": self.stats["total_css"],
            "js_files": self.stats["total_js"]
        }
        with open(os.path.join(self.output_dir, "summary.json"), "w") as f:
            json.dump(summary, f, indent=2)
        
        console.print(f"\n[bold green]Success! WebReconstruct Finished.[/bold green]")
        console.print(f"⏱️ Time taken: [yellow]{duration}s[/yellow]")
        console.print(f"🏠 Static Site: [cyan]{self.output_dir}/website/index.html[/cyan]")
        console.print(f"🤖 AI Data Pack: [cyan]{self.output_dir}/data/[/cyan] (JSON + Markdown)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WebReconstruct - Website to Static & AI Pack")
    parser.add_argument("url", help="The URL to extract")
    parser.add_argument("--depth", type=int, default=None, help="Max depth to crawl (default: unlimited)")
    args = parser.parse_args()
    
    url = args.url
    if not url.startswith("http"):
        url = "https://" + url
        
    extractor = WebsiteExtractor(url, max_depth=args.depth)
    asyncio.run(extractor.run())
