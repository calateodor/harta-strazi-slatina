"""Inject streets.json into the map template and lay out the site folder (served by GitHub Pages).

usage: python -I build.py <template.html> <build_dir> <out_dir>
"""
import json
import shutil
import sys
from pathlib import Path

tpl, build, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)

data = json.loads((build / "streets.json").read_text(encoding="utf-8"))
blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
html = tpl.read_text(encoding="utf-8")
assert html.count("/*__DATA__*/null") == 1
html = html.replace("/*__DATA__*/null", blob)
(out / "index.html").write_text(html, encoding="utf-8")
shutil.copyfile(build / "Strazi-Slatina-toate.kml", out / "Strazi-Slatina-toate.kml")
(out / ".nojekyll").write_text("", encoding="utf-8")

# config.js belongs to the user once they paste their Google key into it: create, never overwrite
cfg = out / "config.js"
if not cfg.exists():
    cfg.write_text(
        "// Cheia Google Maps (Maps JavaScript API), restricționată la https://calateodor.github.io/*\n"
        "// Lipește cheia între ghilimele. Gol = harta folosește imaginile Esri.\n"
        'window.GOOGLE_MAPS_KEY = "";\n', encoding="utf-8")

day = data["osm"][:10]
(out / "Google My Maps - pasi.txt").write_text(f"""STRĂZI SLATINA ÎN GOOGLE MY MAPS (satelit Google, fără cheie API)
Date: OpenStreetMap, {day}

Varianta A - toate străzile, marchezi direct în Google
1. Intră pe https://www.google.com/mymaps (logat cu contul Google) > CREAȚI O HARTĂ NOUĂ.
2. La „Strat fără titlu” apasă „Importați” și alege fișierul  Strazi-Slatina-toate.kml
3. Jos, la „Hartă de bază”, alege „Satelit” (sau „Hibrid”).
4. Ca să marchezi o stradă: click pe ea > iconița de găleată > alege culoarea și grosimea.
   (Dacă găleata e gri: la strat > „Stiluri individuale”.)
5. Ca numele să fie afișate pe hartă: la strat > „Stiluri individuale” > „Setați etichetele” > „name”.
6. Harta apare și pe telefon: aplicația Google Maps > Salvate > Hărți.

Varianta B - marchezi comod pe harta online, apoi trimiți în Google
1. Deschide https://calateodor.github.io/harta-strazi-slatina/
2. Caută și bifează străzile, alege culori.
3. Apasă „Export KML pentru Google” > se descarcă Strazi-marcate-Slatina-<data>.kml
4. Importă fișierul în Google My Maps, ca la pașii 1-3 de mai sus. Culorile se păstrează.
""", encoding="utf-8")

(out / "README.md").write_text(f"""# Străzi Slatina

Hartă interactivă cu toate străzile din municipiul Slatina (date OpenStreetMap din {day}).
Cauți o stradă, o marchezi cu o culoare și rămâne colorată, cu numele scris, la orice zoom.

**Deschide harta:** https://calateodor.github.io/harta-strazi-slatina/

- Fundal: Hartă, Satelit, Hibrid, Teren, OSM (Esri; Google dacă există cheie în `config.js`)
- Click pe o stradă: Marchează, culoare, Street View, Google Maps
- Click dreapta pe hartă: Street View în orice punct
- Export KML pentru Google My Maps / Google Earth, copiere listă, salvare/încărcare marcaje
- Marcajele se păstrează în browserul fiecărui om (nu sunt publice)

## Imagini Google (opțional)

Imaginile Google pot fi folosite oficial doar printr-o cheie Google Maps. Pași:

1. Intră pe https://console.cloud.google.com/google/maps-apis/ cu contul Google, acceptă termenii și creează un proiect (ex. „Harta Slatina”).
2. Google cere un cont de facturare (card). Google Maps are o cotă lunară gratuită; o hartă folosită de câțiva oameni nu ajunge la plată. Pentru siguranță pune limita de la pasul 5.
3. Activează **Maps JavaScript API** (APIs & Services → Library → Maps JavaScript API → Enable).
4. Creează cheia: APIs & Services → Credentials → Create credentials → **API key**, apoi editeaz-o:
   - *Application restrictions* → **Websites** → adaugă `https://calateodor.github.io/*`
   - *API restrictions* → **Restrict key** → doar **Maps JavaScript API** → Save
5. Recomandat: la Quotas pentru Maps JavaScript API pune o limită zilnică (ex. 300 de încărcări pe zi).
6. Deschide https://github.com/calateodor/harta-strazi-slatina/edit/main/config.js, lipește cheia între ghilimele și apasă **Commit changes**. După ~1 minut harta online folosește Google (Hartă, Satelit, Hibrid, Teren și Street View direct în pagină).

Cheia restricționată la site merge doar pe harta online. Dacă nu e acceptată, harta revine singură la imaginile Esri.

## Actualizarea datelor

`_generator/` conține scripturile: `process.py` (din descărcarea Overpass face `streets.json` și KML-ul), `build.py` (construiește `index.html`) și `map_template.html`.

Date străzi © OpenStreetMap contributors (ODbL). Imagini satelit © Esri, Maxar, Earthstar Geographics.
""", encoding="utf-8")
for f in sorted(out.iterdir()):
    print(f"{f.stat().st_size if f.is_file() else '-':>9}  {f.name}")
