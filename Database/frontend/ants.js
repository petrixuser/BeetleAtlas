(function () {
  // ── Vec2 ──────────────────────────────────────────────────────────────────
  class Vec2 {
    constructor(x = 0, y = 0) { this.x = x; this.y = y; }
    add(v)   { return new Vec2(this.x + v.x, this.y + v.y); }
    sub(v)   { return new Vec2(this.x - v.x, this.y - v.y); }
    scale(s) { return new Vec2(this.x * s, this.y * s); }
    len()    { return Math.sqrt(this.x * this.x + this.y * this.y); }
    norm()   { const l = this.len(); return l > 0 ? this.scale(1 / l) : new Vec2(); }
    limit(m) { const l = this.len(); return l > m ? this.scale(m / l) : new Vec2(this.x, this.y); }
    static dist(a, b) { return a.sub(b).len(); }
  }

  // ── Helpers ────────────────────────────────────────────────────────────────
  // x-edges of .page box in viewport coords (don't change on scroll)
  function getPageEdges() {
    const W    = window.innerWidth;
    const page = document.querySelector('.page');
    if (!page) return { left: 20, right: W - 20 };
    const r    = page.getBoundingClientRect();
    return { left: r.left, right: r.right };
  }

  function docHeight() {
    return Math.max(
      document.body.scrollHeight,
      document.documentElement.scrollHeight
    );
  }

  // ── Path generation ────────────────────────────────────────────────────────
  // U-shape in DOCUMENT space: left margin ↓ → arc → bottom → arc → right ↑
  // Large sinusoidal oscillation gives the "kurviger" wave character.
  function generatePath() {
    const W   = window.innerWidth;
    const H   = docHeight();
    const { left, right } = getPageEdges();

    // Centre the path in the margin between page-box and browser edge
    const lx  = Math.max(4, Math.round(left  / 2));
    const rx  = Math.min(W - 4, Math.round(right + (W - right) / 2));

    // Oscillation fills the available half-margin on each side, capped at 26 px
    const osc = Math.min(26, Math.max(2, lx - 4));
    const per = 190;  // period in document-px (bigger → fewer, wider curves)

    const by   = H - 20;  // y of bottom section
    const cr   = 32;      // corner-arc radius
    const step = 2;
    const pts  = [];

    // Left side: top → bottom
    for (let y = -12; y <= by - cr; y += step) {
      pts.push(new Vec2(lx + osc * Math.sin((y / per) * Math.PI * 2), y));
    }

    // Bottom-left arc: centre (lx+cr, by-cr), π → π/2
    for (let a = Math.PI; a >= Math.PI / 2; a -= 0.04) {
      pts.push(new Vec2((lx + cr) + cr * Math.cos(a), (by - cr) + cr * Math.sin(a)));
    }

    // Bottom: left → right
    for (let x = lx + cr + step; x <= rx - cr; x += step) {
      pts.push(new Vec2(x, by));
    }

    // Bottom-right arc: centre (rx-cr, by-cr), π/2 → 0
    for (let a = Math.PI / 2; a >= 0; a -= 0.04) {
      pts.push(new Vec2((rx - cr) + cr * Math.cos(a), (by - cr) + cr * Math.sin(a)));
    }

    // Right side: bottom → top
    for (let y = by - cr - step; y >= -12; y -= step) {
      pts.push(new Vec2(rx + osc * Math.sin((y / per) * Math.PI * 2 + Math.PI), y));
    }

    return pts;
  }

  // ── Apple ─────────────────────────────────────────────────────────────────
  class Apple {
    constructor(x, y) {
      this.pos       = new Vec2(x, y);
      this.claimed   = false;
      this.collected = false;
      this.wobble    = Math.random() * Math.PI * 2;
    }

    draw(ctx, t) {
      if (this.collected) return;
      const bob = Math.sin(t * 0.002 + this.wobble) * 1;
      ctx.save();
      ctx.translate(this.pos.x, this.pos.y + bob);

      ctx.fillStyle = '#c0392b';
      ctx.beginPath();
      ctx.ellipse(0, 0.4, 2.2, 2.6, 0, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = 'rgba(255,255,255,0.2)';
      ctx.beginPath();
      ctx.ellipse(-0.7, -0.5, 0.75, 1.1, -0.4, 0, Math.PI * 2);
      ctx.fill();

      ctx.strokeStyle = '#5a3000';
      ctx.lineWidth   = 0.6;
      ctx.beginPath();
      ctx.moveTo(0, -2.2);
      ctx.quadraticCurveTo(1.2, -3.8, 1.8, -4.5);
      ctx.stroke();

      ctx.fillStyle = '#2e7d32';
      ctx.beginPath();
      ctx.ellipse(1.1, -3.6, 1.2, 0.6, 0.7, 0, Math.PI * 2);
      ctx.fill();

      ctx.restore();
    }
  }

  // ── Ant ───────────────────────────────────────────────────────────────────
  const STATE     = { FOLLOW: 0, SEEK: 1 };
  const ANT_SPEED = 1.35;
  const MAX_FORCE = 0.24;
  const FLEE_R    = 52;
  const BARRIER_R = 44;
  const SENSE_R   = 65;
  const PICKUP_R  = 6;
  const SEP_R     = 5;

  class Ant {
    constructor(path, idx = 0) {
      this.path     = path;
      this.pathIdx  = idx;
      this.pos      = new Vec2(path[idx].x, path[idx].y);
      this.vel      = new Vec2(0, ANT_SPEED);
      this.acc      = new Vec2();
      this.angle    = 0;
      this.legPhase = Math.random() * Math.PI * 2;
      this.speed    = ANT_SPEED * (0.88 + Math.random() * 0.28);
      this.state    = STATE.FOLLOW;
      this.apple    = null;  // apple reference; kept after pickup for visual
      this.done     = false;
    }

    steer(target) {
      return target.sub(this.pos).norm().scale(this.speed).sub(this.vel).limit(MAX_FORCE);
    }

    flee(threat, r) {
      const d = Vec2.dist(this.pos, threat);
      if (d >= r) return new Vec2();
      return this.pos.sub(threat).norm().scale((1 - d / r) * MAX_FORCE * 4.5);
    }

    closestIdx() {
      let best = this.pathIdx, bestD = 1e9;
      const lo = Math.max(0, this.pathIdx - 30);
      const hi = Math.min(this.path.length - 1, this.pathIdx + 60);
      for (let i = lo; i <= hi; i++) {
        const d = Vec2.dist(this.pos, this.path[i]);
        if (d < bestD) { bestD = d; best = i; }
      }
      return best;
    }

    update(mouse, barriers, apples, ants) {
      this.acc = new Vec2();

      if (this.state === STATE.FOLLOW) {
        this.pathIdx = this.closestIdx();
        if (this.pathIdx >= this.path.length - 18) { this.done = true; return; }

        const ahead = Math.min(this.path.length - 1, this.pathIdx + 20);
        this.acc = this.acc.add(this.steer(this.path[ahead]).scale(1.6));

        // Sense unclaimed apple only if not already carrying one
        if (!this.apple) {
          for (const a of apples) {
            if (!a.claimed && !a.collected && Vec2.dist(this.pos, a.pos) < SENSE_R) {
              a.claimed = true; this.apple = a; this.state = STATE.SEEK; break;
            }
          }
        }
      }

      if (this.state === STATE.SEEK && this.apple) {
        if (Vec2.dist(this.pos, this.apple.pos) < PICKUP_R) {
          this.apple.collected = true;  // remove from world
          this.state = STATE.FOLLOW;    // continue on trail carrying it
        } else {
          // Stay loosely on path while detouring to apple
          this.pathIdx = this.closestIdx();
          const ahead  = Math.min(this.path.length - 1, this.pathIdx + 20);
          this.acc = this.acc.add(this.steer(this.path[ahead]).scale(0.6));
          this.acc = this.acc.add(this.steer(this.apple.pos).scale(1.8));
        }
      }

      // Flee cursor (document coordinates)
      if (mouse) this.acc = this.acc.add(this.flee(mouse, FLEE_R));

      // Flee barriers
      for (const b of barriers) {
        this.acc = this.acc.add(this.flee(b.pos, BARRIER_R).scale(b.strength));
      }

      // Separation: tight column
      let sep = new Vec2(), sepN = 0;
      for (const o of ants) {
        if (o === this) continue;
        const d = Vec2.dist(this.pos, o.pos);
        if (d < SEP_R && d > 0) { sep = sep.add(this.pos.sub(o.pos).norm().scale(1 / d)); sepN++; }
      }
      if (sepN > 0) this.acc = this.acc.add(sep.scale(0.25));

      this.vel      = this.vel.add(this.acc).limit(this.speed);
      this.pos      = this.pos.add(this.vel);
      if (this.vel.len() > 0.1) this.angle = Math.atan2(this.vel.y, this.vel.x);
      this.legPhase += this.vel.len() * 0.42;
    }

    draw(ctx) {
      ctx.save();
      ctx.translate(this.pos.x, this.pos.y);
      ctx.rotate(this.angle);

      // Legs
      const roots = [1.22, 0.17, -0.87];
      ctx.strokeStyle = '#111111';
      ctx.lineWidth   = 0.45;

      for (let i = 0; i < 3; i++) {
        const rx    = roots[i];
        const phase = this.legPhase + i * (Math.PI * 2 / 3);
        const sw    = Math.sin(phase) * 1.9;
        const lf    = Math.abs(Math.sin(phase)) * 0.9;

        ctx.beginPath();
        ctx.moveTo(rx, -0.9);
        ctx.lineTo(rx + sw * 0.4, -2.3);
        ctx.lineTo(rx + sw * 0.55 - 0.4, -3.5 - lf);
        ctx.stroke();

        const phR = phase + Math.PI;
        const swR = Math.sin(phR) * 1.9;
        const lfR = Math.abs(Math.sin(phR)) * 0.9;
        ctx.beginPath();
        ctx.moveTo(rx, 0.9);
        ctx.lineTo(rx + swR * 0.4, 2.3);
        ctx.lineTo(rx + swR * 0.55 - 0.4, 3.5 + lfR);
        ctx.stroke();
      }

      ctx.fillStyle = '#111111';

      // Abdomen, thorax, head
      ctx.beginPath(); ctx.ellipse(-1.82, 0, 1.68, 1.26, 0, 0, Math.PI * 2); ctx.fill();
      ctx.beginPath(); ctx.ellipse(0.07,  0, 0.98, 0.77, 0, 0, Math.PI * 2); ctx.fill();
      ctx.beginPath(); ctx.ellipse(1.47,  0, 0.81, 0.67, 0, 0, Math.PI * 2); ctx.fill();

      // Antennae
      ctx.strokeStyle = '#111111';
      ctx.lineWidth   = 0.38;
      ctx.beginPath(); ctx.moveTo(2.0, -0.4); ctx.quadraticCurveTo(3.3, -1.5, 4.0, -0.9); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(2.0,  0.4); ctx.quadraticCurveTo(3.3,  1.5, 4.0,  0.9); ctx.stroke();

      // Carried apple
      if (this.apple) {
        ctx.fillStyle = '#c0392b';
        ctx.beginPath();
        ctx.ellipse(-1.8, -2.5, 1.3, 1.6, 0, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.restore();
    }
  }

  // ── Barrier ───────────────────────────────────────────────────────────────
  class Barrier {
    constructor(x, y) {
      this.pos      = new Vec2(x, y);
      this.strength = 0.2;
      this.alive    = true;
    }
    update(mouse) {
      if (mouse && Vec2.dist(this.pos, mouse) < 26) {
        this.strength = Math.min(2.0, this.strength + 0.04);
        this.pos      = new Vec2(mouse.x, mouse.y);
      } else {
        this.strength -= 0.006;
        if (this.strength <= 0) this.alive = false;
      }
    }
  }

  // ── Simulation ────────────────────────────────────────────────────────────
  class AntSim {
    constructor() {
      this.canvas = document.createElement('canvas');
      // position:absolute → lives in document space, scrolls with content.
      // z-index:0 + .page z-index:1 → ants appear behind page content.
      this.canvas.style.cssText =
        'position:absolute;top:0;left:0;pointer-events:none;z-index:0;';
      document.body.insertBefore(this.canvas, document.body.firstChild);
      this.ctx = this.canvas.getContext('2d');

      this.ants          = [];
      this.apples        = [];
      this.barriers      = [];
      this.mouse         = null;
      this.mouseOnPathMs = 0;
      this.path          = [];
      this.t             = 0;
      this.spawnTimer    = 0;

      this.resize();
      this.spawnApples();
      this.bindEvents();
      this.loop();
    }

    resize() {
      const W = window.innerWidth;
      const H = docHeight();
      this.canvas.width  = W;
      this.canvas.height = H;
      this.path = generatePath();
      for (const ant of this.ants) {
        ant.path    = this.path;
        ant.pathIdx = Math.min(ant.pathIdx, this.path.length - 1);
      }
    }

    // Apples placed at three spots along the path, inset slightly from it
    spawnApples() {
      const n   = this.path.length;
      const seg = Math.floor(n / 3);
      const W   = window.innerWidth;

      const places = [
        Math.floor(seg * 0.2 + Math.random() * seg * 0.5),
        Math.floor(seg * 1.1 + Math.random() * seg * 0.6),
        Math.floor(seg * 2.1 + Math.random() * seg * 0.5),
      ];

      for (const idx of places) {
        const pt  = this.path[Math.min(idx, n - 1)];
        const off = 12 + Math.random() * 8;
        const ix  = pt.x < W / 2 ? pt.x + off : pt.x - off;
        this.apples.push(new Apple(ix, pt.y + (Math.random() - 0.5) * 18));
      }
    }

    nearPath(pos, r) {
      for (let i = 0; i < this.path.length; i += 5) {
        if (Vec2.dist(pos, this.path[i]) < r) return true;
      }
      return false;
    }

    bindEvents() {
      window.addEventListener('mousemove', e => {
        // Convert viewport coords → document coords
        const sy      = window.scrollY || 0;
        this.mouse    = new Vec2(e.clientX, e.clientY + sy);
      });
      window.addEventListener('mouseleave', () => {
        this.mouse = null; this.mouseOnPathMs = 0;
      });
      window.addEventListener('resize', () => this.resize());
    }

    update(dt) {
      this.t += dt;

      // Continuous spawn at path start
      this.spawnTimer += dt;
      if (this.spawnTimer > 310 && this.ants.length < 80) {
        this.spawnTimer = 0;
        this.ants.push(new Ant(this.path, 0));
      }

      // Remove ants that completed the path
      this.ants = this.ants.filter(a => !a.done);

      // Mouse-cut barrier detection
      if (this.mouse && this.nearPath(this.mouse, 20)) {
        this.mouseOnPathMs += dt;
        if (this.mouseOnPathMs > 550) {
          const nearby = this.barriers.find(b => Vec2.dist(b.pos, this.mouse) < 26);
          if (!nearby) this.barriers.push(new Barrier(this.mouse.x, this.mouse.y));
        }
      } else {
        this.mouseOnPathMs = 0;
      }

      for (const b of this.barriers) b.update(this.mouse);
      this.barriers = this.barriers.filter(b => b.alive);

      for (const ant of this.ants) {
        ant.update(this.mouse, this.barriers, this.apples, this.ants);
      }

      // Off-screen safety net
      const W = window.innerWidth, H = docHeight();
      for (const ant of this.ants) {
        if (ant.pos.x < -80 || ant.pos.x > W + 80 ||
            ant.pos.y < -80 || ant.pos.y > H + 80) {
          ant.done = true;
        }
      }

      // Respawn apples when all collected
      if (this.apples.every(a => a.collected)) {
        this.apples = [];
        this.spawnApples();
      }
    }

    draw() {
      const ctx  = this.ctx;
      const W    = this.canvas.width;
      const H    = this.canvas.height;
      const { left, right } = getPageEdges();
      const buf  = 55; // osc(26) + body(5) + safety buffer

      // Performance: clear only the narrow edge strips where ants actually run.
      // The page content (z-index:1) hides any stale pixels that slip inward.
      ctx.clearRect(0,         0, left  + buf, H);
      ctx.clearRect(right - buf, 0, W - (right - buf), H);
      ctx.clearRect(0, H - 80, W, 80);

      for (const a of this.apples) a.draw(ctx, this.t);
      for (const ant of this.ants)  ant.draw(ctx);
    }

    loop() {
      let last = performance.now();
      const tick = (now) => {
        const dt = Math.min(now - last, 50);
        last = now;
        this.update(dt);
        this.draw();
        requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new AntSim());
  } else {
    new AntSim();
  }
})();
