# Străzi Slatina

Hartă interactivă cu toate străzile din municipiul Slatina (date OpenStreetMap din 2026-10-21).
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
