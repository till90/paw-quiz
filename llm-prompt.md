Du bist mein "Cloud-Run Service Generator" für data-tales.dev.

INPUT (von mir):
A) Ein bereits vorhandenes Datenset aus meinem Crawler (bereits übersetzt):
   - JSON: `out_pawpatrol_characters/characters_de.json`
   - Bilder: `out_pawpatrol_characters/images/*`
   Struktur in `characters_de.json`     {
      "id": "ryder",
      "name": "Ryder",
      "link_text_from_list": "Ryder",
      "tags": [
        "Species: Human",
        "Occupation: Member of the PAW Patrol (No. 1) Leader of the PAW Patrol Driver of the Sub Patroller"
      ],
      "source": {
        "page_title": "Ryder",
        "page_url": "https://pawpatrol.fandom.com/wiki/Ryder",
        "list_url": "https://pawpatrol.fandom.com/wiki/List_of_characters",
        "text_license_default": "CC BY-SA 3.0 (Unported) — unless otherwise specified",
        "text_license_url": "https://pawpatrol.fandom.com/wiki/PAW_Patrol_Wiki:Copyrights",
        "retrieved_at": "2025-12-17T17:43:52Z",
        "revision_id": 649397,
        "revision_timestamp": "2025-12-12T02:14:31Z",
        "attribution": "Text source: PAW Patrol Wiki (Fandom) — \"Ryder\" (https://pawpatrol.fandom.com/wiki/Ryder) — retrieved 2025-12-17T17:43:52Z, revision 649397 — CC BY-SA 3.0 (Unported) — unless otherwise specified"
      },
      "summary": "Ryder (Hauptcharakter, August 2016) S1-S7 S8-S10 S11 Film LIVE Show Spezies Mensch Geschlecht Männlich ♂ Verwandte Chase (Haustierhund) Marshall (Haustierhund) Skye (Haustierhund) Rocky (Haustierhund) Rubble (Haustierhund) Zuma (Haustierhund) Robo-Dog (Roboterhund und Kreation) Everest (Teilzeitbetreuer) Tracker (Teilzeitbetreuer) Sweetie (Teilzeitbetreuer nur in \"Alle Pfoten an Deck\") Arrby (Teilzeitbetreuer in \"Alle Pfoten an Deck\")",
      "profile": [
        {
          "label": "Spezies",
          "value": "Menschlich"
        },
        {
          "label": "Geschlecht",
          "value": "Männlich ♂"
        },
        {
          "label": "Beziehungen",
          "value": "Chase (Haustier) Marshall (Haustier) Skye (Haustier) Rocky (Haustier) Rubble (Haustier) Zuma (Haustier) Robo-Dog (Roboter-Haustier und Kreation) Everest (Teilzeit-Betreuungsempfänger) Tracker (Teilzeit-Betreuungsempfänger) Sweetie (Teilzeit-Betreuungsempfänger nur in \"Alle Pfoten an Deck\") Arrby (Teilzeit-Betreuungsempfänger nur in \"Alle Pfoten an Deck\") Tuck (Teilzeit-Betreuungsempfänger) Ella (Teilzeit-Betreuungsempfänger) Rex (Teilzeit-Betreuungsempfänger) Liberty (Teilzeit-Betreuungsempfänger) Wild (Teilzeit-Betreuungsempfänger) Rory (Teilzeit-Betreuungsempfänger) Leo (Teilzeit-Betreuungsempfänger) Shade (Teilzeit-Betreuungsempfänger) Al (Teilzeit-Betreuungsempfänger) Coral (Teilzeit-Betreuungsempfänger) Charger (Teilzeit-Betreuungsempfänger) Tot (Teilzeit-Betreuungsempfänger) Nano (Teilzeit-Betreuungsempfänger) Mini (Teilzeit-Betreuungsempfänger) Roxi (Teilzeit-Betreuungsempfänger) Motor (Teilzeit-Betreuungsempfänger in \"Die Welpen gegen die Robo-Ducky \"nur)"
        },
        {
          "label": "Alter",
          "value": "10"
        },
        {
          "label": "Spitznamen",
          "value": "Sir & Sir Ryder (von Chase) Rettet Ryder (vom Fluglotsen in \"Die Welpen retten einen Affen-Seefahrer\") Mr. Nice Boy mit allen Welpen (von Arrby in \"Seepatrouille: Die Welpen retten Puplantis\") Rupert (von Winnie Winnington in \"Die Welpen retten die Superkühe\")"
        },
        {
          "label": "Rolle / Beruf",
          "value": "Mitglied der PAW Patrol (Nr. 1) Anführer der PAW Patrol Fahrer des Sub Patrollers"
        },
        {
          "label": "Erster Auftritt",
          "value": "PAW Patrol: „Die Welpen sorgen für Aufsehen“ Rubble & Crew: „Die Crew baut eine Brücke“"
        },
        {
          "label": "Mag",
          "value": "Die PAW Patrol, Robo-Dog, die Mighty Twins (Tuck und Ella), das Katzenrudel, die Junior-Patrouillen, Sweetie (manchmal), Arrby (manchmal), die Bauarbeiter, den Bewohnern von Adventure Bay helfen, seine Welpen beschützen, Äpfel, Spiele auf seinem Pup-Pad spielen, Organisation, Erfinden, seine Spezialwerkzeuge, mit seinen Welpen spielen"
        },
        {
          "label": "Mag nicht",
          "value": "Seine Welpen in Gefahr, Rosenkohl, Unordnung, Bürgermeister Humdingers Intrigen, dass Danny ihn (früher) „Daring Danny X“ nennen musste, Dannys Rücksichtslosigkeit, der Diebstahl des Aussichtsturms, die Unfähigkeit, seinen Welpen zu helfen, Alex' Übermütigkeit, Tintenfisch-Jerky, Rockys Beschwerden über Nässe [1], der Verlust von Chases Vertrauen [2], Sweetie (manchmal), Arrby (manchmal), Codi Gizmody, seine abgelehnten Ratschläge, böse Menschen (insbesondere Bürgermeister Humdingers Wahnvorstellungen), Rubbles Aberglaube"
        },
        {
          "label": "Stimme (US/Kanada)",
          "value": "Owen Mason (Staffel 1 – Mitte Staffel 2) Elijha Hammill (Mitte Staffel 2 – Ende Staffel 3) Jaxon Mercey (Ende Staffel 3 – Anfang Staffel 6, „Mighty Pups“ und „Ready Race Rescue“) Joey Nijem (Anfang Staffel 6 – Ende Staffel 7, „Jet to the Rescue“) Beckett Hipkiss (Ende Staffel 7 – Ende Staffel 8) Kai Harris (Ende Staffel 8 – heute) Will Brisbin (PAW Patrol: Der Film) Finn Lee-Epp (PAW Patrol: Der Mighty Film) Henry Bolan (PAW Patrol: Der Dino-Film) [3] Bentley Griffin (PAW Patrol: Grand Prix) Remi Tuckman (PAW Patrol: World) David Mattle (PAW Patrol: Rescue Wheels Championship)"
        },
        {
          "label": "Stimme (UK)",
          "value": "John Campbell (Staffel 1 – S2 E13) Solomon Brown (S2 E14 – Staffel 6) Lewis Crabb-LaHei (Staffel 7 – S11 EP2) Dexter Turley (S11 EP3 – heute)"
        }
      ],
      "profile_groups": [],
      "profile_flat": {
        "Spezies": "Menschlich",
        "Geschlecht": "Männlich ♂",
        "Beziehungen": "Chase (Haustier) Marshall (Haustier) Skye (Haustier) Rocky (Haustier) Rubble (Haustier) Zuma (Haustier) Robo-Dog (Roboter-Haustier und Kreation) Everest (Teilzeit-Betreuungsempfänger) Tracker (Teilzeit-Betreuungsempfänger) Sweetie (Teilzeit-Betreuungsempfänger nur in \"Alle Pfoten an Deck\") Arrby (Teilzeit-Betreuungsempfänger nur in \"Alle Pfoten an Deck\") Tuck (Teilzeit-Betreuungsempfänger) Ella (Teilzeit-Betreuungsempfänger) Rex (Teilzeit-Betreuungsempfänger) Liberty (Teilzeit-Betreuungsempfänger) Wild (Teilzeit-Betreuungsempfänger) Rory (Teilzeit-Betreuungsempfänger) Leo (Teilzeit-Betreuungsempfänger) Shade (Teilzeit-Betreuungsempfänger) Al (Teilzeit-Betreuungsempfänger) Coral (Teilzeit-Betreuungsempfänger) Charger (Teilzeit-Betreuungsempfänger) Tot (Teilzeit-Betreuungsempfänger) Nano (Teilzeit-Betreuungsempfänger) Mini (Teilzeit-Betreuungsempfänger) Roxi (Teilzeit-Betreuungsempfänger) Motor (Teilzeit-Betreuungsempfänger in \"Die Welpen gegen die Robo-Ducky \"nur)",
        "Alter": "10",
        "Spitznamen": "Sir & Sir Ryder (von Chase) Rettet Ryder (vom Fluglotsen in \"Die Welpen retten einen Affen-Seefahrer\") Mr. Nice Boy mit allen Welpen (von Arrby in \"Seepatrouille: Die Welpen retten Puplantis\") Rupert (von Winnie Winnington in \"Die Welpen retten die Superkühe\")",
        "Rolle / Beruf": "Mitglied der PAW Patrol (Nr. 1) Anführer der PAW Patrol Fahrer des Sub Patrollers",
        "Erster Auftritt": "PAW Patrol: „Die Welpen sorgen für Aufsehen“ Rubble & Crew: „Die Crew baut eine Brücke“",
        "Mag": "Die PAW Patrol, Robo-Dog, die Mighty Twins (Tuck und Ella), das Katzenrudel, die Junior-Patrouillen, Sweetie (manchmal), Arrby (manchmal), die Bauarbeiter, den Bewohnern von Adventure Bay helfen, seine Welpen beschützen, Äpfel, Spiele auf seinem Pup-Pad spielen, Organisation, Erfinden, seine Spezialwerkzeuge, mit seinen Welpen spielen",
        "Mag nicht": "Seine Welpen in Gefahr, Rosenkohl, Unordnung, Bürgermeister Humdingers Intrigen, dass Danny ihn (früher) „Daring Danny X“ nennen musste, Dannys Rücksichtslosigkeit, der Diebstahl des Aussichtsturms, die Unfähigkeit, seinen Welpen zu helfen, Alex' Übermütigkeit, Tintenfisch-Jerky, Rockys Beschwerden über Nässe [1], der Verlust von Chases Vertrauen [2], Sweetie (manchmal), Arrby (manchmal), Codi Gizmody, seine abgelehnten Ratschläge, böse Menschen (insbesondere Bürgermeister Humdingers Wahnvorstellungen), Rubbles Aberglaube",
        "Stimme (US/Kanada)": "Owen Mason (Staffel 1 – Mitte Staffel 2) Elijha Hammill (Mitte Staffel 2 – Ende Staffel 3) Jaxon Mercey (Ende Staffel 3 – Anfang Staffel 6, „Mighty Pups“ und „Ready Race Rescue“) Joey Nijem (Anfang Staffel 6 – Ende Staffel 7, „Jet to the Rescue“) Beckett Hipkiss (Ende Staffel 7 – Ende Staffel 8) Kai Harris (Ende Staffel 8 – heute) Will Brisbin (PAW Patrol: Der Film) Finn Lee-Epp (PAW Patrol: Der Mighty Film) Henry Bolan (PAW Patrol: Der Dino-Film) [3] Bentley Griffin (PAW Patrol: Grand Prix) Remi Tuckman (PAW Patrol: World) David Mattle (PAW Patrol: Rescue Wheels Championship)",
        "Stimme (UK)": "John Campbell (Staffel 1 – S2 E13) Solomon Brown (S2 E14 – Staffel 6) Lewis Crabb-LaHei (Staffel 7 – S11 EP2) Dexter Turley (S11 EP3 – heute)"
      },
      "image": {
        "local_path": "images/ryder.webp",
        "sha256": "344ecdfcd6dfd0d5d6a231b039aa6d9736a5289e781ed0e8561e93e36973b613",
        "info": {
          "file_title": "File:Pic-ryder x1500.webp",
          "file_page_url": "https://pawpatrol.fandom.com/wiki/File%3APic-ryder_x1500.webp",
          "original_url": "https://static.wikia.nocookie.net/paw-patrol/images/d/d7/Pic-ryder_x1500.webp/revision/latest?cb=20250108214529",
          "description_url": "https://pawpatrol.fandom.com/wiki/File:Pic-ryder_x1500.webp",
          "mime": "image/webp",
          "width": 536,
          "height": 604,
          "license_short": null,
          "license_url": null,
          "usage_terms": null,
          "non_free": null,
          "attribution": "https://pawpatrol.fandom.com/wiki/File%3APic-ryder_x1500.webp | retrieved 2025-12-17T17:43:52Z",
          "extmetadata": {
            "DateTime": "2025-01-08T21:45:29Z",
            "ObjectName": "Pic-ryder x1500"
          }
        }
      }
    },
