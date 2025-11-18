# reader 3

![reader3](reader3.png)

A lightweight, self-hosted EPUB reader that lets you read through EPUB books one chapter at a time. This makes it very easy to copy paste the contents of a chapter to an LLM, to read along. Basically - get epub books (e.g. [Project Gutenberg](https://www.gutenberg.org/) has many), open them up in this reader, copy paste text around to your favorite LLM, and read together and along.

This project was 90% vibe coded just to illustrate how one can very easily [read books together with LLMs](https://x.com/karpathy/status/1990577951671509438). I'm not going to support it in any way, it's provided here as is for other people's inspiration and I don't intend to improve it. Code is ephemeral now and libraries are over, ask your LLM to change it in whatever way you like.

## 🚀 Deploy to Cloud (FREE)

Deploy your own instance in minutes:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

Or choose your platform:
- **[Render.com](https://render.com)** - Recommended, zero config
- **[Railway.app](https://railway.app)** - $5/month free credit
- **[Fly.io](https://fly.io)** - Always-on free tier

📖 **[See Deployment Guide](DEPLOYMENT.md)** for detailed instructions

## Usage

The project uses [uv](https://docs.astral.sh/uv/). So for example, download [Dracula EPUB3](https://www.gutenberg.org/ebooks/345) to this directory as `dracula.epub`, then:

```bash
uv run reader3.py dracula.epub
```

This creates the directory `dracula_data`, which registers the book to your local library. We can then run the server:

```bash
uv run server.py
```

And visit [localhost:8123](http://localhost:8123/) to see your current Library. You can easily add more books, or delete them from your library by deleting the folder. It's not supposed to be complicated or complex.

## ✨ Features

- 📖 **Clean Reading Experience** - Minimalist UI inspired by Kindle and Apple Books
- 🌙 **Dark Mode & Themes** - Multiple reading themes (sepia, night mode)
- 🔖 **Bookmarks & Notes** - Save your favorite passages
- 🔍 **Full-text Search** - Find anything in your books
- 📊 **Reading Statistics** - Track your reading progress and time
- ⌨️ **Keyboard Shortcuts** - Navigate efficiently
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile
- 🔒 **Production Ready** - Security hardened, logging, health checks

## License

MIT