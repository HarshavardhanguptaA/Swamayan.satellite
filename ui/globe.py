"""Interactive 3D-styled animated Earth globe with real land from world-atlas via d3/topojson."""


def render_earth_hero_graphic(location_name="Pune, India", coords_text='18° 31\' 25.4" N<br>73° 51\' 22.1" E', window_metric="MULTI-SENSOR"):
    # Palette constants (mirrors :root in styles.py)
    TEAL = "#0B6E6E"
    TEAL_DARK = "#095858"
    AQUA = "#5CC8C0"
    S1_COLOR = "#182322"
    MODIS_COLOR = "#5CC8C0"
    TEXT_MAIN = "#0A1F2C"
    TEXT_MUTED = "#52677A"
    TEXT_SUBTLE = "#7A8DA0"
    BORDER = "#DCE6E8"

    # Determine study area coordinates and short name
    study_lon, study_lat = 73.8567, 18.5204  # default Pune
    loc_l = (location_name or "").lower()
    if "bengaluru" in loc_l or "bangalore" in loc_l:
        study_lon, study_lat = 77.5946, 12.9716
    elif "delhi" in loc_l:
        study_lon, study_lat = 77.2090, 28.6139
    elif "amazon" in loc_l or "brazil" in loc_l:
        study_lon, study_lat = -60.0, -3.1
    study_short = location_name.split(",")[0].strip() if location_name else "Study area"

    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Inter:wght@400;500;600;700&display=swap');
  * {{ box-sizing:border-box; margin:0; padding:0; border-radius:0px !important; }}
  body {{
    background:transparent;
    font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
    overflow:hidden; width:100%; height:100%;
    display:flex; align-items:center; justify-content:center;
    -webkit-font-smoothing:antialiased;
  }}
  .scene-container {{
    position:relative; width:100%; max-width:600px; height:480px;
    display:flex; align-items:center; justify-content:center;
  }}

  /* Study-area tag (top left) */
  .study-tag {{
    position:absolute; top:14px; left:18px;
    display:flex; align-items:center; gap:8px;
    font-family:'Inter',sans-serif; font-size:11px; font-weight:600;
    letter-spacing:0.04em; color:{TEAL};
    background:rgba(244,248,248,0.97);
    border:1px solid rgba(11,110,110,0.28);
    padding:5px 12px; backdrop-filter:blur(8px); z-index:20;
  }}
  .study-dot {{
    width:6px; height:6px; background:{TEAL}; flex-shrink:0;
  }}

  /* Globe wrapper */
  .globe-wrapper {{
    position:relative; width:300px; height:300px;
    display:flex; align-items:center; justify-content:center;
  }}

  /* Pale atmosphere glow */
  .atmosphere {{
    position:absolute; width:310px; height:310px;
    border-radius:50% !important;
    box-shadow:0 0 24px rgba(11,110,110,0.08),0 0 0 1px rgba(11,110,110,0.16);
    pointer-events:none;
  }}

  /* Pale sphere shell */
  .globe-sphere {{
    position:relative; width:290px; height:290px;
    border-radius:50% !important;
    background:radial-gradient(circle at 32% 30%,#ffffff 0%,#f4fbfb 45%,#e6f5f3 85%,#d5efec 100%);
    box-shadow:
      inset -14px -14px 28px rgba(10,31,44,0.04),
      inset 10px 10px 20px rgba(255,255,255,0.7),
      0 16px 36px -8px rgba(11,110,110,0.12);
    overflow:hidden;
  }}
  #globeCanvas {{
    width:100%; height:100%; border-radius:50% !important;
    display:block;
  }}

  /* Single slow orbit ring */
  .orbit-ring {{
    position:absolute; border-radius:50% !important; pointer-events:none;
    width:450px; height:200px;
    border:1px dashed rgba(11,110,110,0.32);
    animation:spinOrbit 70s linear infinite;
  }}
  @keyframes spinOrbit {{
    from {{ transform:rotate(-25deg); }}
    to   {{ transform:rotate(335deg); }}
  }}

  /* Sensor panels (sharp rectangular) */
  .sensor-panel {{
    position:absolute;
    display:flex; align-items:center; gap:10px;
    background:rgba(255,255,255,0.96);
    border:1px solid {BORDER};
    padding:7px 12px; cursor:pointer; z-index:25;
    box-shadow:0 4px 14px -4px rgba(0,0,0,0.06);
    transition:all 0.22s cubic-bezier(0.16,1,0.3,1);
  }}
  .sensor-panel:hover {{
    transform:translateY(-2px);
    border-color:{TEAL};
    box-shadow:0 8px 22px -4px rgba(11,110,110,0.16);
  }}
  .sensor-dot {{
    width:8px; height:8px; flex-shrink:0;
  }}
  .sensor-code {{
    font-family:'Inter',sans-serif; font-size:11px; font-weight:700;
    letter-spacing:0.05em; white-space:nowrap;
  }}
  .sensor-detail {{
    font-family:'Inter',sans-serif; font-size:10px; font-weight:500;
    color:{TEXT_SUBTLE}; max-width:0; opacity:0; overflow:hidden;
    white-space:nowrap;
    transition:max-width 0.32s ease,opacity 0.28s ease,margin-left 0.18s ease;
  }}
  .sensor-panel:hover .sensor-detail {{
    max-width:200px; opacity:1; margin-left:6px;
    padding-left:6px; border-left:1px solid {BORDER};
  }}
  .sensor-s2  {{ top:55px;  right:14px; border-color:rgba(11,110,110,0.3); }}
  .sensor-s2  .sensor-code {{ color:{TEAL}; }}
  .sensor-s2  .sensor-dot  {{ background:{TEAL}; }}
  .sensor-s1  {{ top:140px; left:16px;  border-color:rgba(24,35,34,0.25); }}
  .sensor-s1  .sensor-code {{ color:{S1_COLOR}; }}
  .sensor-s1  .sensor-dot  {{ background:{S1_COLOR}; }}
  .sensor-modis {{ bottom:95px; right:18px; border-color:rgba(92,200,192,0.45); }}
  .sensor-modis .sensor-code {{ color:{TEAL}; }}
  .sensor-modis .sensor-dot  {{ background:{MODIS_COLOR}; }}

  /* Metric badge (bottom left) */
  .metric-badge {{
    position:absolute; bottom:30px; left:24px;
    background:rgba(255,255,255,0.97);
    border:1px solid {BORDER}; padding:14px 20px; z-index:20;
    box-shadow:0 8px 24px -6px rgba(0,0,0,0.05);
  }}
  .metric-badge-label {{
    font-family:'Inter',sans-serif; font-size:10px; font-weight:700;
    letter-spacing:0.08em; text-transform:uppercase; color:{TEXT_SUBTLE}; margin-bottom:2px;
  }}
  .metric-badge-value {{
    font-family:'Inter',sans-serif; font-size:18px; font-weight:700;
    color:{TEXT_MAIN}; letter-spacing:0.04em; line-height:1.2;
  }}

  /* Coordinates (bottom right) */
  .coords-badge {{
    position:absolute; bottom:24px; right:18px;
    font-family:'Inter',sans-serif; font-size:11px; font-weight:500;
    line-height:1.5; color:{TEXT_MUTED}; text-align:right;
    background:rgba(255,255,255,0.94);
    padding:6px 12px;
    border:1px solid {BORDER}; z-index:18;
  }}

  /* Study-area marker on globe */
  .study-marker {{
    position:absolute; pointer-events:none; z-index:30;
    /* positioned by JS */
  }}

  @media (prefers-reduced-motion:reduce) {{
    .orbit-ring {{ animation:none !important; }}
  }}
  @media (max-width:520px) {{
    .sensor-panel {{ padding:5px 8px; }}
    .metric-badge {{ bottom:14px; left:10px; padding:8px 12px; }}
    .coords-badge {{ bottom:14px; right:10px; font-size:10px; }}
  }}