B) Liste vorhandener Services (Name -> URL):
   - "PLZ → Koordinaten" -> "https://plz.data-tales.dev/"
   - "PAW Patrol – Quiz" -> (dieser neue Service; Root "/")

C) Styling-Referenz: Meine Landing Page nutzt CSS-Variablen und Komponenten (siehe Anhang: style.css + index.html).
   Nutze diese Variablen 1:1 (nur die, die du wirklich nutzt) für `:root` und `[data-theme="light"]`.
   Der Look darf nicht verändert werden, nur minimal ergänzende Klassen sind erlaubt.

ZIEL:
Erstelle ein vollständiges, lauffähiges Mini-Webprojekt, das auf Google Cloud Run deploybar ist (Source Deploy, ohne Dockerfile), mit:
- Flask Backend + Gunicorn Start (Cloud Run kompatibel, PORT via env)
- einer HTML Oberfläche für den User: "PAW Patrol Quiz"
- einheitlichem Header im Landing-Style (sticky + blur + gleiche Button/Komponentenklassen)
- Theme Toggle (dark/light) mit localStorage, identisch zum Landing Verhalten
- Navigation: Links zur Landing Page + Cookbook + PLZ-Service + dieser Quiz-Service
- saubere Fehlerbehandlung (keine Stacktraces), robuste Dateipfade
- /api Endpunkte als JSON für das Quiz
- sichere Auslieferung lokaler Bilder (/media) mit Path-Traversal-Schutz + Cache-Headern

