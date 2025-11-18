# Production Deployment Guide

## Production Checklist

### 1. Environment Configuration
- Copy `.env.example` to `.env` and configure:
  ```bash
  cp .env.example .env
  ```
- Update `ALLOWED_HOSTS` to match your domain
- Set appropriate `WORKERS` based on CPU cores
- Configure `BOOKS_DIR` to a dedicated directory

### 2. Security Hardening
- Enable HTTPS with reverse proxy (nginx/caddy)
- Set strong file permissions:
  ```bash
  chmod 600 .env
  chmod 755 books_directory
  ```
- Consider adding authentication middleware
- Review CORS settings in `server.py`

### 3. Performance Optimization
- Increase `MAX_BOOK_CACHE_SIZE` based on available RAM
- Use production WSGI server (gunicorn/uvicorn workers)
- Enable CDN for static assets
- Consider Redis for caching

### 4. Monitoring
- Health check endpoint: `/health`
- Monitor logs for errors
- Set up alerting for 5xx errors
- Track cache hit rates

### 5. Backup Strategy
- Regular backups of books directory
- Version control for configuration
- Database backups if extended

## Production Deployment

### Using systemd (Linux)

Create `/etc/systemd/system/reader3.service`:

```ini
[Unit]
Description=Reader3 EPUB Reader
After=network.target

[Service]
Type=simple
User=reader3
Group=reader3
WorkingDirectory=/opt/reader3
Environment="PATH=/opt/reader3/.venv/bin"
EnvironmentFile=/opt/reader3/.env
ExecStart=/opt/reader3/.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8123 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable reader3
sudo systemctl start reader3
```

### Using Docker

Build and run:
```bash
docker build -t reader3 .
docker run -d -p 8123:8123 -v /path/to/books:/app/books reader3
```

### Behind Nginx

```nginx
server {
    listen 80;
    server_name reader.example.com;
    
    location / {
        proxy_pass http://127.0.0.1:8123;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Scaling

For high traffic:
- Use multiple workers: `WORKERS=4`
- Load balance with nginx
- Cache aggressively
- Consider async workers

## Troubleshooting

- Check logs: `journalctl -u reader3 -f`
- Verify permissions on books directory
- Test health endpoint: `curl http://localhost:8123/health`
- Clear cache if stale: restart service