</style>
</head>
<body>
<div class="scene-container">

  <!-- Study area tag -->
  <div class="study-tag">
    <div class="study-dot"></div>
    <span>Study area — {location_name}</span>
  </div>

  <!-- Single slow orbit ring -->
  <div class="orbit-ring"></div>

  <!-- Globe -->
  <div class="globe-wrapper">
    <div class="atmosphere"></div>
    <div class="globe-sphere">
      <canvas id="globeCanvas" width="290" height="290"></canvas>
    </div>
  </div>

  <!-- S-2 / Optical -->
  <div class="sensor-panel sensor-s2" title="Sentinel-2: Multi-spectral Optical">
    <div class="sensor-dot"></div>
    <span class="sensor-code">S-2 / OPTICAL</span>
    <span class="sensor-detail">Sentinel-2 · Optical Reflectance</span>
  </div>

  <!-- S-1 / Radar -->
  <div class="sensor-panel sensor-s1" title="Sentinel-1: C-Band SAR">
    <div class="sensor-dot"></div>
    <span class="sensor-code">S-1 / RADAR</span>
    <span class="sensor-detail">Sentinel-1 · C-Band SAR</span>
  </div>

  <!-- MODIS / Thermal -->
  <div class="sensor-panel sensor-modis" title="MODIS: Land Surface Temperature">
    <div class="sensor-dot"></div>
    <span class="sensor-code">MODIS / THERMAL</span>
    <span class="sensor-detail">MODIS · Land Surface Temp</span>
  </div>

  <!-- Metric badge -->
  <div class="metric-badge">
    <div class="metric-badge-label">OBSERVATION SUITE</div>
    <div class="metric-badge-value">{window_metric}</div>
  </div>

  <!-- Coordinates -->
  <div class="coords-badge">{coords_text}</div>

