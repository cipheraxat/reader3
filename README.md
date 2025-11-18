# PDFreader - Modern EPUB Reader
Insipred from Andrej karpathy reader3 repo
![reader3](reader3.png)

A lightweight, self-hosted EPUB reader with a beautiful interface for reading digital books. Upload your EPUB files through a simple drag-and-drop interface and enjoy a clean reading experience.

## ✨ Features

### 📚 Library Management
- **Drag & Drop Upload** - Simply drag EPUB files to upload
- **Web-Based Interface** - No command line needed
- **Delete Books** - Remove books with one click
- **Reading Progress** - Automatically tracks where you left off
- **Bookmarks** - Save your favorite passages

### 📖 Reading Experience
- **Clean UI** - Minimalist design inspired by Kindle and Apple Books
- **Dark Mode & Themes** - Multiple reading themes (sepia, night mode)
- **Chapter Navigation** - Easy next/previous chapter controls
- **Table of Contents** - Quick navigation sidebar
- **Responsive Design** - Works on desktop, tablet, and mobile

### 🔧 Technical Features
- **Fast Processing** - Efficient EPUB parsing and caching
- **Secure** - Path traversal protection, file validation
- **Production Ready** - Logging, health checks, error handling
- **100MB File Support** - Handle large EPUB files

## 🚀 Quick Start

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/cipheraxat/reader3.git
cd reader3
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Start the server**
```bash
python server.py
```

4. **Open your browser**
```
http://localhost:8123
```

### Using UV (Alternative)

If you prefer [uv](https://docs.astral.sh/uv/):

```bash
uv run server.py
```

## 📖 How to Use

### Upload Books
1. Open the web interface at `http://localhost:8123`
2. Drag an EPUB file onto the upload zone, or click to browse
3. Wait for processing (10-30 seconds depending on book size)
4. Your book appears in the library!

### Read Books
- Click on any book card to start reading
- Use **Previous/Next** buttons to navigate chapters
- Use the **Table of Contents** sidebar for quick navigation
- Your reading progress is automatically saved

### Delete Books
- Click the **🗑️ Delete** button on any book card
- Confirm the deletion
- Book is permanently removed

## ⚙️ Configuration

### Environment Variables

```bash
# Books storage directory (default: books)
BOOKS_DIR=books

# Cache size for loaded books (default: 10)
MAX_BOOK_CACHE_SIZE=10

# Server host (default: 0.0.0.0)
HOST=0.0.0.0

# Server port (default: 8123)
PORT=8123

# Number of workers (default: 1)
WORKERS=1
```

### Custom Configuration

Create a `.env` file:
```bash
BOOKS_DIR=/path/to/your/books
PORT=3000
MAX_BOOK_CACHE_SIZE=20
```

## 🌐 Deploy to Cloud

Deploy your own instance for free:

### Render.com (Recommended)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### Railway.app
```bash
railway up
```

### Fly.io
```bash
fly launch
fly deploy
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## 📁 Project Structure

```
reader3/
├── server.py              # FastAPI web server
├── reader3.py             # EPUB processing engine
├── requirements.txt       # Python dependencies
├── templates/
│   ├── library.html      # Library page (book grid)
│   └── reader.html       # Reading interface
└── books/                # Uploaded books storage
    └── *_data/           # Processed book data
        ├── book.pkl      # Book metadata & content
        └── images/       # Extracted images
```

## 🛠️ API Endpoints

### Book Management
- `GET /` - Library page (list all books)
- `POST /upload` - Upload EPUB file
- `DELETE /delete/{book_id}` - Delete a book

### Reading
- `GET /read/{book_id}` - Redirect to first chapter
- `GET /read/{book_id}/{chapter_index}` - Read specific chapter
- `GET /read/{book_id}/images/{image_name}` - Serve book images

### System
- `GET /health` - Health check endpoint

## 🔒 Security Features

- **File validation** - Only EPUB files accepted
- **Size limits** - Maximum 100MB per file
- **Path traversal protection** - Prevents directory access attacks
- **Input sanitization** - Cleans filenames and book IDs
- **Secure file handling** - Temporary files auto-cleanup

## 🎨 Keyboard Shortcuts (Reader)

- `←` or `A` - Previous chapter
- `→` or `D` - Next chapter
- `B` - Toggle bookmarks sidebar
- `T` - Toggle table of contents
- `ESC` - Close sidebars

## 📚 Where to Get EPUB Books

- [Project Gutenberg](https://www.gutenberg.org/) - 70,000+ free public domain books
- [Standard Ebooks](https://standardebooks.org/) - High-quality public domain books
- [Open Library](https://openlibrary.org/) - Millions of books
- [ManyBooks](https://manybooks.net/) - Free ebooks
- Your own purchased EPUB files

## 🐛 Troubleshooting

### Upload not working
- Check file is `.epub` format
- Ensure file size is under 100MB
- Check server logs for errors
- Verify disk space available

### Book not appearing after upload
- Wait for page to auto-refresh (1 second)
- Manually refresh the browser
- Check if `books/` directory has the `*_data` folder
- Look for `book.pkl` file inside the book's data folder

### Server won't start
- Check if port 8123 is already in use
- Install all dependencies: `pip install -r requirements.txt`
- Check Python version (3.8+ required)

## 💻 Development

### Run in development mode
```bash
# Enable auto-reload
RELOAD=true python server.py
```

### Process EPUB via command line
```bash
python reader3.py path/to/book.epub
```

This creates a `book_data/` directory with processed content.

## 🤝 Contributing

This is a personal project, but feel free to fork and modify it for your needs. The code is intentionally simple and easy to understand.

## 📄 License

MIT

## 🙏 Credits

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [EbookLib](https://github.com/aerkalov/ebooklib) - EPUB parsing
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - HTML processing

---

**Note**: Code is ephemeral now and libraries are over - ask your favorite LLM to customize this reader in whatever way you like! 🤖