QUIZ-FUNKTIONALITÄT (sehr wichtig):
1) Startseite zeigt direkt das Quiz (kein Suchfeld).
2) Im Zentrum wird ein Charakter-Bild angezeigt (aus `image.local_path`), in einem einheitlichen Format:
   - Nutze `aspect-ratio` + `object-fit: contain`, sodass unterschiedlich große Bilder gleich wirken (z.B. 1:1).
3) Unter dem Bild sind exakt 3 Auswahlmöglichkeiten (Buttons):
   - 1x richtiger Name (der angezeigte Charakter)
   - 2x zufällige falsche Namen (andere Charaktere, eindeutig, nicht doppelt)
4) Klick-Verhalten und Visual Feedback:
   - Sobald der User einen Namen anklickt, wird die Antwort "gelocked" (keine weiteren Klicks auf die Optionen).
   - Wenn richtig:
     - geklickter Button wird grün, bekommt einen Haken ✓
     - beide falschen Buttons werden ausgegraut (disabled/grey)
   - Wenn falsch:
     - geklickter Button wird rot, bekommt ein Kreuz ✕ (und bleibt NICHT ausgegraut)
     - der richtige Button wird grün, bekommt einen Haken ✓
     - der übrige falsche Button wird ausgegraut
5) Sobald ein Name geklickt wurde (egal ob richtig/falsch), erscheinen darunter die Infos aus `profile_flat`
   - ABER: OHNE die Keys "Stimme (US/Kanada)" und "Stimme (UK)" (diese müssen im UI nicht angezeigt werden)
   - Darstellung als Key/Value Liste (zweispaltig auf Desktop, einspaltig mobil)
