"""
Parses an EPUB file into a structured object that can be used to serve the book via a web interface.
Production-ready with comprehensive error handling, validation, and logging.
"""

import os
import pickle
import shutil
import logging
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from urllib.parse import unquote
from pathlib import Path

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup, Comment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Data structures ---

@dataclass
class ChapterContent:
    """
    Represents a physical file in the EPUB (Spine Item).
    A single file might contain multiple logical chapters (TOC entries).
    """
    id: str           # Internal ID (e.g., 'item_1')
    href: str         # Filename (e.g., 'part01.html')
    title: str        # Best guess title from file
    content: str      # Cleaned HTML with rewritten image paths
    text: str         # Plain text for search/LLM context
    order: int        # Linear reading order


@dataclass
class TOCEntry:
    """Represents a logical entry in the navigation sidebar."""
    title: str
    href: str         # original href (e.g., 'part01.html#chapter1')
    file_href: str    # just the filename (e.g., 'part01.html')
    anchor: str       # just the anchor (e.g., 'chapter1'), empty if none
    children: List['TOCEntry'] = field(default_factory=list)


@dataclass
class BookMetadata:
    """Metadata"""
    title: str
    language: str
    authors: List[str] = field(default_factory=list)
    description: Optional[str] = None
    publisher: Optional[str] = None
    date: Optional[str] = None
    identifiers: List[str] = field(default_factory=list)
    subjects: List[str] = field(default_factory=list)


@dataclass
class Book:
    """The Master Object to be pickled."""
    metadata: BookMetadata
    spine: List[ChapterContent]  # The actual content (linear files)
    toc: List[TOCEntry]          # The navigation tree
    images: Dict[str, str]       # Map: original_path -> local_path

    # Meta info
    source_file: str
    processed_at: str
    version: str = "3.0"


# --- Utilities ---

def clean_html_content(soup: BeautifulSoup) -> BeautifulSoup:
    """
    Cleans HTML content by removing dangerous/useless tags.
    Implements comprehensive error handling.
    """
    try:
        # Remove dangerous/useless tags
        dangerous_tags = ['script', 'style', 'iframe', 'video', 'nav', 'form', 'button', 'input']
        for tag_name in dangerous_tags:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        # Remove HTML comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        return soup
    except Exception as e:
        logger.error(f"Error cleaning HTML content: {e}")
        # Return original soup if cleaning fails
        return soup


def extract_plain_text(soup: BeautifulSoup) -> str:
    """
    Extract clean text for LLM/Search usage.
    Implements error handling for malformed HTML.
    """
    try:
        text = soup.get_text(separator=' ')
        # Collapse whitespace
        return ' '.join(text.split())
    except Exception as e:
        logger.error(f"Error extracting plain text: {e}")
        return ""


def parse_toc_recursive(toc_list, depth=0) -> List[TOCEntry]:
    """
    Recursively parses the TOC structure from ebooklib.
    Implements error handling for malformed TOC entries.
    """
    result = []
    
    if depth > 10:  # Prevent infinite recursion
        logger.warning("TOC nesting too deep, stopping recursion")
        return result

    for item in toc_list:
        try:
            # ebooklib TOC items are either `Link` objects or tuples (Section, [Children])
            if isinstance(item, tuple):
                section, children = item
                if not hasattr(section, 'title') or not hasattr(section, 'href'):
                    logger.warning(f"Malformed TOC section: {section}")
                    continue
                    
                entry = TOCEntry(
                    title=section.title or "Untitled",
                    href=section.href or "",
                    file_href=section.href.split('#')[0] if section.href else "",
                    anchor=section.href.split('#')[1] if section.href and '#' in section.href else "",
                    children=parse_toc_recursive(children, depth + 1)
                )
                result.append(entry)
            elif isinstance(item, epub.Link):
                if not hasattr(item, 'title') or not hasattr(item, 'href'):
                    logger.warning(f"Malformed TOC link: {item}")
                    continue
                    
                entry = TOCEntry(
                    title=item.title or "Untitled",
                    href=item.href or "",
                    file_href=item.href.split('#')[0] if item.href else "",
                    anchor=item.href.split('#')[1] if item.href and '#' in item.href else ""
                )
                result.append(entry)
            # Note: ebooklib sometimes returns direct Section objects without children
            elif isinstance(item, epub.Section):
                if not hasattr(item, 'title') or not hasattr(item, 'href'):
                    logger.warning(f"Malformed TOC section: {item}")
                    continue
                    
                entry = TOCEntry(
                    title=item.title or "Untitled",
                    href=item.href or "",
                    file_href=item.href.split('#')[0] if item.href else "",
                    anchor=item.href.split('#')[1] if item.href and '#' in item.href else ""
                )
                result.append(entry)
        except Exception as e:
            logger.error(f"Error parsing TOC item: {e}")
            continue

    return result


