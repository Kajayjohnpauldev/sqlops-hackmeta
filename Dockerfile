FROM python:3.11-slim

LABEL maintainer="K. Ajay John Paul <ajay@kluniversity.in>"
LABEL description="SQLOps OpenEnv — AI SQL Training Environment"

WORKDIR /app

# Install dependencies first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Generate SVG icons at build time
RUN mkdir -p server/static/icons && \
    python -c "s=192;c=s//2;m=s//10;svg=f'<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 {s} {s}\"><rect width=\"{s}\" height=\"{s}\" rx=\"{s//8}\" fill=\"#0A0A0A\"/><text x=\"{c}\" y=\"{int(s*0.6)}\" font-family=\"monospace\" font-weight=\"bold\" font-size=\"{s//4}\" fill=\"#fff\" text-anchor=\"middle\">SQL</text></svg>';open('server/static/icons/icon-192.svg','w').write(svg)" && \
    python -c "s=512;c=s//2;m=s//10;svg=f'<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 {s} {s}\"><rect width=\"{s}\" height=\"{s}\" rx=\"{s//8}\" fill=\"#0A0A0A\"/><text x=\"{c}\" y=\"{int(s*0.6)}\" font-family=\"monospace\" font-weight=\"bold\" font-size=\"{s//4}\" fill=\"#fff\" text-anchor=\"middle\">SQL</text></svg>';open('server/static/icons/icon-512.svg','w').write(svg)"

# Expose port for HF Spaces
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/health')" || exit 1

# Run the app
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
