import os
import requests
import tempfile
from bs4 import BeautifulSoup

def fetch_html(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        res = requests.get(url, timeout=15, headers=headers)
        res.raise_for_status()
        return res.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_html(html):
    try:
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)
    except Exception as e:
        print(f"Error parsing HTML: {e}")
        return None

def parse_pdf(url):
    try:
        from langchain_community.document_loaders import PyPDFLoader

        response = requests.get(url, timeout=15)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name

        loader = PyPDFLoader(tmp_path)
        docs = loader.load()

        os.unlink(tmp_path)  # FIX: os was missing in original

        return "\n".join([d.page_content for d in docs])
    except Exception as e:
        print(f"Error parsing PDF {url}: {e}")
        return None