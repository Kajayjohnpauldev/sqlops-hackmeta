/**
 * SQLOps Oracle — Charts Engine (Canvas 2D only, zero dependencies)
 * Designed by K. Ajay John Paul | KL University Hyderabad
 */

class SQLOpsCharts {

  _font(size, weight) { return `${weight || ''} ${size}px "IBM Plex Mono"`.trim(); }

  /* ═══ HORIZONTAL BAR CHART ═══ */
  barChart(canvasId, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    canvas.width = canvas.offsetWidth * 2; canvas.height = canvas.offsetHeight * 2;
    ctx.scale(2, 2);
    const W = canvas.offsetWidth, H = canvas.offsetHeight;
    const PL = options.labelWidth || 140, PR = 80, PT = 10, PB = 10;
    const barH = Math.min((H - PT - PB) / data.length - 6, 28);
    const MAX = Math.max(...data.map(d => d.value));
    const chartW = W - PL - PR;

    data.forEach((item, i) => {
      const y = PT + i * (barH + 6);
      const barW = (item.value / MAX) * chartW;
      let progress = 0;

      const draw = () => {
        ctx.clearRect(PL - 2, y - 1, chartW + PR + 4, barH + 3);
        // Track
        ctx.fillStyle = 'rgba(10,10,10,0.04)';
        ctx.fillRect(PL, y, chartW, barH);
        // Bar
        const opacity = Math.max(0.25, 0.9 - i * 0.07);
        ctx.fillStyle = `rgba(10,10,10,${opacity})`;
        const rw = barW * progress;
        ctx.beginPath();
        ctx.roundRect(PL, y, rw, barH, 2);
        ctx.fill();
        // Value
        if (progress > 0.3) {
          ctx.font = this._font(10); ctx.textAlign = 'left';
          ctx.fillStyle = 'rgba(10,10,10,0.45)';
          const fmt = options.format ? options.format(item.value) : item.value.toLocaleString();
          ctx.fillText(fmt, PL + rw + 8, y + barH / 2 + 4);
        }
        if (progress < 1) { progress = Math.min(progress + 0.035, 1); requestAnimationFrame(draw); }
      };
      // Label (static)
      ctx.font = this._font(11); ctx.textAlign = 'right';
      ctx.fillStyle = 'rgba(10,10,10,0.55)';
      ctx.fillText(item.label.substring(0, 20), PL - 10, y + barH / 2 + 4);
      setTimeout(draw, i * 60);
    });
  }

