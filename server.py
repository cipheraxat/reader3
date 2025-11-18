import os
import pickle
import logging
import mimetypes
from functools import lru_cache
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from reader3 import Book, BookMetadata, ChapterContent, TOCEntry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BOOKS_DIR = os.getenv("BOOKS_DIR", ".")
MAX_BOOK_CACHE_SIZE = int(os.getenv("MAX_BOOK_CACHE_SIZE", "10"))
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

# Initialize FastAPI with metadata
app = FastAPI(
    title="Reader3 - EPUB Reader",
    description="A lightweight, self-hosted EPUB reader",
    version="1.0.0",
    docs_url=None,  # Disable in production
    redoc_url=None,  # Disable in production
)

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=ALLOWED_HOSTS + ["*"]  # Allow all for dev, restrict in prod
)

# Add CORS middleware for API access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Add compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

templates = Jinja2Templates(directory="templates")

def validate_book_id(book_id: str) -> bool:
    """
    Validates that book_id is safe and doesn't contain path traversal attacks.
    """
    # Prevent path traversal
    if ".." in book_id or "/" in book_id or "\\" in book_id:
        return False
    # Must end with _data
    if not book_id.endswith("_data"):
        return False
    # Reasonable length
    if len(book_id) > 255:
        return False
    return True


@lru_cache(maxsize=MAX_BOOK_CACHE_SIZE)
def load_book_cached(folder_name: str) -> Optional[Book]:
    """
    Loads the book from the pickle file.
    Cached so we don't re-read the disk on every click.
    Implements security checks and proper error handling.
    """
    # Security validation
    if not validate_book_id(folder_name):
        logger.warning(f"Invalid book_id attempted: {folder_name}")
        return None
    
    file_path = Path(BOOKS_DIR) / folder_name / "book.pkl"
    
    # Check if path exists and is within BOOKS_DIR (prevent path traversal)
    try:
        resolved_path = file_path.resolve()
        books_dir_resolved = Path(BOOKS_DIR).resolve()
        if not str(resolved_path).startswith(str(books_dir_resolved)):
            logger.error(f"Path traversal attempt detected: {folder_name}")
            return None
    except Exception as e:
        logger.error(f"Path resolution error for {folder_name}: {e}")
        return None
    
    if not file_path.exists():
        logger.info(f"Book not found: {folder_name}")
        return None

    try:
        with open(file_path, "rb") as f:
            book = pickle.load(f)
        logger.info(f"Successfully loaded book: {folder_name}")
        return book
    except pickle.UnpicklingError as e:
        logger.error(f"Corrupted pickle file for {folder_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading book {folder_name}: {e}")
        return None

@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    try:
        # Verify books directory is accessible
        books_accessible = os.path.exists(BOOKS_DIR) and os.access(BOOKS_DIR, os.R_OK)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "healthy",
                "books_dir_accessible": books_accessible,
                "cache_size": load_book_cached.cache_info()._asdict()
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.get("/", response_class=HTMLResponse)
async def library_view(request: Request):
    """
    Lists all available processed books.
    Implements proper error handling and security checks.
    """
    books = []

    try:
        # Verify books directory exists
        if not os.path.exists(BOOKS_DIR):
            logger.error(f"Books directory does not exist: {BOOKS_DIR}")
            return templates.TemplateResponse(
                "library.html", 
                {"request": request, "books": []}
            )
        
        # Scan directory for folders ending in '_data' that have a book.pkl
        for item in os.listdir(BOOKS_DIR):
            if not item.endswith("_data"):
                continue
                
            item_path = os.path.join(BOOKS_DIR, item)
            if not os.path.isdir(item_path):
                continue
            
            # Validate book_id
            if not validate_book_id(item):
                logger.warning(f"Skipping invalid book directory: {item}")
                continue
            
            # Try to load book metadata
            book = load_book_cached(item)
            if book:
                books.append({
                    "id": item,
                    "title": book.metadata.title or "Untitled",
                    "author": ", ".join(book.metadata.authors) if book.metadata.authors else "Unknown",
                    "chapters": len(book.spine)
                })
        
        # Sort books by title
        books.sort(key=lambda x: x["title"].lower())
        logger.info(f"Library view loaded with {len(books)} books")
        
    except Exception as e:
        logger.error(f"Error loading library: {e}")
        # Don't expose internal errors to users
        books = []

    return templates.TemplateResponse("library.html", {"request": request, "books": books})