6) Neben dem Bild (rechts) ist ein großer Würfel-Button (visuell wie ein Würfel):
   - Klick darauf lädt zufällig die nächste Frage (neuer Charakter + neue 3 Optionen)
   - Die UI wird zurückgesetzt (keine Auswahl markiert, keine Details sichtbar, Buttons wieder aktiv)
7) Über dem Würfel ist ein Score:
   - Zeigt: "Score: X"
   - X = Anzahl korrekt gelöster Fragen in dieser Session (clientseitig, z.B. in JS + localStorage optional)
   - Erhöht sich nur bei korrekter Antwort (einmal pro Frage)

DATENFILTER (wichtig):
- Quiz soll nur Charaktere verwenden, die:
  - ein nicht-leeres `profile_flat` besitzen
  - ein Bild besitzen (`image.local_path` vorhanden) und die Datei existiert (falls nicht, diesen Charakter überspringen)
- Wenn ausnahmsweise keine validen Charaktere gefunden werden: UI zeigt eine klare Fehlermeldung als Card.

API-ANFORDERUNGEN (für JS-Quiz):
- `GET /api/question`
  -> liefert eine neue Frage als JSON:
     {
       ok: true,
       question: {
         qid: "<uuid oder hash>",
         character: { id, name, image_url },
         options: [ { id, name }, { id, name }, { id, name } ]
       }
     }
  -> Die `options` müssen gemischt (shuffle) sein.
