# WebReconstruct 🚀 - Ultimate Website to Static Site & AI Pack

**WebReconstruct** is a powerful, SEO-optimized CLI tool that transforms any dynamic website into a lightweight, fully functional static site AND an AI-ready data package. It captures everything—from metadata and structured JSON data to every CSS, JS, and Image asset—making website archiving, migration, and AI reconstruction easier than ever.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## 🌟 Key Features

- **Full Static Reconstruct**: Generates a complete `website/` folder with local HTML files ready for hosting.
- **AI Data Pack**: Generates a `data/` folder with JSON and Markdown exports, specifically designed for LLMs (ChatGPT, Claude, etc.).
- **Asset Portability**: Automatically downloads all Images, CSS, and JS files.
- **Intelligent Link Rewriting**: Converts online URLs into local `.html` links for seamless offline navigation.
- **Depth Control**: Use `--depth` to control how deep the crawler should go.
- **Fast & Async**: Built with `httpx` and `asyncio` for high-performance crawling.
- **Summary Reports**: Get a quick overview of pages, images, and time taken in `summary.json`.

---

## 📁 Output Structure

WebReconstruct creates a clean, organized output for two distinct use cases:

```text
domain_com_extracted/
├── summary.json        # Quick stats (pages, assets, time)
├── website/            # THE STATIC SITE (Browse or Host)
│   ├── index.html      # Local homepage
│   ├── about.html      # Local internal pages
│   └── assets/         # CSS, JS, and Images
└── data/               # THE AI PACK (For AI Tools)
    ├── data.json       # All data in structured JSON
    └── markdown/       # All pages in clean AI-readable Markdown (.md)
```

---

## 🤖 AI Reconstruction Guide

One of the most powerful features of WebReconstruct is the **AI Pack**. You can use this data to rebuild, improve, or migrate a website using AI:

1.  **Feeding AI**: Upload the `data.json` or specific `.md` files from the `data/markdown/` folder to your favorite LLM (Claude, ChatGPT, or Gemini).
2.  **Prompting**: Use prompts like:
    > "Using the provided JSON data/Markdown, recreate the 'Contact' page in Next.js, keeping the exact same slug (/contact) and headings, but improve the design and make it responsive."
3.  **Perfect Migration**: Because we capture the original slugs, titles, and meta descriptions, the AI can help you migrate a site while keeping its SEO structure perfectly intact.

---

## 🚀 Getting Started

### 1. Installation

```bash
git clone git@github.com:danishfareed/website-extractor.git
cd website-extractor
```

### 2. Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the Extractor

```bash
# Extract the whole site
python extractor.py https://example.com

# Extract with depth control (e.g., only home page and immediate links)
python extractor.py https://example.com --depth 1
```

---

## 🛠 Tech Stack

- **Python**: Core logic.
- **BeautifulSoup4**: HTML parsing and rewriting.
- **Markdown (html2text)**: AI-friendly content conversion.
- **HTTPX**: High-performance async requests.
- **Rich**: Beautiful CLI interface.

---

**Made with ❤️ by [Danish Fareed](https://github.com/danishfareed)**
