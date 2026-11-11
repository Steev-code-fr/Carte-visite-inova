#!/usr/bin/env python3
"""Génère les signatures mail INOVA Sécurité (Outlook / Microsoft 365).

Modifier la liste PERSONNES puis lancer :  python3 source/signatures.py
Sorties dans signatures/ : <nom>.htm (signature HTML), <nom>.txt (mobile),
logo-inova-signature.png et index.html (page « Copier la signature »).
"""
from pathlib import Path
from html import escape
from PIL import Image

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "signatures"
URL_BASE = "https://steev-code-fr.github.io/Carte-visite-inova"
LOGO_URL = f"{URL_BASE}/signatures/logo-inova-signature.png"
KIT_LOGO = RACINE / "source" / "INOVA-principal-couleur.png"

SOCIETE = {
    "nom": "INOVA Sécurité",
    "adresse": "9 place de la Liberté d'Expression · 33610 Canéjan",
    "site": "www.inova-securite.fr",
    "site_url": "https://www.inova-securite.fr",
    "metiers": "Sécurité incendie · Vidéosurveillance · Contrôle d'accès · Anti-intrusion · Interphonie",
}

PERSONNES = [
    {
        "fichier": "steven-poirier",
        "nom": "Steven Poirier",
        "fonction": "Dirigeant associé",
        "mobile": "",  # à compléter, ex. "06 00 00 00 00"
        "email": "stevenpoirier@inova-securite.fr",
        "carte": "",
    },
    {
        "fichier": "stephane-pasquier",
        "nom": "Stéphane Pasquier",
        "fonction": "Dirigeant associé",
        "mobile": "06 98 15 74 50",
        "email": "stephanepasquier@inova-securite.fr",
        "carte": f"{URL_BASE}/stephane-pasquier/",
    },
]

NUIT, MAGENTA, GRIS = "#1B1030", "#E0287D", "#6B6478"
POLICE = "Arial, Helvetica, sans-serif"
LOGO_L, LOGO_H = 150, 50  # taille affichée (image fournie en x2)