  /* ═══ LINE CHART ═══ */
  lineChart(canvasId, datasets, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    canvas.width = canvas.offsetWidth * 2; canvas.height = canvas.offsetHeight * 2;
    ctx.scale(2, 2);
    const W = canvas.offsetWidth, H = canvas.offsetHeight;
    const PAD = { top: 20, right: 20, bottom: 36, left: 44 };
    const cW = W - PAD.left - PAD.right, cH = H - PAD.top - PAD.bottom;

    const allV = datasets.flatMap(d => d.data);
    const minY = 0, maxY = Math.max(1, ...allV);
    const toX = (i, len) => PAD.left + (i / Math.max(len - 1, 1)) * cW;
    const toY = v => PAD.top + cH - ((v - minY) / (maxY - minY)) * cH;

    // Grid
    ctx.setLineDash([2, 4]);
    [0, 0.25, 0.5, 0.75, 1.0].forEach(v => {
      const y = toY(v);
      ctx.beginPath(); ctx.moveTo(PAD.left, y); ctx.lineTo(W - PAD.right, y);
      ctx.strokeStyle = 'rgba(10,10,10,0.08)'; ctx.lineWidth = 0.5; ctx.stroke();
      ctx.fillStyle = 'rgba(10,10,10,0.3)'; ctx.font = this._font(9);
      ctx.textAlign = 'right'; ctx.fillText(v.toFixed(2), PAD.left - 6, y + 3);
    });
    ctx.setLineDash([]);

    // Axes
    ctx.strokeStyle = 'rgba(10,10,10,0.12)'; ctx.lineWidth = 0.5;
    ctx.beginPath();
    ctx.moveTo(PAD.left, PAD.top); ctx.lineTo(PAD.left, H - PAD.bottom);
    ctx.lineTo(W - PAD.right, H - PAD.bottom); ctx.stroke();

    // Draw each dataset with animation
    datasets.forEach((ds, di) => {
      const data = ds.data;
      const dash = di === 0 ? [] : di === 1 ? [6, 3] : [2, 3];
      const opacity = di === 0 ? 0.85 : di === 1 ? 0.55 : 0.35;
      const dotSize = di === 0 ? 3.5 : 2.5;
      let drawn = 0;

      const drawLine = () => {
        // Clear and redraw this line only by layering
        ctx.setLineDash(dash);
        ctx.strokeStyle = `rgba(10,10,10,${opacity})`;
        ctx.lineWidth = di === 0 ? 2 : 1.5;
        ctx.beginPath();
        for (let i = 0; i <= Math.min(drawn, data.length - 1); i++) {
          const x = toX(i, data.length), y = toY(data[i]);
          if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        ctx.stroke(); ctx.setLineDash([]);

        // Area fill for first dataset
        if (di === 0 && drawn > 0) {
          ctx.beginPath();
          ctx.moveTo(toX(0, data.length), toY(0));
          for (let i = 0; i <= Math.min(drawn, data.length - 1); i++) {
            ctx.lineTo(toX(i, data.length), toY(data[i]));
          }
          ctx.lineTo(toX(Math.min(drawn, data.length - 1), data.length), toY(0));
          ctx.closePath();
          ctx.fillStyle = 'rgba(10,10,10,0.04)';
          ctx.fill();
        }

        for (let i = 0; i <= Math.min(drawn, data.length - 1); i++) {
          ctx.beginPath();
          ctx.arc(toX(i, data.length), toY(data[i]), dotSize, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(10,10,10,${opacity})`;
          ctx.fill();
        }

        if (drawn < data.length - 1) { drawn++; requestAnimationFrame(drawLine); }
      };
      setTimeout(drawLine, di * 300);
    });

    // X labels
    const d0 = datasets[0].data;
    const step = Math.max(1, Math.ceil(d0.length / 10));
    d0.forEach((_, i) => {
      if (i % step === 0 || i === d0.length - 1) {
        ctx.fillStyle = 'rgba(10,10,10,0.3)'; ctx.font = this._font(9);
        ctx.textAlign = 'center';
        ctx.fillText(`${i + 1}`, toX(i, d0.length), H - PAD.bottom + 16);
      }
    });
  }

  /* ═══ RADAR CHART ═══ */
  radarChart(canvasId, data, labels) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    canvas.width = canvas.offsetWidth * 2; canvas.height = canvas.offsetHeight * 2;
    ctx.scale(2, 2);
    const W = canvas.offsetWidth, H = canvas.offsetHeight;
    const CX = W / 2, CY = H / 2, R = Math.min(W, H) / 2 - 36;
    const N = labels.length;
    const angle = i => (i / N) * Math.PI * 2 - Math.PI / 2;

    let progress = 0;
    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      // Grid rings
      [0.25, 0.5, 0.75, 1.0].forEach(s => {
        ctx.beginPath();
        for (let i = 0; i < N; i++) {
          const x = CX + Math.cos(angle(i)) * R * s;
          const y = CY + Math.sin(angle(i)) * R * s;
          i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.strokeStyle = 'rgba(10,10,10,0.08)'; ctx.lineWidth = 0.5; ctx.stroke();
      });
      // Spokes + labels
      for (let i = 0; i < N; i++) {
        ctx.beginPath(); ctx.moveTo(CX, CY);
        ctx.lineTo(CX + Math.cos(angle(i)) * R, CY + Math.sin(angle(i)) * R);
        ctx.strokeStyle = 'rgba(10,10,10,0.08)'; ctx.lineWidth = 0.5; ctx.stroke();
        const lx = CX + Math.cos(angle(i)) * (R + 22);
        const ly = CY + Math.sin(angle(i)) * (R + 22);
        ctx.fillStyle = 'rgba(10,10,10,0.5)'; ctx.font = this._font(9);
        ctx.textAlign = 'center'; ctx.fillText(labels[i], lx, ly + 3);
      }
      // Data polygon
      ctx.beginPath();
      data.forEach((val, i) => {
        const r = R * val * progress;
        const x = CX + Math.cos(angle(i)) * r;
        const y = CY + Math.sin(angle(i)) * r;
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      });
      ctx.closePath();
      ctx.fillStyle = 'rgba(10,10,10,0.06)'; ctx.fill();
      ctx.strokeStyle = 'rgba(10,10,10,0.65)'; ctx.lineWidth = 1.5; ctx.stroke();
      // Dots
      data.forEach((val, i) => {
        const r = R * val * progress;
        ctx.beginPath();
        ctx.arc(CX + Math.cos(angle(i)) * r, CY + Math.sin(angle(i)) * r, 3, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(10,10,10,0.7)'; ctx.fill();
      });

      if (progress < 1) { progress = Math.min(progress + 0.025, 1); requestAnimationFrame(draw); }
    };
    draw();
  }

  /* ═══ SCATTER PLOT with regression ═══ */
  scatterPlot(canvasId, points, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    canvas.width = canvas.offsetWidth * 2; canvas.height = canvas.offsetHeight * 2;
    ctx.scale(2, 2);
    const W = canvas.offsetWidth, H = canvas.offsetHeight;
    const PAD = { top: 20, right: 20, bottom: 36, left: 44 };
    const cW = W - PAD.left - PAD.right, cH = H - PAD.top - PAD.bottom;
    const maxX = Math.max(...points.map(p => p.x));
    const toX = v => PAD.left + (v / maxX) * cW;
    const toY = v => PAD.top + cH - v * cH;

    // Grid
    ctx.setLineDash([2, 4]);
    [0, 0.25, 0.5, 0.75, 1].forEach(v => {
      ctx.beginPath(); ctx.moveTo(PAD.left, toY(v)); ctx.lineTo(W - PAD.right, toY(v));
      ctx.strokeStyle = 'rgba(10,10,10,0.06)'; ctx.lineWidth = 0.5; ctx.stroke();
      ctx.fillStyle = 'rgba(10,10,10,0.3)'; ctx.font = this._font(9);
      ctx.textAlign = 'right'; ctx.fillText(v.toFixed(2), PAD.left - 6, toY(v) + 3);
    });
    ctx.setLineDash([]);

    // Regression line
    const n = points.length;
    const sx = points.reduce((a, p) => a + p.x, 0);
    const sy = points.reduce((a, p) => a + p.y, 0);
    const sxy = points.reduce((a, p) => a + p.x * p.y, 0);
    const sx2 = points.reduce((a, p) => a + p.x * p.x, 0);
    const slope = (n * sxy - sx * sy) / (n * sx2 - sx * sx);
    const intercept = (sy - slope * sx) / n;

    ctx.beginPath();
    ctx.moveTo(toX(0), toY(Math.max(0, intercept)));
    ctx.lineTo(toX(maxX), toY(Math.min(1, slope * maxX + intercept)));
    ctx.strokeStyle = 'rgba(10,10,10,0.18)'; ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]); ctx.stroke(); ctx.setLineDash([]);

    // R^2 label
    const mean = sy / n;
    const ssTot = points.reduce((a, p) => a + (p.y - mean) ** 2, 0);
    const ssRes = points.reduce((a, p) => a + (p.y - (slope * p.x + intercept)) ** 2, 0);
    const r2 = Math.max(0, 1 - ssRes / ssTot);
    ctx.fillStyle = 'rgba(10,10,10,0.4)'; ctx.font = this._font(10);
    ctx.textAlign = 'right';
    ctx.fillText(`R\u00B2 = ${r2.toFixed(2)}`, W - PAD.right, PAD.top + 12);

    // Points (staggered)
    points.forEach((p, i) => {
      setTimeout(() => {
        const opacity = p.task === 0 ? 0.85 : p.task === 1 ? 0.55 : 0.3;
        ctx.beginPath();
        ctx.arc(toX(p.x), toY(p.y), 5, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(10,10,10,${opacity})`; ctx.fill();
        ctx.strokeStyle = 'rgba(10,10,10,0.15)'; ctx.lineWidth = 0.5; ctx.stroke();
      }, i * 50);
    });
  }

  /* ═══ MINI SPARKLINE ═══ */
  sparkline(canvasId, data, color = 'rgba(10,10,10,0.6)') {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    canvas.width = canvas.offsetWidth * 2; canvas.height = canvas.offsetHeight * 2;
    ctx.scale(2, 2);
    const W = canvas.offsetWidth, H = canvas.offsetHeight;
    const max = Math.max(1, ...data);
    ctx.beginPath();
    data.forEach((v, i) => {
      const x = (i / (data.length - 1)) * W;
      const y = H - (v / max) * H * 0.9;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.strokeStyle = color; ctx.lineWidth = 1.5; ctx.stroke();
  }
}

window.sqlCharts = new SQLOpsCharts();
