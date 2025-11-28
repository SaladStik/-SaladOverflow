import re
import html
import bleach
from markdown import markdown
from bs4 import BeautifulSoup
from typing import List, Tuple
from app.schemas.posts import ContentAnalysis
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound
import logging

logger = logging.getLogger(__name__)

# Allowed HTML tags and attributes for content
ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "b",
    "em",
    "i",
    "u",
    "strike",
    "del",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ul",
    "ol",
    "li",
    "blockquote",
    "pre",
    "code",
    "a",
    "img",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "hr",
    "div",
    "span",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target"],
    "img": ["src", "alt", "title", "width", "height"],
    "pre": ["class"],
    "code": ["class"],
    "div": ["class"],
    "span": ["class"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def sanitize_html(content: str) -> str:
    """
    Sanitize HTML content to prevent XSS attacks
    """
    try:
        # Use bleach to sanitize HTML
        cleaned = bleach.clean(
            content,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            protocols=ALLOWED_PROTOCOLS,
            strip=True,
        )

        return cleaned
    except Exception as e:
        logger.error(f"Error sanitizing HTML: {e}")
        # Fallback to basic HTML escaping
        return html.escape(content)


def markdown_to_html(content: str) -> str:
    """
    Convert Markdown to safe HTML
    """
    try:
        # Convert markdown to HTML
        html_content = markdown(
            content, extensions=["codehilite", "fenced_code", "tables", "toc", "nl2br"]
        )

        # Sanitize the resulting HTML
        return sanitize_html(html_content)
    except Exception as e:
        logger.error(f"Error converting markdown: {e}")
        return sanitize_html(content)


def extract_plain_text(html_content: str) -> str:
    """
    Extract plain text from HTML for search indexing
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        return soup.get_text(separator=" ", strip=True)
    except Exception as e:
        logger.error(f"Error extracting plain text: {e}")
        return ""


def analyze_content(content: str) -> ContentAnalysis:
    """
    Analyze content for code blocks, images, etc.
    """
    try:
        soup = BeautifulSoup(content, "html.parser")

        # Find code blocks
        code_blocks = []
        for code_elem in soup.find_all(["code", "pre"]):
            if code_elem.get_text(strip=True):
                code_blocks.append(code_elem.get_text())

        # Find images
        image_urls = []
        for img_elem in soup.find_all("img"):
            src = img_elem.get("src")
            if src:
                image_urls.append(src)

        # Extract plain text
        plain_text = soup.get_text(separator=" ", strip=True)

        # Count words
        word_count = len(plain_text.split()) if plain_text else 0

        return ContentAnalysis(
            has_code=len(code_blocks) > 0,
            has_images=len(image_urls) > 0,
            code_blocks=code_blocks,
            image_urls=image_urls,
            plain_text=plain_text,
            word_count=word_count,
        )

    except Exception as e:
        logger.error(f"Error analyzing content: {e}")
        return ContentAnalysis(plain_text=extract_plain_text(content) or content)


def create_slug(title: str, post_id: int) -> str:
    """
    Create URL-friendly slug from title
    """
    try:
        # Remove HTML tags if any
        soup = BeautifulSoup(title, "html.parser")
        clean_title = soup.get_text()

        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = re.sub(r"[^a-zA-Z0-9\s-]", "", clean_title.lower())
        slug = re.sub(r"\s+", "-", slug.strip())
        slug = re.sub(r"-+", "-", slug)
        slug = slug.strip("-")

        # Limit length and add ID for uniqueness
        if len(slug) > 50:
            slug = slug[:50].rstrip("-")

        return f"{slug}-{post_id}" if slug else f"post-{post_id}"

    except Exception as e:
        logger.error(f"Error creating slug: {e}")
        return f"post-{post_id}"


def highlight_code_blocks(content: str) -> str:
    """
    Add syntax highlighting to code blocks using Pygments
    """
    try:
        soup = BeautifulSoup(content, "html.parser")

        # Handle code blocks (usually in <pre><code> structure)
        for pre_elem in soup.find_all("pre"):
            code_elem = pre_elem.find("code")
            if code_elem:
                code_text = code_elem.get_text()

                # Try to determine language from class attribute
                language = None
                if code_elem.get("class"):
                    for class_name in code_elem.get("class"):
                        if class_name.startswith("language-"):
                            language = class_name.replace("language-", "")
                            break

                try:
                    # Get lexer for syntax highlighting
                    if language:
                        lexer = get_lexer_by_name(language)
                    else:
                        # Try to guess the language
                        lexer = guess_lexer(code_text)

                    # Create HTML formatter
                    formatter = HtmlFormatter(
                        style="default",
                        cssclass="highlight",
                        linenos=False,
                        noclasses=False,
                    )

                    # Highlight the code
                    highlighted = highlight(code_text, lexer, formatter)

                    # Replace the pre element with highlighted version
                    highlighted_soup = BeautifulSoup(highlighted, "html.parser")
                    pre_elem.replace_with(highlighted_soup)

                except ClassNotFound:
                    # If can't determine language, just add generic styling
                    if not code_elem.get("class"):
                        code_elem["class"] = ["language-text"]
                except Exception as e:
                    logger.warning(f"Error highlighting code block: {e}")
                    # Keep original code block if highlighting fails
                    continue

        # Handle inline code (just <code> elements not in <pre>)
        for code_elem in soup.find_all("code"):
            if not code_elem.parent or code_elem.parent.name != "pre":
                if not code_elem.get("class"):
                    code_elem["class"] = ["inline-code"]

        return str(soup)

    except Exception as e:
        logger.error(f"Error in highlight_code_blocks: {e}")
        return content  # Return original content if highlighting fails

        return str(soup)

    except Exception as e:
        logger.error(f"Error highlighting code: {e}")
        return content


def process_post_content(
    content: str, content_type: str = "markdown"
) -> Tuple[str, ContentAnalysis]:
    """
    Process post content from markdown/HTML to safe HTML with analysis
    """
    try:
        # Convert markdown to HTML if needed
        if content_type.lower() == "markdown":
            html_content = markdown_to_html(content)
        else:
            html_content = sanitize_html(content)

        # Highlight code blocks
        html_content = highlight_code_blocks(html_content)

        # Analyze content
        analysis = analyze_content(html_content)

        return html_content, analysis

    except Exception as e:
        logger.error(f"Error processing content: {e}")
        # Fallback to basic sanitization
        safe_content = sanitize_html(content)
        basic_analysis = ContentAnalysis(plain_text=extract_plain_text(safe_content))
        return safe_content, basic_analysis


def validate_image_url(url: str) -> bool:
    """
    Validate image URL for security
    """
    try:
        # Basic URL validation
        if not url.startswith(("http://", "https://")):
            return False

        # Check for valid image extensions
        valid_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]
        if not any(url.lower().endswith(ext) for ext in valid_extensions):
            return False

        # Additional security checks can be added here
        return True

    except Exception:
        return False


def extract_mentions(content: str) -> List[str]:
    """
    Extract @mentions from content
    """
    try:
        # Find @username mentions
        mentions = re.findall(r"@([a-zA-Z0-9_]+)", content)
        return list(set(mentions))  # Remove duplicates
    except Exception as e:
        logger.error(f"Error extracting mentions: {e}")
        return []


def extract_code_language(code_block: str) -> str:
    """
    Try to detect programming language from code content
    """
    try:
        # Simple language detection based on keywords
        code_lower = code_block.lower()

        if any(
            keyword in code_lower
            for keyword in ["def ", "import ", "class ", "print(", "if __name__"]
        ):
            return "python"
        elif any(
            keyword in code_lower
            for keyword in ["function ", "const ", "let ", "var ", "=>"]
        ):
            return "javascript"
        elif any(
            keyword in code_lower
            for keyword in ["select ", "insert ", "update ", "delete ", "create table"]
        ):
            return "sql"
        elif any(
            keyword in code_lower
            for keyword in ["public class", "private ", "public static void"]
        ):
            return "java"
        elif any(
            keyword in code_lower for keyword in ["#include", "int main", "printf"]
        ):
            return "c"
        elif any(keyword in code_lower for keyword in ["<html", "<div", "<script"]):
            return "html"
        elif any(
            keyword in code_lower for keyword in ["{", "}", "margin:", "padding:"]
        ):
            return "css"
        else:
            return "text"

    except Exception:
        return "text"