</div>

<!-- Load d3 and topojson, then draw globe with real land -->
<script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"
        crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/topojson-client@3/dist/topojson-client.min.js"
        crossorigin="anonymous"></script>
<script>
(function () {{
  const canvas = document.getElementById('globeCanvas');
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height, R = W / 2;

  // Fallback if D3 fails to load from CDN
  if (typeof d3 === 'undefined') {{
    ctx.clearRect(0, 0, W, H);
    ctx.beginPath();
    ctx.arc(R, R, R - 1, 0, Math.PI * 2);
    ctx.fillStyle = '#f4fbfb';
    ctx.fill();
    ctx.strokeStyle = 'rgba(11, 110, 110, 0.28)';
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.strokeStyle = 'rgba(11, 110, 110, 0.12)';
    ctx.lineWidth = 0.6;
    for (let y = R * 0.35; y < H; y += R * 0.35) {{
      ctx.beginPath();
      ctx.ellipse(R, y, R * 0.85, R * 0.22, 0, 0, Math.PI * 2);
      ctx.stroke();
    }}
    return;
  }}

  // Palette
  const TEAL = '{TEAL}';
  const OCEAN_LIGHT = '#f4fbfb';
  const OCEAN_DARK  = '#e2f4f2';
  const LAND_FILL   = 'rgba(11,110,110,0.12)';
  const LAND_STROKE = 'rgba(11,110,110,0.55)';
  const GRID_COLOR  = 'rgba(11,110,110,0.12)';

  let rotation = 0;
  let landFeatures = null;
  let animating = true;

  const prefersReduced = window.matchMedia('(prefers-reduced-motion:reduce)').matches;

  // Projection factory (re-created each frame with updated rotation)
  function makeProjection(rot) {{
    return d3.geoOrthographic()
      .scale(R - 2)
      .translate([R, R])
      .rotate([rot, -20, 0])
      .clipAngle(90);
  }}

  function drawFrame() {{
    ctx.clearRect(0, 0, W, H);
    ctx.save();
    // Clip to circle
    ctx.beginPath();
    ctx.arc(R, R, R - 1, 0, Math.PI * 2);
    ctx.clip();

    const proj = makeProjection(rotation);
    const path = d3.geoPath(proj, ctx);

    // Ocean fill (pale sphere: very light teal / white fill)
    const oceanGrad = ctx.createRadialGradient(R * 0.72, R * 0.72, R * 0.08, R, R, R);
    oceanGrad.addColorStop(0, '#ffffff');
    oceanGrad.addColorStop(0.5, OCEAN_LIGHT);
    oceanGrad.addColorStop(1, OCEAN_DARK);
    ctx.fillStyle = oceanGrad;
    ctx.fillRect(0, 0, W, H);

    // Graticule (always drawn even without land)
    ctx.strokeStyle = GRID_COLOR;
    ctx.lineWidth = 0.6;
    ctx.beginPath();
    path(d3.geoGraticule()());
    ctx.stroke();

    // Sphere outline
    ctx.strokeStyle = 'rgba(11,110,110,0.25)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    path({{ type:'Sphere' }});
    ctx.stroke();

    // Land masses (if loaded from world-atlas)
    if (landFeatures) {{
      ctx.fillStyle = LAND_FILL;
      ctx.strokeStyle = LAND_STROKE;
      ctx.lineWidth = 0.75;
      ctx.beginPath();
      path(landFeatures);
      ctx.fill();
      ctx.stroke();
    }}

    // Mark study-area location if visible on front hemisphere
    try {{
      const centerCoord = proj.invert([R, R]);
      const studyPt = [{study_lon}, {study_lat}];
      if (centerCoord && d3.geoDistance(centerCoord, studyPt) < Math.PI / 2) {{
        const pt = proj(studyPt);
        if (pt && !isNaN(pt[0])) {{
          ctx.beginPath();
          ctx.arc(pt[0], pt[1], 6.5, 0, Math.PI * 2);
          ctx.strokeStyle = TEAL;
          ctx.lineWidth = 1.2;
          ctx.stroke();

          ctx.beginPath();
          ctx.arc(pt[0], pt[1], 2.5, 0, Math.PI * 2);
          ctx.fillStyle = TEAL;
          ctx.fill();

          ctx.font = '600 10px Inter, -apple-system, sans-serif';
          ctx.fillStyle = '{TEXT_MAIN}';
          ctx.fillText('{study_short}', pt[0] + 9, pt[1] + 3);
        }}
      }}
    }} catch (e) {{}}

    // Edge vignette
    const edge = ctx.createRadialGradient(R, R, R * 0.62, R, R, R);
    edge.addColorStop(0, 'rgba(0,0,0,0)');
    edge.addColorStop(0.88, 'rgba(10,31,44,0.03)');
    edge.addColorStop(1, 'rgba(10,31,44,0.10)');
    ctx.fillStyle = edge;
    ctx.fillRect(0, 0, W, H);

    ctx.restore();

    if (!prefersReduced && animating) {{
      rotation += 0.15;
      requestAnimationFrame(drawFrame);
    }}
  }}

  // Start drawing immediately (shows graticule even if land hasn't loaded yet)
  drawFrame();

  // Fetch real land from world-atlas via CDN
  try {{
    fetch('https://cdn.jsdelivr.net/npm/world-atlas@2/land-110m.json')
      .then(r => r.json())
      .then(world => {{
        if (world && world.objects && world.objects.land && typeof topojson !== 'undefined') {{
          landFeatures = topojson.feature(world, world.objects.land);
        }}
      }})
      .catch(() => {{
        // CDN failed — graceful fallback, graticule already rendering, no JS error
      }});
  }} catch (e) {{}}
}})();
</script>
</body>
</html>
"""
    return html_content

