(function () {
  const movementApi = window.AntsMovement || {};
  const combatApi = window.AntsCombat || {};

  // 2D-Vektor fuer Bewegungs-, Distanz- und Richtungsberechnungen.
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

  // Hilfsfunktionen fuer Seitengrenzen und Dokumenthoehe.
  // X-Kanten des .page-Containers in Viewport-Koordinaten (scroll-unabhaengig).
  function getPageEdges() {
    const W    = window.innerWidth;
    const page = document.querySelector('.page');
    if (!page) return { left: 20, right: W - 20 };
    const r    = page.getBoundingClientRect();
    return { left: r.left, right: r.right };
  }

  // Ermittelt die gesamte Dokumenthoehe robust ueber body + documentElement.
  function docHeight() {
    return Math.max(
      document.body.scrollHeight,
      document.documentElement.scrollHeight
    );
  }

  // Pfadgenerierung: U-Form im Dokumentraum mit sinusfoermiger Seitenwelle.
  // Verlauf: linke Seite -> untere linke Kurve -> unten -> rechte Kurve -> rechte Seite.
  function generatePath() {
    const W   = window.innerWidth;
    const H   = docHeight();
    const { left, right } = getPageEdges();

    // Zentriert den Pfad in den Aussenraendern zwischen Seitenbox und Browserkante.
    const lx  = Math.max(4, Math.round(left  / 2));
    const rx  = Math.min(W - 4, Math.round(right + (W - right) / 2));

    // Schwingung fuellt den Randbereich, aber bleibt auf max. 26 px begrenzt.
    const osc = Math.min(26, Math.max(2, lx - 4));
    const per = 190;  // Periode in Dokument-Pixeln (groesser = breitere Kurven).

    const by   = H - 20;  // Y-Koordinate des unteren Abschnitts.
    const cr   = 32;      // Radius der unteren Eckkurven.
    const step = 2;
    const pts  = [];

    // Linke Seite: von oben nach unten.
    for (let y = -12; y <= by - cr; y += step) {
      pts.push(new Vec2(lx + osc * Math.sin((y / per) * Math.PI * 2), y));
    }

    // Untere linke Kurve: Zentrum (lx+cr, by-cr), Winkel PI -> PI/2.
    for (let a = Math.PI; a >= Math.PI / 2; a -= 0.04) {
      pts.push(new Vec2((lx + cr) + cr * Math.cos(a), (by - cr) + cr * Math.sin(a)));
    }

    // Unterkante: von links nach rechts.
    for (let x = lx + cr + step; x <= rx - cr; x += step) {
      pts.push(new Vec2(x, by));
    }

    // Untere rechte Kurve: Zentrum (rx-cr, by-cr), Winkel PI/2 -> 0.
    for (let a = Math.PI / 2; a >= 0; a -= 0.04) {
      pts.push(new Vec2((rx - cr) + cr * Math.cos(a), (by - cr) + cr * Math.sin(a)));
    }

    // Rechte Seite: von unten nach oben.
    for (let y = by - cr - step; y >= -12; y -= step) {
      pts.push(new Vec2(rx + osc * Math.sin((y / per) * Math.PI * 2 + Math.PI), y));
    }

    return pts;
  }

  class Apple {
    constructor(x, y) {
      this.pos       = new Vec2(x, y);
      this.claimed   = false;
      this.collected = false;
      this.wobble    = Math.random() * Math.PI * 2;
    }

    draw(ctx, t) {
      if (this.collected) return;
      const bob = Math.sin(t * 0.002 + this.wobble) * 1.2;
      ctx.save();
      ctx.translate(this.pos.x, this.pos.y + bob);

      // Koerper (groesser + kraeftigeres Rot, damit er auf dem Waldboden auffaellt)
      ctx.fillStyle = '#e23b2e';
      ctx.beginPath();
      ctx.ellipse(0, 0.6, 3.6, 4.3, 0, 0, Math.PI * 2);
      ctx.fill();
      // dunkler Rand fuer Kontrast auf hellen Blaettern wie dunkler Erde
      ctx.strokeStyle = 'rgba(60,12,8,0.55)';
      ctx.lineWidth   = 0.8;
      ctx.stroke();

      // Glanzlicht
      ctx.fillStyle = 'rgba(255,255,255,0.45)';
      ctx.beginPath();
      ctx.ellipse(-1.2, -0.9, 1.2, 1.7, -0.4, 0, Math.PI * 2);
      ctx.fill();

      // Stiel
      ctx.strokeStyle = '#5a3000';
      ctx.lineWidth   = 1.0;
      ctx.beginPath();
      ctx.moveTo(0, -3.6);
      ctx.quadraticCurveTo(2.0, -6.2, 3.0, -7.4);
      ctx.stroke();

      // Blatt
      ctx.fillStyle = '#2e7d32';
      ctx.beginPath();
      ctx.ellipse(1.9, -6.0, 2.0, 1.0, 0.7, 0, Math.PI * 2);
      ctx.fill();

      ctx.restore();
    }
  }

  // Ameisenzustand und Bewegungsparameter.
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
        ctx.fillStyle = '#e23b2e';
        ctx.beginPath();
        ctx.ellipse(-1.8, -2.7, 1.7, 2.1, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = 'rgba(60,12,8,0.5)';
        ctx.lineWidth   = 0.35;
        ctx.stroke();
      }

      ctx.restore();
    }
  }

  // Kurzlebige Barriere, die Ameisen im Umkreis ablenkt.
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

  // Hauptsimulation: Canvas-Setup, Spawn, Update, Rendering und Loop.
  class AntSim {
    constructor() {
      this.canvas = document.createElement('canvas');
      this.canvas.id = 'antsTrailCanvas';
      // Positioniert im Dokumentraum (scrollt mit), hinter dem Seiteninhalt.
      this.canvas.style.cssText =
        'position:absolute;top:0;left:0;pointer-events:none;z-index:0;';
      document.body.insertBefore(this.canvas, document.body.firstChild);
      this.ctx = this.canvas.getContext('2d');

      this.overlayCanvas = document.createElement('canvas');
      this.overlayCanvas.id = 'antsOverlayCanvas';
      this.overlayCanvas.style.cssText =
        'position:absolute;top:0;left:0;pointer-events:none;z-index:2;';
      document.body.appendChild(this.overlayCanvas);
      this.overlayCtx = this.overlayCanvas.getContext('2d');

      this.ants          = [];
      this.overlayAnts   = [];
      this.hitBursts     = [];
      this.apples        = [];
      this.barriers      = [];
      this.mouse         = null;
      this.mouseOnPathMs = 0;
      this.path          = [];
      this.t             = 0;
      this.spawnTimer    = 0;
      this.overlaySpawnMs = 2200;

      this.resize();
      this.spawnApples();
      this.bindEvents();

      // Barrierefreiheit + Performance: bei "Bewegung reduzieren" gar nicht animieren.
      const reduce = window.matchMedia &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (!reduce) this.loop();
    }

    resize() {
      const W = window.innerWidth;
      const H = docHeight();
      this.canvas.width  = W;
      this.canvas.height = H;
      this.overlayCanvas.width  = W;
      this.overlayCanvas.height = H;
      this.path = generatePath();
      for (const ant of this.ants) {
        ant.path    = this.path;
        ant.pathIdx = Math.min(ant.pathIdx, this.path.length - 1);
      }
    }

    divertTrailAntToOverlay() {
      const H = docHeight();
      const { left } = getPageEdges();
      const leftBand = Math.max(36, left + 62);
      const candidates = [];

      for (const ant of this.ants) {
        if (ant.done) continue;
        if (ant.pos.x > leftBand) continue;
        if (ant.pos.y < 20 || ant.pos.y > H - 20) continue;
        candidates.push(ant);
      }

      if (!candidates.length) return false;

      const source = candidates[Math.floor(Math.random() * candidates.length)];
      source.done = true;

      const speed = 0.95 + Math.random() * 0.8;
      this.overlayAnts.push({
        pos: new Vec2(source.pos.x, source.pos.y),
        vx: speed,
        vy: (Math.random() - 0.5) * 0.12,
        angle: 0,
        legPhase: source.legPhase || (Math.random() * Math.PI * 2),
        dead: false,
      });
      return true;
    }

    findClosestPathIndex(pos, preferRight = false) {
      let best = 0;
      let bestD = 1e9;
      const { right } = getPageEdges();

      for (let i = 0; i < this.path.length; i += 2) {
        const p = this.path[i];
        if (preferRight && p.x < right - 54) continue;
        const d = Vec2.dist(pos, p);
        if (d < bestD) {
          bestD = d;
          best = i;
        }
      }

      return best;
    }

    rejoinOverlayAnt(overlayAnt) {
      const idx = this.findClosestPathIndex(overlayAnt.pos, true);
      const ant = new Ant(this.path, idx);
      ant.pos = new Vec2(overlayAnt.pos.x, overlayAnt.pos.y);
      ant.vel = new Vec2(Math.max(0.2, overlayAnt.vx), overlayAnt.vy);
      ant.angle = overlayAnt.angle;
      ant.legPhase = overlayAnt.legPhase;
      this.ants.push(ant);
    }

    drawOverlayAnt(ctx, ant) {
      ctx.save();
      ctx.translate(ant.pos.x, ant.pos.y);
      ctx.rotate(ant.angle);

      const roots = [1.18, 0.14, -0.82];
      ctx.strokeStyle = '#0d0d0d';
      ctx.lineWidth = 0.43;
      for (let i = 0; i < 3; i++) {
        const rx = roots[i];
        const phase = ant.legPhase + i * (Math.PI * 2 / 3);
        const sw = Math.sin(phase) * 1.8;

        ctx.beginPath();
        ctx.moveTo(rx, -0.86);
        ctx.lineTo(rx + sw * 0.4, -2.15);
        ctx.lineTo(rx + sw * 0.54 - 0.38, -3.3);
        ctx.stroke();

        const swR = Math.sin(phase + Math.PI) * 1.8;
        ctx.beginPath();
        ctx.moveTo(rx, 0.86);
        ctx.lineTo(rx + swR * 0.4, 2.15);
        ctx.lineTo(rx + swR * 0.54 - 0.38, 3.3);
        ctx.stroke();
      }

      ctx.fillStyle = '#0d0d0d';
      ctx.beginPath(); ctx.ellipse(-1.72, 0, 1.58, 1.2, 0, 0, Math.PI * 2); ctx.fill();
      ctx.beginPath(); ctx.ellipse(0.03, 0, 0.94, 0.73, 0, 0, Math.PI * 2); ctx.fill();
      ctx.beginPath(); ctx.ellipse(1.4, 0, 0.76, 0.62, 0, 0, Math.PI * 2); ctx.fill();

      ctx.strokeStyle = '#0d0d0d';
      ctx.lineWidth = 0.35;
      ctx.beginPath(); ctx.moveTo(1.9, -0.35); ctx.quadraticCurveTo(3.1, -1.3, 3.7, -0.78); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(1.9, 0.35); ctx.quadraticCurveTo(3.1, 1.3, 3.7, 0.78); ctx.stroke();
      ctx.restore();
    }

    // Platziert drei Aepfel entlang des Pfads, leicht seitlich versetzt.
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

    // Rechnet ein DOM-Event von Viewport- in Dokument-Koordinaten um.
    eventToDocPos(e) {
      const sy = window.scrollY || 0;
      return new Vec2(e.clientX, e.clientY + sy);
    }

    // Aktualisiert die Mausposition fuer die Simulation.
    handleMouseMove(e) {
      this.mouse = this.eventToDocPos(e);
    }

    // Prueft Treffer auf Ameisen bei Pointer-Down.
    handlePointerDown(e) {
      this.tryHitAnt(this.eventToDocPos(e));
    }

    // Setzt Maus-bezogene Zustaende beim Verlassen des Fensters zurueck.
    handleMouseLeave() {
      this.mouse = null;
      this.mouseOnPathMs = 0;
    }

    // Bindet alle globalen Fenster-Events fuer Interaktion und Resize.
    bindEvents() {
      window.addEventListener('mousemove', (e) => this.handleMouseMove(e));
      window.addEventListener('pointerdown', (e) => this.handlePointerDown(e));
      window.addEventListener('mouseleave', () => this.handleMouseLeave());
      window.addEventListener('resize', () => this.resize());
    }

    // Leitet Hit-Tests an die Combat-API weiter.
    tryHitAnt(pos) {
      if (combatApi.tryHitAnt) return combatApi.tryHitAnt(this, pos, Vec2);
      return false;
    }

    // Fuehrt das Bewegungs-Update ueber die Movement-API aus.
    updateMovementFrame(dt) {
      if (!movementApi.updateMovement) return;
      movementApi.updateMovement(this, dt, {
        Vec2, Ant, Barrier, docHeight, getPageEdges,
      });
    }

    // Fuehrt Combat-Nachbearbeitung (z. B. Burst-Lebenszeit) aus.
    updateCombatFrame(dt) {
      if (combatApi.updateHitBursts) {
        combatApi.updateHitBursts(this, dt);
      }
    }

    // Aktualisiert die komplette Simulation fuer ein Frame.
    update(dt) {
      this.t += dt;
      this.updateMovementFrame(dt);
      this.updateCombatFrame(dt);
    }

    // Berechnet das sichtbare Zeichenband (+ Sicherheitsrand) fuer Teil-Redraws.
    visibleBand() {
      const H = this.canvas.height;
      const vTop = Math.max(0, (window.scrollY || 0) - 40);
      const vH = Math.min(H - vTop, window.innerHeight + 80);
      return {
        vTop, vH, top: vTop - 20, bot: vTop + vH + 20,
      };
    }

    // Loescht nur die relevanten Randbereiche statt des kompletten Canvas.
    clearVisibleBands(ctx, octx, band) {
      const W = this.canvas.width;
      const H = this.canvas.height;
      const edges = getPageEdges();
      const left = edges.left;
      const right = edges.right;
      const buf = 55; // osc(26) + body(5) + safety buffer

      ctx.clearRect(0, band.vTop, left + buf, band.vH);
      ctx.clearRect(right - buf, band.vTop, W - (right - buf), band.vH);
      ctx.clearRect(0, H - 80, W, 80);
      octx.clearRect(0, band.vTop, W, band.vH);
    }

    // Zeichnet nur sichtbare Aepfel innerhalb des aktuellen Zeichenbands.
    drawVisibleApples(ctx, band) {
      for (const apple of this.apples) {
        if (apple.pos.y >= band.top && apple.pos.y <= band.bot) {
          apple.draw(ctx, this.t);
        }
      }
    }

    // Zeichnet nur sichtbare Trail-Ameisen innerhalb des aktuellen Zeichenbands.
    drawVisibleTrailAnts(ctx, band) {
      for (const ant of this.ants) {
        if (ant.pos.y >= band.top && ant.pos.y <= band.bot) {
          ant.draw(ctx);
        }
      }
    }

    // Zeichnet nur sichtbare Overlay-Ameisen innerhalb des aktuellen Zeichenbands.
    drawVisibleOverlayAnts(octx, band) {
      for (const ant of this.overlayAnts) {
        if (ant.pos.y >= band.top && ant.pos.y <= band.bot) {
          this.drawOverlayAnt(octx, ant);
        }
      }
    }

    // Zeichnet Treffer-Bursts auf die angegebene Zeichenebene.
    drawHitBurstsForLayer(layerCtx, band) {
      if (combatApi.drawHitBursts) {
        combatApi.drawHitBursts(layerCtx, this.hitBursts, band.top, band.bot);
      }
    }

    // Rendert ein komplettes Frame fuer Trail- und Overlay-Canvas.
    draw() {
      const ctx  = this.ctx;
      const octx = this.overlayCtx;
      const band = this.visibleBand();

      this.clearVisibleBands(ctx, octx, band);
      this.drawVisibleApples(ctx, band);
      this.drawVisibleTrailAnts(ctx, band);
      this.drawHitBurstsForLayer(ctx, band);
      this.drawVisibleOverlayAnts(octx, band);
      this.drawHitBurstsForLayer(octx, band);
    }

    // Verarbeitet ein Animations-Frame mit Delta-Kappung und Tab-Optimierung.
    processFrame(now, state) {
      const dt = Math.min(now - state.last, 50);
      state.last = now;
      if (!document.hidden) {
        this.update(dt);
        this.draw();
      }
    }

    // Startet den requestAnimationFrame-Loop.
    loop() {
      const state = { last: performance.now() };
      const tick = (now) => {
        this.processFrame(now, state);
        requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    }
  }

  window.AntsCore = { AntSim: AntSim };

  // Bindet die Komponente in den aktuellen Seitenkontext ein.
  function mountAnts() {
    if (window.ANTS_ENABLED === false) return;
    if (!window.AntsMovement || !window.AntsCombat) return;
    new AntSim();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountAnts);
  } else {
    mountAnts();
  }
})();