@app.get("/read/{book_id}", response_class=HTMLResponse)
async def redirect_to_first_chapter(request: Request, book_id: str):
    """
    Redirects to the first chapter of a book.
    Validates book_id before processing.
    """
    # Validate book_id
    if not validate_book_id(book_id):
        logger.warning(f"Invalid book_id in redirect: {book_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid book identifier"
        )
    
    return await read_chapter(request=request, book_id=book_id, chapter_index=0)

@app.get("/read/{book_id}/{chapter_index}", response_class=HTMLResponse)
async def read_chapter(request: Request, book_id: str, chapter_index: int):
    """
    The main reader interface.
    Implements comprehensive validation and error handling.
    """
    # Validate book_id
    if not validate_book_id(book_id):
        logger.warning(f"Invalid book_id in read_chapter: {book_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid book identifier"
        )
    
    # Validate chapter_index is reasonable
    if chapter_index < 0 or chapter_index > 10000:  # Reasonable upper limit
        logger.warning(f"Invalid chapter_index: {chapter_index}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid chapter index"
        )
    
    # Load book
    book = load_book_cached(book_id)
    if not book:
        logger.info(f"Book not found: {book_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )

    # Validate chapter exists
    if chapter_index >= len(book.spine):
        logger.info(f"Chapter {chapter_index} not found in book {book_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )

    try:
        current_chapter = book.spine[chapter_index]

        # Calculate Prev/Next links
        prev_idx = chapter_index - 1 if chapter_index > 0 else None
        next_idx = chapter_index + 1 if chapter_index < len(book.spine) - 1 else None

        return templates.TemplateResponse("reader.html", {
            "request": request,
            "book": book,
            "current_chapter": current_chapter,
            "chapter_index": chapter_index,
            "book_id": book_id,
            "prev_idx": prev_idx,
            "next_idx": next_idx
        })
    except Exception as e:
        logger.error(f"Error rendering chapter {chapter_index} of {book_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error loading chapter"
        )

@app.get("/read/{book_id}/images/{image_name}")
async def serve_image(book_id: str, image_name: str):
    """
    Serves images for a book with comprehensive security checks.
    Prevents path traversal and validates file types.
    """
    # Validate book_id
    if not validate_book_id(book_id):
        logger.warning(f"Invalid book_id in serve_image: {book_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid book identifier"
        )
    
    # Security: Validate image_name
    safe_image_name = os.path.basename(image_name)
    
    # Prevent path traversal
    if ".." in safe_image_name or "/" in safe_image_name or "\\" in safe_image_name:
        logger.warning(f"Path traversal attempt in image name: {image_name}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image name"
        )
    
    # Build and validate path
    img_path = Path(BOOKS_DIR) / book_id / "images" / safe_image_name
    
    try:
        # Resolve path and check it's within allowed directory
        resolved_path = img_path.resolve()
        allowed_dir = (Path(BOOKS_DIR) / book_id / "images").resolve()
        
        if not str(resolved_path).startswith(str(allowed_dir)):
            logger.error(f"Path traversal attempt detected: {image_name}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        if not resolved_path.exists():
            logger.info(f"Image not found: {resolved_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )
        
        # Verify it's a file, not a directory
        if not resolved_path.is_file():
            logger.warning(f"Attempted to serve non-file: {resolved_path}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid resource"
            )
        
        # Validate file type (only serve images)
        mime_type, _ = mimetypes.guess_type(str(resolved_path))
        if not mime_type or not mime_type.startswith('image/'):
            logger.warning(f"Attempted to serve non-image file: {resolved_path}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid file type"
            )
        
        # Serve with proper media type and cache headers
        return FileResponse(
            path=resolved_path,
            media_type=mime_type,
            headers={
                "Cache-Control": "public, max-age=31536000",  # Cache images for 1 year
                "X-Content-Type-Options": "nosniff"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving image {image_name} for {book_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error loading image"
        )

if __name__ == "__main__":
    import uvicorn
    
    # Production configuration with cloud platform support
    host = os.getenv("HOST", "0.0.0.0")  # Changed default for cloud deployment
    port = int(os.getenv("PORT", "8123"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    workers = int(os.getenv("WORKERS", "1"))
    
    logger.info(f"Starting Reader3 server at http://{host}:{port}")
    logger.info(f"Books directory: {BOOKS_DIR}")
    logger.info(f"Cache size: {MAX_BOOK_CACHE_SIZE}")
    logger.info(f"Python version: {os.sys.version}")
    
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        log_level="info",
        access_log=True,
        proxy_headers=True,  # Important for cloud deployments
        forwarded_allow_ips="*"  # Trust proxy headers
    )
