(function () {
  // Spawnt neue Trail-Ameisen am Pfadanfang mit Spawn-Limit.
  function spawnTrailAnts(sim, dt, Ant) {
    sim.spawnTimer += dt;
    if (sim.spawnTimer > 310 && sim.ants.length < 80) {
      sim.spawnTimer = 0;
      sim.ants.push(new Ant(sim.path, 0));
    }
  }

  // Entfernt Ameisen, die den Pfad bereits abgeschlossen haben.
  function pruneCompletedTrailAnts(sim) {
    sim.ants = sim.ants.filter(function (ant) { return !ant.done; });
  }

  // Erstellt beim "Schneiden" der Spur eine temporaere Barriere.
  function detectMouseBarrier(sim, dt, Vec2, Barrier) {
    if (sim.mouse && sim.nearPath(sim.mouse, 20)) {
      sim.mouseOnPathMs += dt;
      if (sim.mouseOnPathMs > 550) {
        var nearby = sim.barriers.find(function (barrier) {
          return Vec2.dist(barrier.pos, sim.mouse) < 26;
        });
        if (!nearby) sim.barriers.push(new Barrier(sim.mouse.x, sim.mouse.y));
      }
      return;
    }

    sim.mouseOnPathMs = 0;
  }

  // Aktualisiert Barrieren und entfernt inaktive Eintraege.
  function updateBarriers(sim) {
    sim.barriers.forEach(function (barrier) { barrier.update(sim.mouse); });
    sim.barriers = sim.barriers.filter(function (barrier) { return barrier.alive; });
  }

  // Aktualisiert alle Trail-Ameisen gegen aktuelle Umgebung.
  function updateTrailAnts(sim) {
    sim.ants.forEach(function (ant) {
      ant.update(sim.mouse, sim.barriers, sim.apples, sim.ants);
    });
  }

  // Steuert das Intervall, in dem Ameisen in den Overlay-Stream umgeleitet werden
  // (einzelne Ameisen laufen quer ueber die Seite und reihen sich rechts wieder ein).
  function scheduleOverlayDiversion(sim, dt) {
    sim.overlaySpawnMs -= dt;
    if (sim.overlaySpawnMs > 0) return;

    var diverted = sim.divertTrailAntToOverlay();
    sim.overlaySpawnMs = diverted
      ? (3200 + Math.random() * 5200)
      : (700 + Math.random() * 900);
  }

  // Bewegt Overlay-Ameisen frameunabhaengig mit Delta-Zeit.
  function moveOverlayAnts(sim, dt) {
    var step = dt / 16.67;
    sim.overlayAnts.forEach(function (ant) {
      ant.pos.x += ant.vx * step;
      ant.pos.y += ant.vy * step;
      ant.angle = Math.atan2(ant.vy, ant.vx);
      ant.legPhase += Math.abs(ant.vx) * 0.45 * step;
    });
  }

  // Entfernt Overlay-Ameisen ausserhalb des Sichtbereichs und fuehrt Rejoin am rechten Rand aus.
  function pruneAndRejoinOverlayAnts(sim, viewportWidth, docH, getPageEdges) {
    sim.overlayAnts = sim.overlayAnts.filter(function (ant) {
      if (ant.dead) return false;
      if (ant.pos.y < -30 || ant.pos.y > docH + 30) return false;
      if (ant.pos.x > viewportWidth + 30) return false;

      var right = getPageEdges().right;
      if (ant.pos.x >= right - 8) {
        sim.rejoinOverlayAnt(ant);
        return false;
      }

      return true;
    });
  }

  // Markiert Trail-Ameisen ausserhalb des Dokumentbereichs als beendet.
  function markOffscreenTrailAntsDone(sim, viewportWidth, docH) {
    sim.ants.forEach(function (ant) {
      if (ant.pos.x < -80 || ant.pos.x > viewportWidth + 80 || ant.pos.y < -80 || ant.pos.y > docH + 80) {
        ant.done = true;
      }
    });
  }

  // Spawnt Aepfel neu, sobald alle vorhandenen eingesammelt wurden.
  function respawnApplesIfCollected(sim) {
    if (!sim.apples.length) return;
    if (!sim.apples.every(function (apple) { return apple.collected; })) return;
    sim.apples = [];
    sim.spawnApples();
  }

  // Fuehrt einen kompletten Bewegungs-Frame der Ameisen-Simulation aus.
  function updateMovement(sim, dt, deps) {
    var Ant = deps.Ant;
    var Barrier = deps.Barrier;
    var Vec2 = deps.Vec2;
    var docHeight = deps.docHeight;
    var getPageEdges = deps.getPageEdges;

    var viewportWidth = window.innerWidth;
    var docH = docHeight();

    spawnTrailAnts(sim, dt, Ant);
    pruneCompletedTrailAnts(sim);
    detectMouseBarrier(sim, dt, Vec2, Barrier);
    updateBarriers(sim);
    updateTrailAnts(sim);

    scheduleOverlayDiversion(sim, dt);
    moveOverlayAnts(sim, dt);
    pruneAndRejoinOverlayAnts(sim, viewportWidth, docH, getPageEdges);

    markOffscreenTrailAntsDone(sim, viewportWidth, docH);
    respawnApplesIfCollected(sim);
  }

  window.AntsMovement = {
    updateMovement: updateMovement,
  };
})();