def logo():
    im = Image.open(KIT_LOGO).convert("RGBA")
    l, h = LOGO_L * 2, LOGO_H * 2
    pad = 2
    im.thumbnail((l - 2 * pad, h - 2 * pad), Image.LANCZOS)
    fond = Image.new("RGB", (l, h), "white")
    fond.paste(im, ((l - im.width) // 2, (h - im.height) // 2), im)
    fond.save(SORTIE / "logo-inova-signature.png", optimize=True)


def tel_uri(n):
    return "+33" + n.replace(" ", "")[1:]


def ligne(label, contenu):
    return (f'<tr><td style="padding:0 0 3px 0;font-family:{POLICE};font-size:13px;line-height:18px;color:{NUIT};">'
            f'<span style="color:{MAGENTA};font-weight:bold;">{label}</span>&nbsp;&nbsp;{contenu}</td></tr>')


def lien(url, texte, couleur=NUIT):
    return f'<a href="{url}" style="color:{couleur};text-decoration:none;">{escape(texte)}</a>'


def html_signature(p):
    lignes = []
    if p["mobile"]:
        lignes.append(ligne("M", lien("tel:" + tel_uri(p["mobile"]), p["mobile"])))
    lignes.append(ligne("E", lien("mailto:" + p["email"], p["email"])))
    lignes.append(ligne("W", lien(SOCIETE["site_url"], SOCIETE["site"])))
    lignes.append(f'<tr><td style="padding:0;font-family:{POLICE};font-size:12px;line-height:17px;color:{GRIS};">{escape(SOCIETE["adresse"])}</td></tr>')
    carte = ""
    if p["carte"]:
        carte = (f'<tr><td style="padding:8px 0 0 0;font-family:{POLICE};font-size:12px;line-height:16px;">'
                 f'<a href="{p["carte"]}" style="color:{MAGENTA};text-decoration:none;font-weight:bold;">Ma carte de visite &#8250;</a></td></tr>')
    return f"""<table cellpadding="0" cellspacing="0" border="0" role="presentation" style="border-collapse:collapse;font-family:{POLICE};">
<tr>
<td valign="middle" style="padding:0 16px 0 0;">
<a href="{SOCIETE['site_url']}" style="text-decoration:none;"><img src="{LOGO_URL}" width="{LOGO_L}" height="{LOGO_H}" alt="INOVA Sécurité" style="display:block;width:{LOGO_L}px;height:{LOGO_H}px;border:0;"></a>
</td>
<td valign="top" style="padding:0 0 0 16px;border-left:3px solid {MAGENTA};">
<table cellpadding="0" cellspacing="0" border="0" role="presentation" style="border-collapse:collapse;">
<tr><td style="padding:0;font-family:{POLICE};font-size:16px;line-height:21px;font-weight:bold;color:{NUIT};">{escape(p['nom'])}</td></tr>
<tr><td style="padding:0 0 8px 0;font-family:{POLICE};font-size:12px;line-height:17px;letter-spacing:1px;color:{MAGENTA};">{escape(p['fonction'].upper())} &middot; {escape(SOCIETE['nom'].upper())}</td></tr>
{chr(10).join(lignes)}
{carte}
</table>
</td>
</tr>
<tr><td colspan="2" style="padding:10px 0 0 0;font-family:{POLICE};font-size:11px;line-height:15px;color:{GRIS};">{escape(SOCIETE['metiers'])}</td></tr>
</table>"""


def texte_signature(p):
    t = ["--", p["nom"], f"{p['fonction']} · {SOCIETE['nom']}"]
    if p["mobile"]:
        t.append(f"Mobile : {p['mobile']}")
    t += [p["email"], SOCIETE["site"], SOCIETE["adresse"]]
    return "\n".join(t) + "\n"


PAGE = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>Signatures mail INOVA</title>
<style>
:root{--nuit:#1B1030;--magenta:#E0287D;--brume:#F7F4FA}
body{margin:0;background:var(--brume);color:var(--nuit);font:15px/1.5 Arial,Helvetica,sans-serif}
main{max-width:760px;margin:0 auto;padding:24px 16px 48px}
h1{font-size:22px;margin:0 0 4px} p.intro{margin:0 0 24px;color:#4a4458}
section{background:#fff;border-radius:12px;padding:20px;margin:0 0 20px;box-shadow:0 1px 3px rgba(27,16,48,.08)}
h2{font-size:15px;margin:0 0 14px;letter-spacing:1px;color:var(--magenta)}
.apercu{overflow-x:auto;padding:16px;border:1px dashed #d9d3e2;border-radius:8px;background:#fff}
.actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
button,a.btn{font:inherit;font-weight:bold;border:0;border-radius:8px;padding:10px 14px;cursor:pointer;text-decoration:none}
button.principal{background:var(--magenta);color:#fff} button.second,a.btn{background:var(--brume);color:var(--nuit)}
.ok{color:#18794e;font-weight:bold;align-self:center}
ol{padding-left:20px} li{margin:0 0 6px}
</style></head><body><main>
<h1>Signatures mail INOVA Sécurité</h1>
<p class="intro">Ouvrez cette page sur l'ordinateur, cliquez sur « Copier la signature », puis collez-la dans Outlook (étapes en bas de page).</p>
{BLOCS}
<section><h2>Coller dans Outlook</h2>
<ol>
<li><b>Outlook sur le web</b> (outlook.office.com) : roue dentée › Courrier › Composer et répondre › « + Nouvelle signature ». Nommez-la « INOVA », collez (Ctrl+V), enregistrez. Sous « Signatures par défaut », choisissez « INOVA » pour les nouveaux messages <b>et</b> pour les réponses/transferts, puis enregistrez.</li>
<li><b>Nouvel Outlook pour Windows</b> : Paramètres › Comptes › Signatures, même procédure.</li>
<li><b>Outlook classique (Windows)</b> : Fichier › Options › Courrier › Signatures › Nouveau, collez dans la zone d'édition, puis choisissez-la dans « Nouveaux messages » et « Réponses/transferts ».</li>
<li><b>Outlook Mac</b> : Outlook › Paramètres › Signatures › « + », collez, puis choisissez-la par défaut.</li>
<li><b>Outlook mobile</b> (iPhone/Android) : Paramètres › Signature, collez la version texte.</li>
</ol></section>
</main>
<script>
function copier(id, ok){
  var el=document.getElementById(id), r=document.createRange(), s=window.getSelection();
  s.removeAllRanges(); r.selectNodeContents(el); s.addRange(r);
  var reussi=false; try{reussi=document.execCommand('copy');}catch(e){}
  s.removeAllRanges();
  document.getElementById(ok).textContent = reussi ? 'Copiée ✓' : 'Sélectionnez la signature puis Ctrl+C';
}
function copierTexte(id, ok){
  var t=document.getElementById(id).value;
  (navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).then(
    function(){document.getElementById(ok).textContent='Texte copié ✓';},
    function(){var a=document.getElementById(id);a.style.display='block';a.select();document.execCommand('copy');document.getElementById(ok).textContent='Texte copié ✓';});
}
</script>
</body></html>
"""

BLOC = """<section><h2>{nom}</h2>
<div class="apercu" id="sig-{f}">{html}</div>
<div class="actions">
<button class="principal" onclick="copier('sig-{f}','ok-{f}')">Copier la signature</button>
<button class="second" onclick="copierTexte('txt-{f}','ok-{f}')">Copier la version texte (mobile)</button>
<a class="btn" href="{f}.htm" download>Télécharger le .htm</a>
<span class="ok" id="ok-{f}" aria-live="polite"></span>
</div>
<textarea id="txt-{f}" style="display:none;width:100%;height:140px;margin-top:10px" readonly>{txt}</textarea>
</section>"""


def main():
    SORTIE.mkdir(exist_ok=True)
    if KIT_LOGO.exists():
        logo()
    blocs = []
    for p in PERSONNES:
        h, t = html_signature(p), texte_signature(p)
        (SORTIE / f"{p['fichier']}.htm").write_text(
            f'<!doctype html>\n<html lang="fr"><head><meta charset="utf-8"><title>Signature {escape(p["nom"])}</title></head>\n<body style="margin:0;background:#ffffff;">\n{h}\n</body></html>\n',
            encoding="utf-8")
        (SORTIE / f"{p['fichier']}.txt").write_text(t, encoding="utf-8")
        blocs.append(BLOC.format(nom=escape(p["nom"]), f=p["fichier"], html=h, txt=escape(t)))
    (SORTIE / "index.html").write_text(PAGE.replace("{BLOCS}", "\n".join(blocs)), encoding="utf-8")
    print("OK :", ", ".join(sorted(x.name for x in SORTIE.iterdir())))


if __name__ == "__main__":
    main()
