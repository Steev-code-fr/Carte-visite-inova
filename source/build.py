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
            # symbole I blanc + deux traits magenta sur fond Nuit (Samsung Contacts recadre en cercle)
            im = Image.open(HERE / "INOVA-symbole-nuit-plein.png").convert("RGB").resize((300, 300), Image.LANCZOS)
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
sym = Image.open(HERE / "INOVA-symbole-nuit-plein.png").convert("RGBA")
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
logo_couleur = (HERE / "INOVA-horizontal-couleur.svg").read_text(encoding="utf-8").replace("<svg ", '<svg class="logo-verso" ', 1)
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

ICO = {
    "tel": '<path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    "sms": '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.4A8 8 0 1 1 21 12Z"/>',
    "web": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3.5 3 14.5 0 18M12 3c-3 3.5-3 14.5 0 18"/>',
    "pin": '<path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21Z"/><circle cx="12" cy="9.5" r="2.5"/>',
    "in": '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M8 10v7M8 7v.01M12 17v-4a2 2 0 0 1 4 0v4M12 10v7"/>',
    "add": '<circle cx="10" cy="8" r="4"/><path d="M3 20a7 7 0 0 1 14 0M19 8v6M16 11h6"/>',
    "share": '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.6 13.5 6.8 4M15.4 6.5l-6.8 4"/>',
    "flip": '<path d="M4 12a8 8 0 0 1 14-5.3M20 12a8 8 0 0 1-14 5.3"/><path d="M18 3v4h-4M6 21v-4h4"/>',
    "feu": '<path d="M12 3c1 4 6 5.5 6 11a6 6 0 0 1-12 0c0-3.5 2.5-4.5 2.5-8 2 1.2 3.5 3 3.5 5"/>',
    "cam": '<path d="M3 7h11l5-2v9l-5-2H3z"/><path d="M8 12v5M5 19h6"/>',
    "badge": '<rect x="5" y="3" width="14" height="18" rx="2"/><circle cx="12" cy="10" r="2.5"/><path d="M8.5 17a3.5 3.5 0 0 1 7 0"/>',
    "bouclier": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
    "interphone": '<rect x="6" y="3" width="12" height="18" rx="2"/><circle cx="12" cy="8.5" r="2"/><path d="M9.5 14h5M9.5 17h5"/>',
}
def ico(n):
    return f'<svg class="ico" viewBox="0 0 24 24" aria-hidden="true">{ICO[n]}</svg>'

METIERS = [("feu", "Sécurité incendie"), ("cam", "Vidéosurveillance"), ("badge", "Contrôle d'accès"),
           ("bouclier", "Anti-intrusion"), ("interphone", "Interphonie")]
site_txt = c['site'].replace('https://', '').replace('http://', '')
metiers_recto = "".join(f'<span title="{h(m)}">{ico(i)}</span>' for i, m in METIERS)
metiers_html = "".join(f'<li>{ico(i)}<span>{h(m)}</span></li>' for i, m in METIERS)
linkedin_li = (f'<li><a href="{h(c["linkedin"])}" target="_blank" rel="noopener">{ico("in")}<span><small>LinkedIn</small>Voir le profil</span></a></li>' if c["linkedin"] else "")
fixe_li = (f'<li><a href="tel:{tel_uri(c["fixe"])}">{ico("tel")}<span><small>Bureau</small>{h(c["fixe"])}</span></a></li>' if c["fixe"] else "")

HALO = """<svg class="halo" viewBox="0 0 600 600" aria-hidden="true">
  <defs><radialGradient id="halo-g"><stop offset="0" stop-color="#E0287D" stop-opacity=".38"/><stop offset=".45" stop-color="#E0287D" stop-opacity=".10"/><stop offset="1" stop-color="#E0287D" stop-opacity="0"/></radialGradient></defs>
  <circle cx="300" cy="300" r="300" fill="url(#halo-g)"/>
  <g fill="none" stroke="#E0287D">
    <circle class="h1" cx="300" cy="300" r="150" stroke-width="2" stroke-opacity=".55" stroke-dasharray="4 14"/>
    <circle class="h2" cx="300" cy="300" r="205" stroke-width="1.5" stroke-opacity=".35" stroke-dasharray="120 40 8 40"/>
    <circle class="h3" cx="300" cy="300" r="262" stroke-width="1" stroke-opacity=".22"/>
    <circle class="h4" cx="300" cy="300" r="292" stroke-width="10" stroke-opacity=".10" stroke-dasharray="60 400"/>
  </g>
</svg>"""

