/**
 * SQLOps Oracle — 4D Animation Engine
 * Designed by K. Ajay John Paul | KL University Hyderabad
 *
 * 1. Particle constellation field
 * 2. 3D Score landscape (isometric wireframe)
 * 3. Typewriter terminal
 * 4. Counter animations
 * 5. Scroll-triggered reveals
 * 6. SVG arc progress
 */

class SQLOpsEngine {
  constructor() {
    this.canvases = new Map();
    this.animFrames = new Map();
    this.isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  /* ═══ 1. PARTICLE FIELD ═══ */
  initParticleField(canvasId, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const count = options.count || 80;
    const maxDist = options.maxDist || 120;
    const speed = options.speed || 0.3;
    const isDark = options.dark || false;

    const resize = () => {
      canvas.width = canvas.offsetWidth * (window.devicePixelRatio || 1);
      canvas.height = canvas.offsetHeight * (window.devicePixelRatio || 1);
      ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);
    };
    resize();
    window.addEventListener('resize', resize);

    const particles = Array.from({ length: count }, () => ({
      x: Math.random() * canvas.offsetWidth,
      y: Math.random() * canvas.offsetHeight,
      vx: (Math.random() - 0.5) * speed,
      vy: (Math.random() - 0.5) * speed,
      size: Math.random() * 1.5 + 0.5,
      opacity: Math.random() * 0.4 + 0.1,
    }));

    const cw = () => canvas.offsetWidth;
    const ch = () => canvas.offsetHeight;

    const animate = () => {
      ctx.clearRect(0, 0, cw(), ch());
      const baseColor = isDark ? '255,255,255' : '10,10,10';

      particles.forEach(p => {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > cw()) p.vx *= -1;
        if (p.y < 0 || p.y > ch()) p.vy *= -1;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${baseColor},${p.opacity})`;
        ctx.fill();
      });

      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < maxDist) {
            const alpha = (1 - dist / maxDist) * 0.12;
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(${baseColor},${alpha})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }
      this.animFrames.set(canvasId, requestAnimationFrame(animate));
    };

    if (!this.isReducedMotion) animate();
    this.canvases.set(canvasId, { canvas, ctx, particles });
  }

  /* ═══ 2. 3D SCORE LANDSCAPE ═══ */
  initScoreLandscape(canvasId, rewardHistory) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const resize = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    };
    resize();

    const W = () => canvas.width;
    const H = () => canvas.height;
    const COLS = 12, ROWS = 8;

    const heightMap = [];
    for (let r = 0; r < ROWS; r++) {
      heightMap[r] = [];
      for (let c = 0; c < COLS; c++) {
        const idx = r * COLS + c;
        heightMap[r][c] = idx < rewardHistory.length
          ? rewardHistory[idx]
          : Math.sin(r * 0.5) * Math.cos(c * 0.5) * 0.3 + 0.15;
      }
    }

    let time = 0;
    const toIso = (x, y, z) => {
      const angle = Math.PI / 6;
      return {
        px: W() * 0.5 + (x - y) * Math.cos(angle) * (W() / COLS * 0.5),
        py: H() * 0.65 + ((x + y) * Math.sin(angle) - z * 50) * (H() / ROWS * 0.35)
      };
    };

    const animate = () => {
      ctx.clearRect(0, 0, W(), H());
      time += 0.003;

      for (let r = 0; r < ROWS - 1; r++) {
        for (let c = 0; c < COLS - 1; c++) {
          const wave = Math.sin(time + r * 0.3 + c * 0.2) * 0.03;
          const h00 = heightMap[r][c] + wave;
          const h10 = heightMap[r][c + 1] + wave;
          const h01 = heightMap[r + 1][c] + wave;
          const h11 = heightMap[r + 1][c + 1] + wave;

          const p00 = toIso(c, r, h00);
          const p10 = toIso(c + 1, r, h10);
          const p01 = toIso(c, r + 1, h01);
          const p11 = toIso(c + 1, r + 1, h11);

          const avg = (h00 + h10 + h01 + h11) / 4;
          const l = Math.round(255 - avg * 200);

          ctx.beginPath();
          ctx.moveTo(p00.px, p00.py); ctx.lineTo(p10.px, p10.py);
          ctx.lineTo(p11.px, p11.py); ctx.lineTo(p01.px, p01.py);
          ctx.closePath();
          ctx.fillStyle = `rgba(${l},${l},${l},0.5)`;
          ctx.fill();
          ctx.strokeStyle = 'rgba(255,255,255,0.08)';
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }

      rewardHistory.forEach((reward, idx) => {
        const c = idx % COLS, r = Math.floor(idx / COLS);
        if (r < ROWS) {
          const pt = toIso(c, r, reward);
          ctx.beginPath();
          ctx.arc(pt.px, pt.py, 3, 0, Math.PI * 2);
          ctx.fillStyle = 'rgba(255,255,255,0.8)';
          ctx.fill();
        }
      });

      this.animFrames.set(canvasId, requestAnimationFrame(animate));
    };
    if (!this.isReducedMotion) animate();
  }

  /* ═══ 3. TYPEWRITER TERMINAL ═══ */
  typewriteTerminal(containerId, lines, delay = 12) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';
    let lineIdx = 0;

    const writeLine = () => {
      if (lineIdx >= lines.length) {
        const cur = document.createElement('span');
        cur.className = 'cursor-blink';
        container.lastElementChild?.appendChild(cur);
        return;
      }
      const { text, cls } = lines[lineIdx];
      lineIdx++;
      const div = document.createElement('div');
      div.style.minHeight = '1.4em';
      container.appendChild(div);

      let charIdx = 0;
      const writeChar = () => {
        if (charIdx >= text.length) {
          setTimeout(writeLine, text.startsWith('[START]') ? 300 : text.startsWith('[END]') ? 400 : 40);
          return;
        }
        const span = document.createElement('span');
        span.className = cls || 't-step';
        span.textContent = text[charIdx];
        div.appendChild(span);
        charIdx++;
        container.scrollTop = container.scrollHeight;
        setTimeout(writeChar, delay);
      };
      writeChar();
    };
    setTimeout(writeLine, 600);
  }

  /* ═══ 4. COUNTER ANIMATION ═══ */
  animateCounter(elementId, target, duration = 1200, decimals = 2, suffix = '') {
    const el = document.getElementById(elementId);
    if (!el) return;
    const start = performance.now();
    const tick = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3);
      el.textContent = (target * ease).toFixed(decimals) + suffix;
      if (progress < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  /* ═══ 5. SCROLL REVEAL ═══ */
  initScrollReveal(selector = '.reveal') {
    const els = document.querySelectorAll(selector);
    els.forEach((el, i) => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(12px)';
      el.style.transition = `opacity 0.5s cubic-bezier(0.4,0,0.2,1) ${i * 60}ms, transform 0.5s cubic-bezier(0.4,0,0.2,1) ${i * 60}ms`;
    });
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.style.opacity = '1';
          e.target.style.transform = 'none';
          obs.unobserve(e.target);
        }
      });
    }, { threshold: 0.1 });
    els.forEach(el => obs.observe(el));
  }

  /* ═══ 6. SVG ARC PROGRESS ═══ */
  animateArc(circleId, textId, pct, duration = 1200) {
    const circle = document.getElementById(circleId);
    const text = document.getElementById(textId);
    if (!circle) return;
    const r = parseFloat(circle.getAttribute('r'));
    const circ = 2 * Math.PI * r;
    circle.style.strokeDasharray = `${circ}`;
    circle.style.strokeDashoffset = `${circ}`;
    const start = performance.now();
    const tick = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3);
      circle.style.strokeDashoffset = `${circ - circ * pct * ease}`;
      if (text) text.textContent = Math.round(pct * ease * 100) + '%';
      if (progress < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  destroy(canvasId) {
    const frame = this.animFrames.get(canvasId);
    if (frame) cancelAnimationFrame(frame);
    this.animFrames.delete(canvasId);
    this.canvases.delete(canvasId);
  }
}

window.sqlEngine = new SQLOpsEngine();
