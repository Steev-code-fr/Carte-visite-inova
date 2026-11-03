#!/usr/bin/env python3
"""Génère la carte de visite dématérialisée INOVA Sécurité.

Modifier uniquement le bloc CARTE ci-dessous, puis lancer :
    pip install segno pillow
    python3 build.py
Les fichiers sont écrits dans le dossier parent (../site/ et ../).
"""
import base64, io, json, pathlib, html
import segno
from PIL import Image

# ------------------------------------------------------------------ données
CARTE = {
    "prenom": "Stéphane",
    "nom": "Pasquier",
    "fonction": "Directeur commercial",
    "role": "Associé",
    "societe": "INOVA Sécurité",
    "mobile": "06 98 15 74 50",
    "fixe": "",                               # facultatif
    "email": "stephanepasquier@inova-securite.fr",
    "site": "https://www.inova-securite.fr",
    "linkedin": "",                           # ex. https://www.linkedin.com/in/... (vide = bouton masqué)
    "adresse": {
        "rue": "9 place de la Liberté d'Expression",
        "cp": "33610",
        "ville": "Canéjan",
        "pays": "France",
    },
    # Adresse publique de la page une fois en ligne
    "url_carte": "https://steev-code-fr.github.io/Carte-visite-inova/stephane-pasquier/",
}
# Mettre à False quand toutes les coordonnées sont réelles : retire le bandeau « Aperçu ».
APERCU = False
# --------------------------------------------------------------------------

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent
SITE = OUT / "site"
SITE.mkdir(exist_ok=True)
c = CARTE
a = c["adresse"]
slug = f"{c['prenom']}-{c['nom']}".lower().replace("é", "e").replace("è", "e")


def esc(s):  # vCard escaping
    return s.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")


def tel_uri(t):
    t = "".join(ch for ch in t if ch.isdigit() or ch == "+")
    return "+33" + t[1:] if t.startswith("0") else t


PHOTO_PROFIL = HERE / "photo-profil.jpg"   # déposer ici la photo de Stéphane (carrée de préférence)
BANDEAU = HERE / "bandeau.jpg"             # facultatif : photo de chantier pour le bandeau


def photo_carree(taille):
    """Photo de profil recadrée au carré (centrée, un peu vers le haut pour le visage)."""
    from PIL import ImageOps
    im = ImageOps.exif_transpose(Image.open(PHOTO_PROFIL)).convert("RGB")
    w, hh = im.size; cote = min(w, hh)
    x = (w - cote) // 2; y = max(0, min(hh - cote, int((hh - cote) * 0.3)))
    return im.crop((x, y, x + cote, y + cote)).resize((taille, taille), Image.LANCZOS)


def jpeg_b64(im, q=85):
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=q, optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def vcard(photo=True):
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"N;CHARSET=UTF-8:{esc(c['nom'])};{esc(c['prenom'])};;;",
        f"FN;CHARSET=UTF-8:{esc(c['prenom'])} {esc(c['nom'])}",
        f"ORG;CHARSET=UTF-8:{esc(c['societe'])}",
        f"TITLE;CHARSET=UTF-8:{esc(c['fonction'])} · {esc(c['role'])}",
        f"TEL;TYPE=CELL,VOICE:{tel_uri(c['mobile'])}",
    ]
    if c["fixe"]:
        lines.append(f"TEL;TYPE=WORK,VOICE:{tel_uri(c['fixe'])}")
    lines += [
        f"EMAIL;TYPE=INTERNET,WORK:{c['email']}",
        f"ADR;TYPE=WORK;CHARSET=UTF-8:;;{esc(a['rue'])};{esc(a['ville'])};;{esc(a['cp'])};{esc(a['pays'])}",
        f"URL;TYPE=WORK:{c['site']}",
    ]
    if photo:  # champs secondaires : seulement dans le fichier, pour garder un QR code lisible
        if c["linkedin"]:
            lines.append(f"URL;TYPE=LinkedIn:{c['linkedin']}")
        lines += ["NOTE;CHARSET=UTF-8:Sécurité incendie · Vidéosurveillance · Contrôle d'accès · Anti-intrusion · Interphonie"]
    if photo:
        if PHOTO_PROFIL.exists():
            im = photo_carree(300)
        else:
            src = Image.open(HERE / "INOVA-symbole-rond-magenta.png").convert("RGBA")
            # fond blanc derrière le rond (Samsung Contacts recadre en cercle)
            im = Image.new("RGB", src.size, "white"); im.paste(src, mask=src.split()[3])
            im = im.resize((240, 240), Image.LANCZOS)
        b64 = jpeg_b64(im, 85)
        first, rest = "PHOTO;ENCODING=b;TYPE=JPEG:" + b64[:45], b64[45:]
        lines.append(first)
        lines += [" " + rest[i:i + 74] for i in range(0, len(rest), 74)]
    lines.append("END:VCARD")
    return "\r\n".join(lines) + "\r\n"