- `POST /api/reveal`
  Body JSON: { qid: "...", choice_id: "..." }
  -> Antwort:
     {
       ok: true,
       correct: true/false,
       correct_id: "...",
       profile_flat: { ... }   // bereits gefiltert (ohne Stimme-Keys)
       source: { page_url, attribution }
     }
  -> Keine Server-Session notwendig; qid darf stateless validiert werden (z.B. HMAC-Signatur) ODER du darfst den correct_id im qid codieren.
     Wichtig: robust und ohne in-memory state, damit Cloud Run horizontal skaliert.
- `GET /api/health`
  -> { ok: true }

MEDIA:
- `GET /media/<path>` (oder äquivalent)
  -> liefert lokale Bilder aus `out_pawpatrol_characters/images/` sicher aus (Path-Traversal verhindern)
  -> setzt Cache-Control (public, max-age=..., immutable)

AUSGABEFORMAT (sehr wichtig):
Gib AUSSCHLIESSLICH die folgenden Dateien aus, jeweils in einem eigenen Codeblock mit Dateiname als Überschrift:
1) `requirements.txt`
2) `main.py`
3) `README.md`
Keine weiteren Erklärtexte außerhalb der Dateien.

ARCHITEKTUR-VORGABEN:
- Datei heißt `main.py` und exportiert `app` (Flask instance), damit Cloud Run standardmäßig `gunicorn -b :$PORT main:app` nutzen kann.
- Keine externen Templates-Dateien; nutze `render_template_string`, damit es bei 3 Dateien bleibt.
- Kein Docker Compose, kein Dockerfile.
- Projekt liest das Datenset aus dem Repo-Dateisystem:
  - Default: `out_pawpatrol_characters/characters_de.json`
  - Default: `out_pawpatrol_characters/` als Basis für relative Pfade wie `image.local_path`
  - Optional per ENV konfigurierbar:
    - `DATA_JSON_PATH` (Pfad zur JSON)
    - `DATA_BASE_DIR` (Basis für relative Pfade wie image.local_path)
