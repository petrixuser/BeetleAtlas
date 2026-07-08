(function () {
  // Sucht das naechste Trail-Ameisenziel innerhalb des Treffer-Radius.
  function findNearestTrailAnt(sim, pos, Vec2, hitRadius) {
    var nearest = null;
    var bestD = hitRadius;

    sim.ants.forEach(function (ant) {
      var d = Vec2.dist(ant.pos, pos);
      if (d <= bestD) {
        bestD = d;
        nearest = ant;
      }
    });

    return { ant: nearest, bestD: bestD };
  }

  // Sucht das naechste Overlay-Ziel und vergleicht mit einem bestehenden Bestwert.
  function findNearestOverlayAnt(sim, pos, Vec2, currentBestD) {
    var nearest = null;
    var bestD = currentBestD;

    sim.overlayAnts.forEach(function (ant) {
      var d = Vec2.dist(ant.pos, pos);
      if (d <= bestD) {
        bestD = d;
        nearest = ant;
      }
    });

    return { ant: nearest, bestD: bestD };
  }

  // Markiert eine getroffene Ameise als entfernt und erzeugt den Treffer-Effekt.
  function applyHit(sim, ant, kind, Vec2) {
    if (kind === "overlay") ant.dead = true;
    else ant.done = true;

    sim.hitBursts.push({
      pos: new Vec2(ant.pos.x, ant.pos.y),
      life: 220,
    });
  }

  // Fuehrt einen Hit-Test gegen Trail- und Overlay-Ameisen aus.
  function tryHitAnt(sim, pos, Vec2) {
    var HIT_R = 14;
    var trailHit = findNearestTrailAnt(sim, pos, Vec2, HIT_R);
    var overlayHit = findNearestOverlayAnt(sim, pos, Vec2, trailHit.bestD);

    if (overlayHit.ant) {
      applyHit(sim, overlayHit.ant, "overlay", Vec2);
      return true;
    }
    if (trailHit.ant) {
      applyHit(sim, trailHit.ant, "trail", Vec2);
      return true;
    }
    return false;
  }

  // Reduziert die Lebenszeit aktiver Treffer-Bursts und entfernt abgelaufene.
  function updateHitBursts(sim, dt) {
    sim.hitBursts.forEach(function (burst) { burst.life -= dt; });
    sim.hitBursts = sim.hitBursts.filter(function (b) { return b.life > 0; });
  }

  // Zeichnet sichtbare Treffer-Bursts als expandierende Kreise.
  function drawHitBursts(ctx, hitBursts, top, bot) {
    hitBursts.forEach(function (burst) {
      if (burst.pos.y < top || burst.pos.y > bot) return;
      var p = Math.max(0, Math.min(1, burst.life / 220));
      var r = 2 + (1 - p) * 8;
      ctx.save();
      ctx.globalAlpha = p * 0.75;
      ctx.fillStyle = "#b50f0f";
      ctx.beginPath();
      ctx.arc(burst.pos.x, burst.pos.y, r, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    });
  }

  window.AntsCombat = {
    tryHitAnt: tryHitAnt,
    updateHitBursts: updateHitBursts,
    drawHitBursts: drawHitBursts,
  };
})();