# 1. vCard complète (avec logo) à télécharger
vcf_name = f"{slug}.vcf"
(SITE / vcf_name).write_text(vcard(True), encoding="utf-8", newline="")
(OUT / vcf_name).write_text(vcard(True), encoding="utf-8", newline="")

# 2. QR codes : contact (vCard sans photo, marche hors ligne) et lien vers la page
NUIT, MAGENTA = "#1B1030", "#E0287D"
qr_contact = segno.make(vcard(False), error="l", micro=False)
qr_lien = segno.make(c["url_carte"], error="q", micro=False)
for qr, nom in ((qr_contact, "qr-contact"), (qr_lien, "qr-lien-carte")):
    qr.save(str(OUT / f"{nom}.png"), scale=16, border=3, dark=NUIT, light="#FFFFFF")
    qr.save(str(OUT / f"{nom}.svg"), scale=10, border=3, dark=NUIT, light="#FFFFFF")
buf = io.BytesIO()
qr_lien.save(buf, kind="svg", scale=6, border=2, dark=NUIT, light="#FFFFFF", xmldecl=False, svgns=True, nl=False, omitsize=True)
qr_svg_inline = buf.getvalue().decode()

# 3. Icônes écran d'accueil (Samsung / Android)
sym = Image.open(HERE / "INOVA-symbole-rond-magenta.png").convert("RGBA")
for s in (192, 512):
    sym.resize((s, s), Image.LANCZOS).save(SITE / f"icone-{s}.png")
