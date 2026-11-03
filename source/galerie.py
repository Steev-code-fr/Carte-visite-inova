#!/usr/bin/env python3
"""Génère galerie.html (image téléphone 1080x2340) ; à capturer avec Playwright (voir LISEZMOI)."""
import io, pathlib, segno, importlib.util
HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("b", HERE / "build.py"); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
c = b.CARTE
buf = io.BytesIO()
segno.make(c["url_carte"], error="q").save(buf, kind="svg", scale=8, border=3, dark="#1B1030", light="#FFFFFF", xmldecl=False, svgns=True, nl=False, omitsize=True)
qr = buf.getvalue().decode()
logo = (HERE / "INOVA-principal-negatif-transparent.svg").read_text(encoding="utf-8")
sym = (HERE / "INOVA-symbole-rond-magenta.svg").read_text(encoding="utf-8")
html = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;800&family=Michroma&display=swap">
<style>
*{{box-sizing:border-box}}html,body{{margin:0;width:360px;height:780px;overflow:hidden}}
body{{background:#1B1030;color:#F7F4FA;font-family:Manrope,sans-serif;position:relative}}
.motif{{position:absolute;inset:0;width:100%;height:100%}}
.in{{position:relative;height:100%;display:flex;flex-direction:column;align-items:center;padding:64px 28px 40px}}
.logo svg{{width:230px;height:auto;display:block}}
.sym{{display:none}}
.sym svg{{width:100%;height:100%;display:block}}
h1{{margin:44px 0 0;font-weight:800;font-size:27px;color:#fff}}
.f{{margin:6px 0 0;font:400 10.5px/1.6 Michroma,sans-serif;letter-spacing:.16em;text-transform:uppercase;color:#F05A9C}}
.r{{margin:2px 0 0;font-weight:600;font-size:13px;color:#B9AECB}}
.qr{{margin-top:30px;width:236px;background:#fff;border-radius:18px;padding:8px;line-height:0;box-shadow:0 18px 40px -16px rgba(224,40,125,.6)}}
.qr svg{{width:100%;height:auto}}
.cap{{margin:16px 0 0;font-weight:800;font-size:15px;color:#fff;text-align:center}}
.sub{{margin:4px 0 0;font-size:12px;color:#B9AECB;text-align:center}}
.co{{margin-top:auto;width:100%;border-top:1px solid rgba(231,225,238,.14);padding-top:16px;display:grid;gap:6px;font-size:12.5px;font-weight:600;text-align:center;color:#F7F4FA}}
</style></head><body>
<div class="in">
<div class="logo">{logo}</div>
<div class="sym">{sym}</div>
<h1>{c['prenom']} {c['nom']}</h1>
<p class="f">{c['fonction']}</p><p class="r">{c['role']}</p>
<div class="qr">{qr}</div>
<p class="cap">Scannez pour ouvrir ma carte</p>
<p class="sub">et m'ajouter à vos contacts</p>
<div class="co"><span>{c['mobile']}</span><span>{c['email']}</span><span>{c['site'].replace('https://','')}</span></div>
</div></body></html>"""
(HERE / "galerie.html").write_text(html, encoding="utf-8")
print("ok")
