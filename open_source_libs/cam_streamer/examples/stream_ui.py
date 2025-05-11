# examples/stream_ui.py
"""
UNICORNER demo UI for CameraStreamer
------------------------------------
Open http://localhost:5000
→ shows the MJPEG stream
→ lets you live-tweak source / res / FPS without crashes
"""

from __future__ import annotations
from flask import Flask, Response, request, redirect, url_for
from unicorner_cam_streamer.camera_streamer import CameraStreamer

# -----------------------------------------------------------------------------
# Initialise a streamer (change the defaults here if desired)
# -----------------------------------------------------------------------------
streamer = CameraStreamer(src=0, width=640, height=480,
                          cap_fps=30, stream_fps=30)
streamer.open()

app = Flask(__name__)

# -----------------------------------------------------------------------------
# MJPEG endpoint
# -----------------------------------------------------------------------------
@app.route("/stream")
def stream():
    return Response(streamer.frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

# -----------------------------------------------------------------------------
# Main page – handles query-string updates & renders UI
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    # ── 1. apply any query-string changes (only the keys provided) ───────────
    q = request.args
    if q:
        if "src" in q:
            src_val = q.get("src")
            try:
                streamer.set_source(int(src_val))  # cam index
            except ValueError:
                streamer.set_source(src_val)       # file / URL
        if "w" in q or "h" in q:
            w = q.get("w", type=int) or streamer._req_w
            h = q.get("h", type=int) or streamer._req_h
            if w and h:
                streamer.set_resolution(w, h)
        if "cfps" in q:
            streamer.set_capture_fps(q.get("cfps", type=float))
        if "sfps" in q:
            streamer.set_stream_fps(q.get("sfps", type=float))
        # After applying, redirect to clean URL (no params)
        return redirect(url_for("index"), code=303)

    # ── 2. pull current values to pre-fill the form ─────────────────────────
    cur_w, cur_h = streamer._req_w, streamer._req_h
    cur_cfps     = streamer._req_cap_fps
    cur_sfps     = streamer._stream_fps
    cur_src      = streamer._src

    # ── 3. render page ──────────────────────────────────────────────────────
    return f"""
    <!doctype html><html><head>
      <title>UNICORNER Cam Stream</title>
      <style>
        body {{margin:0;background:#000;color:#0f0;
              display:flex;flex-direction:column;align-items:center;gap:12px;
              font-family:Arial,Helvetica,sans-serif}}
        img  {{max-width:100%;max-height:80vh;object-fit:contain}}
        form {{display:flex;flex-wrap:wrap;gap:8px;justify-content:center}}
        label{{display:flex;flex-direction:column;font-size:14px;align-items:center}}
        input{{width:70px;background:#111;border:1px solid #0f0;color:#0f0;padding:4px}}
        button{{padding:6px 16px;background:#0f0;color:#000;border:none;cursor:pointer}}
        button:hover{{background:#6f6}}
      </style>
      <script>
        /* submit via JS so empty boxes are omitted */
        function submitForm(ev) {{
            ev.preventDefault();
            const params = new URLSearchParams();
            ['src','w','h','cfps','sfps'].forEach(id => {{
                const v = document.getElementById(id).value.trim();
                if(v) params.set(id, v);
            }});
            // reload with only the filled keys
            window.location.search = params.toString();
        }}
      </script>
    </head><body>
      <img src="/stream" alt="stream">
      <form onsubmit="submitForm(event)">
        <label>src<br><input id="src"  placeholder="0/file" value="{cur_src}"></label>
        <label>w<br>  <input id="w"    type="number" min="1" value="{cur_w or ''}"></label>
        <label>h<br>  <input id="h"    type="number" min="1" value="{cur_h or ''}"></label>
        <label>cap_fps<br><input id="cfps" type="number" step="1" value="{cur_cfps or ''}"></label>
        <label>out_fps<br><input id="sfps" type="number" step="1" value="{cur_sfps or ''}"></label>
        <button>apply</button>
      </form>
      <small>UNICORNER&nbsp;Cam&nbsp;Streamer – q to quit</small>
    </body></html>
    """

# -----------------------------------------------------------------------------
# Run
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        print("▶ Open  http://localhost:5001  in your browser")
        app.run(host="0.0.0.0", port=5001)
    finally:
        streamer.release()