page_body = f"""
<div class="page">
  {apercu}
  <section class="hero" id="scene" aria-label="Carte de visite de {h(c['prenom'])} {h(c['nom'])}">
    {HALO}
    <div class="entree">
      <div class="carte3d" id="carte3d" tabindex="0" role="button" aria-pressed="false" aria-label="Retourner la carte de visite">
        <span class="tranche t1" aria-hidden="true"></span><span class="tranche t2" aria-hidden="true"></span><span class="tranche t3" aria-hidden="true"></span>
        <div class="face recto">
          <div class="recto-haut">{logo_svg}</div>
          <div class="recto-id">
            <h1>{h(c['prenom'])}<br>{h(c['nom'])}</h1>
            <p class="fonction">{h(c['fonction'])}</p>
            <p class="role">{h(c['role'])}</p>
          </div>
          <p class="recto-metiers" aria-label="Sécurité incendie, vidéosurveillance, contrôle d'accès, anti-intrusion, interphonie">{metiers_recto}</p>
          <span class="angle" aria-hidden="true"></span>
          <span class="reflet" aria-hidden="true"></span><span class="balayage" aria-hidden="true"></span>
        </div>
        <div class="face verso">
          {logo_couleur}
          <div class="verso-qr">{qr_svg_inline}</div>
          <p class="verso-scan">Scannez pour m'enregistrer</p>
          <ul class="verso-infos">
            <li>{h(c['mobile'])}</li>
            <li>{h(c['email'])}</li>
            <li>{h(site_txt)}</li>
            <li>{h(a['rue'])}, {h(a['cp'])} {h(a['ville'])}</li>
          </ul>
          <span class="reflet" aria-hidden="true"></span><span class="balayage" aria-hidden="true"></span>
        </div>
      </div>
    </div>
    <div class="ombre" aria-hidden="true"></div>
    <p class="astuce">{ico("flip")}<span>Touchez la carte pour la retourner</span></p>
  </section>

  <div class="contenu">
    <ul class="coord">
      <li><a href="tel:{tel_uri(c['mobile'])}">{ico("tel")}<span><small>Mobile</small>{h(c['mobile'])}</span></a></li>
      {fixe_li}
      <li><a href="mailto:{h(c['email'])}">{ico("mail")}<span><small>E-mail</small>{h(c['email'])}</span></a></li>
      <li><a href="sms:{tel_uri(c['mobile'])}">{ico("sms")}<span><small>SMS</small>Envoyer un message</span></a></li>
      <li><a href="{h(c['site'])}" target="_blank" rel="noopener">{ico("web")}<span><small>Site</small>{h(site_txt)}</span></a></li>
      <li><a href="{h(maps)}" target="_blank" rel="noopener">{ico("pin")}<span><small>Adresse</small>{h(a['rue'])}<br>{h(a['cp'])} {h(a['ville'])}</span></a></li>
      {linkedin_li}
    </ul>

    <section class="metiers" aria-labelledby="t-metiers">
      <h2 id="t-metiers"><span class="double" aria-hidden="true"></span>Nos métiers</h2>
      <ul>{metiers_html}</ul>
    </section>

    <button class="partager" type="button" id="partager">{ico("share")}<span id="partager-txt">Partager cette carte</span></button>

    <footer class="pied">
      {logo_h}
      <p>Un seul interlocuteur pour toute la sécurité du bâtiment.</p>
    </footer>
  </div>
</div>

<nav class="barre" aria-label="Contacter {h(c['prenom'])}">
  <a class="b-sec" href="tel:{tel_uri(c['mobile'])}">{ico("tel")}<span>Appeler</span></a>
  <a class="b-sec" href="mailto:{h(c['email'])}">{ico("mail")}<span>E-mail</span></a>
  <a class="b-pri" href="{vcf_name}" download="{vcf_name}">{ico("add")}<span>Enregistrer</span></a>
</nav>
<script>
(function () {{
  var scene = document.getElementById('scene'), carte = document.getElementById('carte3d');
  var calme = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var rx = 0, ry = 0, flip = 0, start = null, bouge = false, gyro = false, main = false, repos = 0;
  function rendre() {{
    carte.style.setProperty('--rx', rx.toFixed(2) + 'deg');
    carte.style.setProperty('--ry', (ry + flip).toFixed(2) + 'deg');
    carte.style.setProperty('--mx', (30 + ry * 3).toFixed(1) + '%');
    carte.style.setProperty('--my', (20 - rx * 3).toFixed(1) + '%');
    carte.style.setProperty('--bx', (50 + ry * 6).toFixed(1) + '%');
    scene.style.setProperty('--ox', (-ry * 1.2).toFixed(1) + 'px');
    scene.style.setProperty('--hx', (ry * -0.8).toFixed(1) + 'px');
    scene.style.setProperty('--hy', (rx * 0.8).toFixed(1) + 'px');
  }}
  function retourner() {{
    flip = flip ? 0 : 180; carte.setAttribute('aria-pressed', flip ? 'true' : 'false');
    carte.classList.add('anime'); repos = performance.now() + 900; rendre();
  }}
  carte.addEventListener('keydown', function (e) {{ if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); retourner(); }} }});
  scene.addEventListener('pointerdown', function (e) {{ start = [e.clientX, e.clientY]; bouge = false; }});
  scene.addEventListener('pointermove', function (e) {{
    if (calme || gyro) return;
    var r = carte.getBoundingClientRect();
    var x = (e.clientX - r.left) / r.width - .5, y = (e.clientY - r.top) / r.height - .5;
    if (start && Math.hypot(e.clientX - start[0], e.clientY - start[1]) > 8) bouge = true;
    if (e.pointerType === 'mouse' || start) {{
      main = true; carte.classList.remove('anime');
      ry = Math.max(-22, Math.min(22, x * 40)); rx = Math.max(-16, Math.min(16, -y * 28)); rendre();
    }}
  }});
  function relacher() {{ start = null; main = false; repos = performance.now() + 1200; if (!gyro) {{ carte.classList.add('anime'); rx = 0; ry = 0; rendre(); }} }}
  scene.addEventListener('pointerleave', relacher);
  scene.addEventListener('pointercancel', relacher);
  carte.addEventListener('click', function () {{ if (!bouge) retourner(); bouge = false; start = null; }});
  function orientation(e) {{
    if (e.gamma == null || main) return;
    gyro = true; carte.classList.remove('anime');
    ry = Math.max(-22, Math.min(22, e.gamma * 0.7));
    rx = Math.max(-16, Math.min(16, -(e.beta - 50) * 0.45));
    rendre();
  }}
  if (!calme && window.DeviceOrientationEvent) {{
    if (typeof DeviceOrientationEvent.requestPermission === 'function') {{
      carte.addEventListener('click', function demande() {{
        DeviceOrientationEvent.requestPermission().then(function (r) {{ if (r === 'granted') addEventListener('deviceorientation', orientation); }}).catch(function () {{}});
        carte.removeEventListener('click', demande);
      }});
    }} else {{ addEventListener('deviceorientation', orientation); }}
  }}
  /* balancement doux quand personne ne touche la carte */
  var t0 = performance.now() + 1400;
  function flotter(t) {{
    if (!calme && !gyro && !main && t > t0 && t > repos) {{
      var s = (t - t0) / 1000;
      carte.classList.remove('anime');
      ry = Math.sin(s * 0.9) * 9; rx = Math.sin(s * 0.6 + 1) * 5; rendre();
    }}
    requestAnimationFrame(flotter);
  }}
  requestAnimationFrame(flotter);
  rendre();
}})();
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
  /* Une carte de visite qui flotte dans le halo du « O » : Nuit en aplat, magenta en accent (charte INOVA v1.0) */
  --nuit:#1B1030; --nuit-2:#251740; --nuit-3:#33224F; --magenta:#E0287D; --magenta-clair:#F05A9C; --magenta-fonce:#C41E68;
  --blanc:#FFFFFF; --brume:#F7F4FA; --lavande:#B9AECB; --prune:#6E6578; --filet:rgba(231,225,238,.14);
  --f-titre:"Michroma","Eurostile","Arial Black",sans-serif;
  --f-texte:"Manrope","Segoe UI",Roboto,Arial,sans-serif;
  --barre-h:76px;
  color-scheme:dark;
}
*{box-sizing:border-box}
html{background:var(--nuit);overflow-x:hidden}
body{margin:0;background:var(--nuit);color:var(--brume);font:400 16px/1.5 var(--f-texte);overflow-x:hidden;-webkit-text-size-adjust:100%;
  -webkit-tap-highlight-color:transparent}
a{color:inherit}
.ico{width:22px;height:22px;flex:none;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
:focus-visible{outline:2px solid var(--magenta-clair);outline-offset:3px}
.page{max-width:1080px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));
  padding-block:max(12px,env(safe-area-inset-top,0px)) calc(var(--barre-h) + 28px + env(safe-area-inset-bottom,0px))}
.apercu{margin:0 0 8px;padding:8px 12px;border:1px dashed var(--magenta);border-radius:8px;color:var(--magenta-clair);font-size:13px;text-align:center}

/* --- Héros : la carte occupe l'écran --- */
.hero{--ox:0px;--hx:0px;--hy:0px;position:relative;perspective:1300px;min-height:calc(100svh - var(--barre-h) - 24px);
  display:flex;flex-direction:column;align-items:center;justify-content:center;padding-block:12px 8px;touch-action:pan-y;-webkit-user-select:none;user-select:none;overflow-x:clip}
.halo{position:absolute;left:50%;top:46%;width:min(170vw,980px);height:auto;max-width:none;transform:translate(calc(-50% + var(--hx)),calc(-50% + var(--hy)));pointer-events:none;
  animation:halo-in 1.6s ease-out both}
.halo .h1{transform-origin:300px 300px;animation:tourne 38s linear infinite}
.halo .h2{transform-origin:300px 300px;animation:tourne 60s linear infinite reverse}
.halo .h4{transform-origin:300px 300px;animation:tourne 16s linear infinite}
@keyframes tourne{to{transform:rotate(360deg)}}
@keyframes halo-in{from{opacity:0;transform:translate(calc(-50% + var(--hx)),calc(-50% + var(--hy))) scale(.6)}to{opacity:1}}
.entree{position:relative;width:min(84vw,380px,calc((100svh - var(--barre-h) - 150px) * 55 / 85));animation:entree 1.4s cubic-bezier(.2,.75,.25,1) both}
@keyframes entree{from{transform:translateY(40px) rotateX(24deg) rotateY(-220deg) scale(.8);opacity:0}30%{opacity:1}to{transform:none;opacity:1}}
.carte3d{--rx:0deg;--ry:0deg;--mx:30%;--my:20%;--bx:50%;position:relative;width:100%;aspect-ratio:55/85;transform-style:preserve-3d;
  transform:rotateX(var(--rx)) rotateY(var(--ry));cursor:pointer;border-radius:22px;outline-offset:8px}
.carte3d.anime{transition:transform .8s cubic-bezier(.2,.75,.25,1)}
.tranche{position:absolute;inset:0;border-radius:22px;background:var(--magenta-fonce)}
.t1{transform:translateZ(-1.5px)}.t2{transform:translateZ(0)}.t3{transform:translateZ(1.5px)}
.face{position:absolute;inset:0;border-radius:22px;overflow:hidden;backface-visibility:hidden;-webkit-backface-visibility:hidden;
  box-shadow:0 40px 70px -30px rgba(0,0,0,.9)}
.recto{transform:translateZ(3px);background:var(--nuit);border:1px solid rgba(224,40,125,.45);display:flex;flex-direction:column;padding:10% 9% 9%}
.verso{transform:rotateY(180deg) translateZ(3px);background:var(--brume);color:var(--nuit);display:flex;flex-direction:column;align-items:center;padding:9% 9% 8%;text-align:center}
.recto-haut{display:flex;justify-content:space-between;align-items:flex-start}
.recto .logo{width:62%;height:auto;display:block}
.double{display:inline-block;width:28px;height:16px;flex:none;position:relative}
.double::before,.double::after{content:"";position:absolute;left:0;right:0;height:4px;background:var(--magenta);border-radius:1px}
.double::before{top:0}.double::after{bottom:0}
.recto-id{margin-top:auto;display:flex;flex-direction:column;gap:4px}
.recto h1{margin:0;font-weight:800;font-size:clamp(30px,10.5vw,44px);line-height:1.02;letter-spacing:-.02em;color:var(--blanc)}
.recto .fonction{margin:10px 0 0;font:400 clamp(9px,2.7vw,11.5px)/1.5 var(--f-titre);letter-spacing:.16em;text-transform:uppercase;color:var(--magenta-clair)}
.recto .role{margin:0;font-weight:600;font-size:clamp(13px,3.8vw,16px);color:var(--lavande)}
.recto-metiers{margin:9% 0 0;padding-top:7%;border-top:1px solid var(--filet);display:flex;gap:7%;color:var(--lavande)}
.recto-metiers .ico{width:clamp(18px,5.6vw,24px);height:clamp(18px,5.6vw,24px);stroke-width:1.6}
.angle{position:absolute;right:-16%;bottom:-11%;width:48%;aspect-ratio:1;border-radius:50%;border:12px solid var(--magenta);pointer-events:none}
.recto-id,.recto-metiers{position:relative;z-index:1}
.recto-metiers{margin-right:30%}
.logo-verso{width:72%;height:auto;display:block}
.verso-qr{margin-top:9%;width:74%;background:#fff;border-radius:14px;padding:4%;line-height:0;box-shadow:0 0 0 1px #E7E1EE,0 12px 24px -16px rgba(27,16,48,.5)}
.verso-qr svg{width:100%;height:auto}
.verso-scan{margin:5% 0 0;font:400 clamp(7.5px,2.2vw,9.5px)/1.4 var(--f-titre);letter-spacing:.14em;text-transform:uppercase;color:var(--magenta-fonce)}
.verso-infos{list-style:none;margin:auto 0 0;padding:0;display:grid;gap:2px;font-size:clamp(10px,3vw,13px);font-weight:600;line-height:1.35;overflow-wrap:anywhere}
.verso-infos li:first-child{font-weight:800;font-size:1.15em}
.reflet{position:absolute;inset:0;pointer-events:none;border-radius:inherit;
  background:radial-gradient(circle at var(--mx) var(--my),rgba(255,255,255,.13),rgba(255,255,255,0) 55%)}
.balayage{position:absolute;inset:-20%;pointer-events:none;
  background:linear-gradient(105deg,transparent 42%,rgba(255,255,255,.10) 50%,transparent 58%);background-size:250% 100%;background-position:var(--bx) 0;
  mix-blend-mode:screen}
.verso .balayage{mix-blend-mode:normal;opacity:.6}
.ombre{width:min(70vw,320px);height:22px;margin-top:22px;border-radius:50%;background:radial-gradient(closest-side,rgba(0,0,0,.6),transparent);
  transform:translateX(var(--ox));filter:blur(3px);animation:fondu .8s .6s both}
.astuce{display:flex;align-items:center;gap:8px;margin:12px 0 0;font-size:13px;font-weight:600;color:var(--lavande);animation:fondu .8s 1.2s both}
.astuce .ico{width:18px;height:18px;color:var(--magenta-clair);animation:tourne 3.5s ease-in-out infinite}
@keyframes fondu{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}

/* --- Contenu --- */
.contenu{display:flex;flex-direction:column;gap:26px;max-width:520px;margin:0 auto;width:100%}
.coord{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:1fr 1fr;gap:10px}
.coord li{min-width:0}
.coord li:nth-child(2),.coord li:nth-child(5){grid-column:1/-1}
.coord a{height:100%;display:flex;align-items:flex-start;gap:12px;padding:14px;border-radius:16px;background:var(--nuit-2);border:1px solid var(--filet);
  text-decoration:none;font-weight:700;font-size:14.5px;line-height:1.35;color:var(--blanc);transition:border-color .2s,background .2s,transform .2s}
.coord a:hover,.coord a:focus-visible{border-color:var(--magenta);background:var(--nuit-3);transform:translateY(-2px)}
.coord .ico{color:var(--magenta-clair);margin-top:2px}
.coord span{min-width:0;overflow-wrap:anywhere;display:flex;flex-direction:column}
.coord small{font:400 9.5px/1.6 var(--f-titre);letter-spacing:.14em;text-transform:uppercase;color:var(--lavande)}
.metiers h2{display:flex;align-items:center;gap:12px;margin:0 0 14px;font:400 12px/1.4 var(--f-titre);letter-spacing:.2em;text-transform:uppercase;color:var(--blanc)}
.metiers h2 .double{width:20px;height:12px}
.metiers h2 .double::before,.metiers h2 .double::after{height:3px}
.metiers ul{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(96px,1fr));gap:10px}
.metiers li{display:flex;flex-direction:column;align-items:center;gap:8px;padding:16px 8px;border-radius:16px;border:1px solid var(--filet);text-align:center;font-size:12.5px;font-weight:700;line-height:1.25}
.metiers li .ico{width:28px;height:28px;color:var(--magenta-clair)}
.partager{display:flex;align-items:center;justify-content:center;gap:10px;padding:15px;border-radius:16px;width:100%;
  background:transparent;border:1px solid var(--magenta);color:var(--blanc);font:700 15px/1 var(--f-texte);cursor:pointer;transition:background .2s}
.partager:hover{background:var(--nuit-2)}
.pied{display:flex;flex-direction:column;align-items:center;gap:12px;text-align:center;font-size:13px;color:var(--lavande);padding-top:24px;border-top:1px solid var(--filet)}
.pied p{margin:0}
.logo-pied{width:min(210px,60%);height:auto;display:block}

/* --- Barre d'actions fixe --- */
.barre{position:fixed;left:0;right:0;bottom:0;z-index:20;display:grid;grid-template-columns:1fr 1fr 1.6fr;gap:8px;
  padding:10px max(12px,env(safe-area-inset-right,0px)) calc(10px + env(safe-area-inset-bottom,0px)) max(12px,env(safe-area-inset-left,0px));
  background:rgba(27,16,48,.86);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);border-top:1px solid var(--filet);animation:monte .7s 1s both}
@keyframes monte{from{transform:translateY(100%)}to{transform:none}}
.barre a{display:flex;align-items:center;justify-content:center;gap:8px;min-height:54px;border-radius:14px;text-decoration:none;font-weight:800;font-size:14.5px}
.b-sec{background:var(--nuit-2);border:1px solid var(--filet);color:var(--blanc)}
.b-sec .ico{color:var(--magenta-clair)}
.b-pri{background:var(--magenta);color:var(--blanc);box-shadow:0 10px 26px -10px rgba(224,40,125,.8)}
@media (max-width:360px){.barre a span{font-size:13px}.b-sec span{display:none}}

/* --- Grand écran : carte à gauche, informations à droite --- */
@media (min-width:900px){
  .page{display:grid;grid-template-columns:1.05fr 1fr;gap:48px;align-items:start}
  .hero{position:sticky;top:0;min-height:100svh}
  .contenu{padding-block:56px;margin:0}
  .barre{left:auto;right:max(24px,calc((100vw - 1080px) / 2 + 16px));bottom:24px;width:min(460px,42vw);border-radius:20px;border:1px solid var(--filet);padding:10px}
}
@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{animation:none!important;transition:none!important}
}
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