sym.resize((180, 180), Image.LANCZOS).save(SITE / "apple-touch-icon.png")
(SITE / "manifest.webmanifest").write_text(json.dumps({
    "name": f"{c['prenom']} {c['nom']} · INOVA Sécurité",
    "short_name": f"{c['prenom']} {c['nom'][0]}.",
    "start_url": "./", "scope": "./", "display": "standalone",
    "background_color": NUIT, "theme_color": NUIT, "lang": "fr",
    "icons": [{"src": "icone-192.png", "sizes": "192x192", "type": "image/png"},
              {"src": "icone-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}],
}, ensure_ascii=False, indent=2), encoding="utf-8")
(SITE / ".htaccess").write_text(
    "AddType text/vcard .vcf\nAddType application/manifest+json .webmanifest\n"
    "<FilesMatch \"\\.vcf$\">\n  Header set Content-Disposition \"attachment\"\n</FilesMatch>\n", encoding="utf-8")

# 4. Page HTML
logo_svg = (HERE / "INOVA-principal-negatif-transparent.svg").read_text(encoding="utf-8")
logo_svg = logo_svg.replace("<svg ", '<svg class="logo" ', 1)
h = html.escape
logo_h = (HERE / "INOVA-horizontal-negatif-transparent.svg").read_text(encoding="utf-8").replace("<svg ", '<svg class="logo-pied" ', 1)
linkedin_btn = (f'''<a class="btn" href="{html.escape(c['linkedin'])}" target="_blank" rel="noopener">
      <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="3"/><path d="M8 10v7M8 7v.01M12 17v-4a2 2 0 0 1 4 0v4M12 10v7"/></svg>
      LinkedIn</a>''' if c["linkedin"] else "")
adr_txt = f"{a['rue']}, {a['cp']} {a['ville']}"
maps = "https://www.google.com/maps/search/?api=1&query=" + "+".join(f"{a['rue']} {a['cp']} {a['ville']}".split())
if PHOTO_PROFIL.exists():
    photo_html = f'<img class="photo" src="data:image/jpeg;base64,{jpeg_b64(photo_carree(360), 82)}" alt="Photo de {h(c["prenom"])} {h(c["nom"])}" width="120" height="120">'
else:
    sym_svg = (HERE / "INOVA-symbole-rond-magenta.svg").read_text(encoding="utf-8")
    photo_html = f'<div class="photo photo-symbole" role="img" aria-label="INOVA Sécurité">{sym_svg}</div>'
if BANDEAU.exists():
    from PIL import ImageOps
    bd = ImageOps.exif_transpose(Image.open(BANDEAU)).convert("RGB"); bd.thumbnail((1000, 1000))
    bandeau_fond = f'<img class="bandeau-photo" src="data:image/jpeg;base64,{jpeg_b64(bd, 78)}" alt="">'
else:
    bandeau_fond = ""
BANDEAU_MOTIF = """<svg class="bandeau-motif" viewBox="0 0 440 190" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
  <defs>
    <linearGradient id="bd-g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2A1848"/><stop offset="1" stop-color="#140B25"/></linearGradient>
    <pattern id="bd-p" width="16" height="16" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1.1" fill="#FFFFFF" fill-opacity=".07"/></pattern>
  </defs>
  <rect width="440" height="190" fill="url(#bd-g)"/>
  <g fill="none" stroke="#E0287D">
    <circle cx="392" cy="34" r="46" stroke-width="10" stroke-opacity=".9"/>
    <circle cx="392" cy="34" r="84" stroke-width="2" stroke-opacity=".45"/>
    <circle cx="392" cy="34" r="122" stroke-width="1.5" stroke-opacity=".25"/>
    <circle cx="392" cy="34" r="160" stroke-width="1" stroke-opacity=".14"/>
  </g>
  <path d="M0 150 L120 112 L440 190 L0 190Z" fill="#E0287D" fill-opacity=".10"/>
</svg>"""
apercu = ('<p class="apercu" role="note">Aperçu : téléphone, LinkedIn et adresse sont encore fictifs.</p>' if APERCU else "")

page_body = f"""
<main class="carte">
  {apercu}
  <header class="bandeau">
    {BANDEAU_MOTIF}
    {bandeau_fond}
    {logo_svg}
  </header>

  <section class="identite">
    {photo_html}
    <h1>{h(c['prenom'])} {h(c['nom'])}</h1>
    <p class="fonction">{h(c['fonction'])}</p>
    <p class="role">{h(c['role'])}</p>
  </section>

  <nav class="actions{' actions-3' if not c['linkedin'] else ''}" aria-label="Contacter {h(c['prenom'])}">
    <a class="btn" href="tel:{tel_uri(c['mobile'])}">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2"/></svg>
      Appeler</a>
    <a class="btn" href="mailto:{h(c['email'])}">
      <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>
      E-mail</a>
    <a class="btn" href="sms:{tel_uri(c['mobile'])}">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.4A8 8 0 1 1 21 12Z"/></svg>
      SMS</a>
    {linkedin_btn}
  </nav>

  <a class="enregistrer" href="{vcf_name}" download="{vcf_name}">
    <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10" cy="8" r="4"/><path d="M3 20a7 7 0 0 1 14 0M19 8v6M16 11h6"/></svg>
    Enregistrer le contact
  </a>

  <dl class="coord">
    <div><dt>Mobile</dt><dd><a href="tel:{tel_uri(c['mobile'])}">{h(c['mobile'])}</a></dd></div>
    {f'<div><dt>Bureau</dt><dd><a href="tel:{tel_uri(c["fixe"])}">{h(c["fixe"])}</a></dd></div>' if c['fixe'] else ''}
    <div><dt>E-mail</dt><dd><a href="mailto:{h(c['email'])}">{h(c['email'])}</a></dd></div>
    <div><dt>Site</dt><dd><a href="{h(c['site'])}" target="_blank" rel="noopener">{h(c['site'].replace('https://', '').replace('http://', ''))}</a></dd></div>
    <div><dt>Adresse</dt><dd><a href="{h(maps)}" target="_blank" rel="noopener">{h(adr_txt)}</a></dd></div>
  </dl>

  <section class="metiers" aria-label="Nos métiers">
    <h2>Nos métiers</h2>
    <ul>
      <li>Sécurité incendie</li><li>Vidéosurveillance</li><li>Contrôle d'accès</li>
      <li>Anti-intrusion</li><li>Interphonie</li>
    </ul>
  </section>

  <section class="qr" aria-label="QR code de la carte">
    <div class="qr-code">{qr_svg_inline}</div>
    <p>Scannez avec l'appareil photo pour ouvrir cette carte et ajouter {h(c['prenom'])} à vos contacts.</p>
  </section>

  <button class="partager" type="button" id="partager">
    <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.6 13.5 6.8 4M15.4 6.5l-6.8 4"/></svg>
    <span id="partager-txt">Partager cette carte</span>
  </button>

  <footer class="pied">
    {logo_h}
    <p>Un seul interlocuteur pour toute la sécurité du bâtiment.</p>
  </footer>
</main>
<script>
(function () {{
  var b = document.getElementById('partager'), t = document.getElementById('partager-txt');
  var url = {json.dumps(c['url_carte'])};
  if (location.protocol.indexOf('http') === 0 && location.hostname.indexOf('claude') < 0) url = location.href.split('#')[0];
  b.addEventListener('click', function () {{
    var data = {{ title: {json.dumps(c['prenom'] + ' ' + c['nom'] + ' · INOVA Sécurité')}, url: url }};
    if (navigator.share) {{ navigator.share(data).catch(function () {{}}); return; }}
    if (navigator.clipboard) {{
      navigator.clipboard.writeText(url).then(function () {{
        t.textContent = 'Lien copié'; setTimeout(function () {{ t.textContent = 'Partager cette carte'; }}, 2200);
      }}, function () {{ t.textContent = url; }});
    }} else {{ t.textContent = url; }}
  }});
}})();
</script>
"""

css = """
:root{
  /* Carte de visite : un seul écran sombre Nuit, accents magenta (charte INOVA v1.0) */
  --nuit:#1B1030; --nuit-2:#251740; --nuit-3:#33224F; --magenta:#E0287D; --magenta-clair:#F05A9C;
  --blanc:#FFFFFF; --brume:#F7F4FA; --lavande:#B9AECB; --filet:rgba(231,225,238,.14);
  --f-titre:"Michroma","Eurostile","Arial Black",sans-serif;
  --f-texte:"Manrope","Segoe UI",Roboto,Arial,sans-serif;
  color-scheme:dark;
}
*{box-sizing:border-box}
html{background:var(--nuit)}
body{margin:0;background:var(--nuit);color:var(--brume);font:400 16px/1.5 var(--f-texte);
  padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));
  padding-block:max(20px,env(safe-area-inset-top,0px)) max(28px,env(safe-area-inset-bottom,0px));
  -webkit-text-size-adjust:100%}
a{color:inherit}
.carte{max-width:440px;margin:0 auto;display:flex;flex-direction:column;gap:22px}
.apercu{margin:0;padding:8px 12px;border:1px dashed var(--magenta);border-radius:8px;color:var(--magenta-clair);font-size:13px;text-align:center}
.bandeau{position:relative;height:190px;border-radius:20px;overflow:hidden;display:flex;align-items:flex-start;padding:26px 24px;
  background:var(--nuit-2);border:1px solid var(--filet)}
.bandeau-motif,.bandeau-photo{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;max-width:none}
.bandeau-photo{opacity:.55;mix-blend-mode:luminosity}
.logo{position:relative;width:min(200px,54%);height:auto;display:block}
.identite{display:flex;flex-direction:column;align-items:center;text-align:center;gap:4px;padding-bottom:6px;margin-top:-86px;position:relative}
.photo{width:120px;height:120px;border-radius:50%;object-fit:cover;display:grid;place-items:center;margin-bottom:14px;
  background:var(--nuit-2);border:4px solid var(--nuit);box-shadow:0 0 0 2px var(--magenta),0 10px 30px -8px rgba(0,0,0,.6)}
.photo-symbole{background:var(--magenta);overflow:hidden}
.photo-symbole svg{width:100%;height:100%;display:block}
h1{margin:0;font-weight:800;font-size:clamp(28px,8vw,34px);line-height:1.15;color:var(--blanc);text-wrap:balance;letter-spacing:-.01em}
.fonction{margin:4px 0 0;font:400 12.5px/1.6 var(--f-titre);letter-spacing:.16em;text-transform:uppercase;color:var(--magenta-clair)}
.role{margin:0;display:flex;align-items:center;gap:10px;font-weight:600;color:var(--lavande);font-size:15px}
.barres{display:inline-block;width:14px;height:14px;position:relative;flex:none}
.barres::before,.barres::after{content:"";position:absolute;left:0;right:0;height:3px;background:var(--magenta)}
.barres::before{top:0}.barres::after{bottom:0}
.actions{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.btn{display:flex;flex-direction:column;align-items:center;gap:6px;padding:14px 4px 12px;border-radius:14px;
  background:var(--nuit-2);border:1px solid var(--filet);text-decoration:none;font-weight:600;font-size:13px;color:var(--brume);
  transition:background .15s,border-color .15s}
.btn svg,.enregistrer svg,.partager svg{width:24px;height:24px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.btn svg{color:var(--magenta-clair)}
.btn:hover,.btn:focus-visible{background:var(--nuit-3);border-color:var(--magenta)}
.enregistrer{display:flex;align-items:center;justify-content:center;gap:10px;padding:16px;border-radius:14px;
  background:var(--magenta);color:var(--blanc);text-decoration:none;font-weight:800;font-size:17px;letter-spacing:.01em;
  box-shadow:0 8px 24px -10px rgba(224,40,125,.7);transition:filter .15s}
.enregistrer:hover,.enregistrer:focus-visible{filter:brightness(1.08)}
:focus-visible{outline:2px solid var(--magenta-clair);outline-offset:3px}
.coord{margin:0;display:flex;flex-direction:column;border-top:1px solid var(--filet)}
.coord>div{display:grid;grid-template-columns:78px 1fr;gap:12px;padding:12px 2px;border-bottom:1px solid var(--filet);align-items:baseline}
.coord dt{font:400 10px/1.4 var(--f-titre);letter-spacing:.14em;text-transform:uppercase;color:var(--lavande)}
.coord dd{margin:0;min-width:0;overflow-wrap:anywhere;font-weight:600;color:var(--blanc)}
.coord dd a{text-decoration:none}
.coord dd a:hover{text-decoration:underline;text-decoration-color:var(--magenta)}
.metiers h2{margin:0 0 10px;font:400 11px/1.4 var(--f-titre);letter-spacing:.18em;text-transform:uppercase;color:var(--lavande)}
.metiers ul{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:8px}
.metiers li{padding:6px 12px;border-radius:999px;border:1px solid var(--filet);font-size:13.5px;font-weight:600;color:var(--brume)}
.qr{display:flex;flex-direction:column;align-items:center;text-align:center;gap:12px;padding:14px;border-radius:16px;background:var(--nuit-2);border:1px solid var(--filet)}
.qr-code{flex:none;width:min(220px,70%);background:#fff;border-radius:10px;padding:6px;line-height:0}
.qr-code svg{width:100%;height:auto}
.qr p{margin:0;font-size:14px;color:var(--lavande);min-width:0}
.partager{display:flex;align-items:center;justify-content:center;gap:10px;padding:14px;border-radius:14px;width:100%;
  background:transparent;border:1px solid var(--magenta);color:var(--blanc);font:600 15px/1 var(--f-texte);cursor:pointer}
.partager:hover{background:var(--nuit-2)}
.actions-3{grid-template-columns:repeat(3,1fr)}
.pied{display:flex;flex-direction:column;align-items:center;gap:12px;text-align:center;font-size:13px;color:var(--lavande);margin-top:8px;padding-top:24px;border-top:1px solid var(--filet)}
.pied p{margin:0}
.logo-pied{width:min(200px,58%);height:auto;display:block}
@media (max-width:360px){.actions{grid-template-columns:repeat(2,1fr)}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
"""

fonts = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;800&family=Michroma&display=swap">'
title = f"{c['prenom']} {c['nom']} · INOVA Sécurité"
desc = f"{c['fonction']}, {c['role'].lower()} d'INOVA Sécurité : sécurité incendie, vidéosurveillance, contrôle d'accès, anti-intrusion, interphonie."

standalone = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{h(title)}</title>
<meta name="description" content="{h(desc)}">
<meta name="theme-color" content="{NUIT}">
<meta name="robots" content="noindex">
<meta property="og:title" content="{h(title)}">
<meta property="og:description" content="{h(desc)}">
<meta property="og:image" content="icone-512.png">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icone-192.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
{fonts}
<style>{css}</style>
</head>
<body>{page_body}</body>
</html>
"""
(SITE / "index.html").write_text(standalone, encoding="utf-8")

# Version aperçu (publication Artifact : pas de squelette html/head)
preview = f"""<title>Carte Stéphane Pasquier</title>
<meta name="claude:viewport-fit-sides" content="cover">
{fonts}
<style>{css}</style>
{page_body}"""
(HERE / "apercu-artifact.html").write_text(preview, encoding="utf-8")
print("OK ->", SITE)