def get_fallback_toc(book_obj) -> List[TOCEntry]:
    """
    If TOC is missing, build a flat one from the Spine.
    """
    toc = []
    for item in book_obj.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            name = item.get_name()
            # Try to guess a title from the content or ID
            title = item.get_name().replace('.html', '').replace('.xhtml', '').replace('_', ' ').title()
            toc.append(TOCEntry(title=title, href=name, file_href=name, anchor=""))
    return toc


def extract_metadata_robust(book_obj) -> BookMetadata:
    """
    Extracts metadata handling both single and list values.
    """
    def get_list(key):
        data = book_obj.get_metadata('DC', key)
        return [x[0] for x in data] if data else []

    def get_one(key):
        data = book_obj.get_metadata('DC', key)
        return data[0][0] if data else None

    return BookMetadata(
        title=get_one('title') or "Untitled",
        language=get_one('language') or "en",
        authors=get_list('creator'),
        description=get_one('description'),
        publisher=get_one('publisher'),
        date=get_one('date'),
        identifiers=get_list('identifier'),
        subjects=get_list('subject')
    )


# --- Main Conversion Logic ---

def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """
    Sanitizes a filename to be safe for filesystem.
    """
    # Remove or replace dangerous characters
    safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    sanitized = "".join(c if c in safe_chars else '_' for c in filename)
    
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    
    # Ensure not empty
    if not sanitized:
        sanitized = "unnamed"
    
    # Limit length
    if len(sanitized) > max_length:
        # Keep extension if present
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:max_length - len(ext)] + ext
    
    return sanitized