- Beim Start: JSON einmalig laden, validieren (Schema-light), und in-memory cachen (z.B. lru_cache).
- Strikte Robustheit:
  - Wenn JSON fehlt oder ungültig: UI zeigt klare Fehlermeldung (Card) und API liefert {ok:false,...}.
  - Keine Stacktraces im Browser.
- Input-Validierung:
  - `id` nur `[a-z0-9-]{1,80}` zulassen.
  - `qid` und `choice_id` strikt validieren (Regex) und serverseitig gegen Manipulation schützen.
  - `media` Route muss Path-Traversal verhindern (nur erlaubte Unterpfade unterhalb `DATA_BASE_DIR`).
- Security:
  - timeouts sind nicht relevant (keine externen Calls), aber robuste Fehlerbehandlung ist Pflicht.
  - Keine Debug-Ausgaben, keine sensitiven Pfade im UI.

LANDING STYLE CSS (muss verwendet werden):
- Nutze exakt die CSS Variablen aus meiner Landing Page als `:root` und `[data-theme="light"]`.
- Header-Komponenten semantisch an Landing Page angelehnt:
  - `.site-header`, `.container`, `.header-inner`, `.brand`, `.brand-mark`, `.nav`, `.header-actions`,
    `.btn`, `.btn-primary`, `.btn-ghost`
- Du darfst zusätzlich minimal ergänzen (z.B. `.quiz-wrap`, `.quiz-card`, `.quiz-image`, `.option-btn`, `.dice-btn`, `.score`),
  aber NICHT den Look ändern.
- Entferne Variablen, die du nicht nutzt.

HEADER/LINKS:
- Brand klickt auf LANDING_URL
- Nav enthält: "Landing", "Cookbook", plus Links:
  - "PLZ → Koordinaten" -> "https://plz.data-tales.dev/"
  - "PAW Patrol – Quiz" -> "/" (aktueller Service)
- Rechtes Ende: Theme Toggle Button (☾/☀) + optional Primary Button zur Landing-Kontaktsektion.
- Keine generischen Platzhalter-Links.

THEME TOGGLE (identisch zur Landing):
- setzt `data-theme="light"` auf `document.documentElement` (oder entfernt es)
- speichert `theme` in localStorage
- Icon wechselt ☾/☀

README-VORGABEN:
- Kurzer Zweck (1–2 Sätze)
- Lokales Starten:
  - `python -m venv .venv`
  - pip install
  - `python main.py`
  - URL nennen
- Cloud Run Deploy (Source):
  - `gcloud run deploy <service-name> --source . --region europe-west1 --allow-unauthenticated`
- Hinweis auf env vars (falls genutzt): `DATA_JSON_PATH`, `DATA_BASE_DIR`
- Optional: Domain mapping Hinweis "Subdomain -> Cloud Run"

INPUT-DATEN:
LANDING_URL = "https://data-tales.dev/"
COOKBOOK_URL = "https://data-tales.dev/cookbook/"

SERVICE_META:
- service_name_slug: "paw-quiz"
- page_title: "PAW Patrol – Quiz"
- page_h1: "PAW Patrol Quiz"
- page_subtitle: "Errate den Charakter anhand des Bildes."

WICHTIG:
- Liefere lauffähigen Code ohne TODOs.
- Keine externen Template-Dateien; alles in `main.py` via `render_template_string`.
- Keine zusätzlichen erklärenden Texte außerhalb der drei Dateien.