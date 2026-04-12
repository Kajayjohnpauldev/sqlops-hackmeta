FROM python:3.11-slim

LABEL maintainer="K. Ajay John Paul <ajay@kluniversity.in>"
LABEL description="SQLOps OpenEnv — AI SQL Training Environment"

WORKDIR /app

# Install dependencies first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create icons directory
RUN mkdir -p server/static/icons && \
    python -c "
import os
svg_template = '''<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 {s} {s}\">
  <rect width=\"{s}\" height=\"{s}\" rx=\"{r}\" fill=\"#030508\"/>
  <rect x=\"{m}\" y=\"{m}\" width=\"{i}\" height=\"{i}\" rx=\"{ir}\" fill=\"none\" stroke=\"#0D2244\" stroke-width=\"{sw}\"/>
  <ellipse cx=\"{c}\" cy=\"{t}\" rx=\"{ex}\" ry=\"{ey}\" fill=\"none\" stroke=\"#00D4FF\" stroke-width=\"{sw}\"/>
  <line x1=\"{l}\" y1=\"{t}\" x2=\"{l}\" y2=\"{b}\" stroke=\"#00D4FF\" stroke-width=\"{sw}\"/>
  <line x1=\"{rr}\" y1=\"{t}\" x2=\"{rr}\" y2=\"{b}\" stroke=\"#00D4FF\" stroke-width=\"{sw}\"/>
  <ellipse cx=\"{c}\" cy=\"{b}\" rx=\"{ex}\" ry=\"{ey}\" fill=\"none\" stroke=\"#00D4FF\" stroke-width=\"{sw}\"/>
  <text x=\"{c}\" y=\"{tt}\" font-family=\"monospace\" font-weight=\"bold\" font-size=\"{fs}\" fill=\"#00FF9D\" text-anchor=\"middle\">SQL</text>
</svg>'''
for size in [192, 512]:
    s=size; c=s//2; m=s//10; i=s-2*m; r=s//8; ir=s//12
    t=int(s*0.3); b=int(s*0.6); ex=s//4; ey=s//8; sw=max(s//40,2)
    l=c-ex; rr=c+ex; tt=int(s*0.82); fs=s//6
    svg = svg_template.format(s=s,c=c,m=m,i=i,r=r,ir=ir,t=t,b=b,ex=ex,ey=ey,sw=sw,l=l,rr=rr,tt=tt,fs=fs)
    with open(f'server/static/icons/icon-{size}.svg', 'w') as f:
        f.write(svg)
    print(f'Created icon-{size}.svg')
"

# Expose port for HF Spaces
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/health')" || exit 1

# Run the app
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