def process_epub(epub_path: str, output_dir: str) -> Book:

    # 1. Validate input
    epub_path_obj = Path(epub_path)
    if not epub_path_obj.exists():
        raise FileNotFoundError(f"EPUB file not found: {epub_path}")
    
    if not epub_path_obj.is_file():
        raise ValueError(f"Path is not a file: {epub_path}")
    
    if epub_path_obj.stat().st_size == 0:
        raise ValueError(f"EPUB file is empty: {epub_path}")
    
    if epub_path_obj.stat().st_size > 500 * 1024 * 1024:  # 500MB limit
        logger.warning(f"Large EPUB file: {epub_path_obj.stat().st_size / 1024 / 1024:.2f}MB")

    # 2. Load Book
    logger.info(f"Loading {epub_path}...")
    try:
        book = epub.read_epub(epub_path)
    except Exception as e:
        logger.error(f"Failed to read EPUB: {e}")
        raise ValueError(f"Invalid or corrupted EPUB file: {e}")

    # 3. Extract Metadata
    try:
        metadata = extract_metadata_robust(book)
        logger.info(f"Extracted metadata: {metadata.title}")
    except Exception as e:
        logger.error(f"Error extracting metadata: {e}")
        # Use fallback metadata
        metadata = BookMetadata(
            title=os.path.splitext(os.path.basename(epub_path))[0],
            language="en",
            authors=["Unknown"]
        )

    # 4. Prepare Output Directories
    try:
        if os.path.exists(output_dir):
            logger.info(f"Removing existing directory: {output_dir}")
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        images_dir = os.path.join(output_dir, 'images')
        os.makedirs(images_dir, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create output directory: {e}")
        raise

    # 5. Extract Images & Build Map
    logger.info("Extracting images...")
    image_map = {}  # Key: internal_path, Value: local_relative_path
    image_count = 0

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_IMAGE:
            try:
                # Normalize filename
                original_fname = os.path.basename(item.get_name())
                
                # Sanitize filename for OS
                safe_fname = sanitize_filename(original_fname)
                
                # Avoid duplicates by adding hash if needed
                local_path = os.path.join(images_dir, safe_fname)
                if os.path.exists(local_path):
                    # Add hash to make unique
                    name, ext = os.path.splitext(safe_fname)
                    content_hash = hashlib.md5(item.get_content()).hexdigest()[:8]
                    safe_fname = f"{name}_{content_hash}{ext}"
                    local_path = os.path.join(images_dir, safe_fname)

                # Save to disk
                with open(local_path, 'wb') as f:
                    f.write(item.get_content())

                # Map keys: We try both the full internal path and just the basename
                rel_path = f"images/{safe_fname}"
                image_map[item.get_name()] = rel_path
                image_map[original_fname] = rel_path
                image_count += 1
                
            except Exception as e:
                logger.error(f"Error extracting image {item.get_name()}: {e}")
                continue
    
    logger.info(f"Extracted {image_count} images")

    # 6. Process TOC
    logger.info("Parsing Table of Contents...")
    try:
        toc_structure = parse_toc_recursive(book.toc)
        if not toc_structure:
            logger.warning("Empty TOC, building fallback from Spine...")
            toc_structure = get_fallback_toc(book)
    except Exception as e:
        logger.error(f"Error parsing TOC: {e}")
        logger.info("Building fallback TOC from Spine...")
        toc_structure = get_fallback_toc(book)

    # 7. Process Content (Spine-based to preserve HTML validity)
    logger.info("Processing chapters...")
    spine_chapters = []
    processed_count = 0
    error_count = 0

    # We iterate over the spine (linear reading order)
    for i, spine_item in enumerate(book.spine):
        item_id, linear = spine_item
        item = book.get_item_with_id(item_id)

        if not item:
            logger.warning(f"Spine item not found: {item_id}")
            continue

        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            try:
                # Raw content
                raw_content = item.get_content().decode('utf-8', errors='ignore')
                soup = BeautifulSoup(raw_content, 'html.parser')

                # A. Fix Images
                for img in soup.find_all('img'):
                    try:
                        src = img.get('src', '')
                        if not src:
                            continue

                        # Decode URL (part01/image%201.jpg -> part01/image 1.jpg)
                        src_decoded = unquote(src)
                        filename = os.path.basename(src_decoded)

                        # Try to find in map
                        if src_decoded in image_map:
                            img['src'] = image_map[src_decoded]
                        elif filename in image_map:
                            img['src'] = image_map[filename]
                    except Exception as e:
                        logger.error(f"Error fixing image in chapter {i}: {e}")
                        continue

                # B. Clean HTML
                soup = clean_html_content(soup)

                # C. Extract Body Content only
                body = soup.find('body')
                if body:
                    # Extract inner HTML of body
                    final_html = "".join([str(x) for x in body.contents])
                else:
                    final_html = str(soup)

                # D. Create Object
                chapter = ChapterContent(
                    id=item_id,
                    href=item.get_name(),  # Important: This links TOC to Content
                    title=f"Section {i+1}",  # Fallback, real titles come from TOC
                    content=final_html,
                    text=extract_plain_text(soup),
                    order=i
                )
                spine_chapters.append(chapter)
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing chapter {i} ({item_id}): {e}")
                error_count += 1
                continue
    
    logger.info(f"Processed {processed_count} chapters, {error_count} errors")
    
    if not spine_chapters:
        raise ValueError("No chapters could be processed from EPUB")

    # 7. Final Assembly
    final_book = Book(
        metadata=metadata,
        spine=spine_chapters,
        toc=toc_structure,
        images=image_map,
        source_file=os.path.basename(epub_path),
        processed_at=datetime.now().isoformat()
    )

    return final_book


def save_to_pickle(book: Book, output_dir: str):
    """
    Saves book object to pickle file with error handling.
    """
    try:
        p_path = os.path.join(output_dir, 'book.pkl')
        # Use highest protocol for better performance
        with open(p_path, 'wb') as f:
            pickle.dump(book, f, protocol=pickle.HIGHEST_PROTOCOL)
        logger.info(f"Saved structured data to {p_path}")
    except Exception as e:
        logger.error(f"Failed to save pickle file: {e}")
        raise


# --- CLI ---

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python reader3.py <file.epub>")
        print("\nProcesses an EPUB file and extracts content for the reader.")
        sys.exit(1)

    epub_file = sys.argv[1]
    
    # Validate input
    if not os.path.exists(epub_file):
        logger.error(f"File not found: {epub_file}")
        sys.exit(1)
    
    if not epub_file.lower().endswith('.epub'):
        logger.warning(f"File does not have .epub extension: {epub_file}")
    
    # Generate output directory name
    out_dir = os.path.splitext(epub_file)[0] + "_data"
    
    # Validate output directory
    if os.path.exists(out_dir):
        logger.info(f"Output directory exists and will be overwritten: {out_dir}")

    try:
        # Process EPUB
        book_obj = process_epub(epub_file, out_dir)
        
        # Save to pickle
        save_to_pickle(book_obj, out_dir)
        
        # Print summary
        print("\n" + "="*50)
        print("✓ Processing Complete")
        print("="*50)
        print(f"Title: {book_obj.metadata.title}")
        print(f"Authors: {', '.join(book_obj.metadata.authors) if book_obj.metadata.authors else 'Unknown'}")
        print(f"Language: {book_obj.metadata.language}")
        print(f"Physical Files (Spine): {len(book_obj.spine)}")
        print(f"TOC Root Items: {len(book_obj.toc)}")
        print(f"Images extracted: {len(book_obj.images)}")
        print(f"\nOutput directory: {out_dir}")
        print("="*50)
        
    except Exception as e:
        logger.error(f"Failed to process EPUB: {e}")
        print(f"\n✗ Error: {e}")
        sys.exit(1)
