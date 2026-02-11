# Tasmota Smart Meter Scripts Repository

Dieses Repository enthält Smart Meter Scripts für Tasmota, automatisiert gesammelt aus dem [Tasmota Wiki](https://tasmota.github.io/docs/Smart-Meter-Interface/) und der [Bitshake Documentation](https://docs.bitshake.de/script/).

## Projektstruktur

```
├── scripts/          # Einzelne Smart Meter Scripts (.txt)
├── api/
│   ├── scripts.json  # Vollständige Script-Metadaten (Hersteller, Protokoll, URL)
│   └── list.json     # Vereinfachte Liste für Dropdown-Menüs
└── tools/
    ├── smart_meter_scripts_crawler.py   # Crawler-Skript
    └── requirements.txt                 # Python-Dependencies für den Crawler
```

## API Endpoints

### Script Liste für Dropdown
```
GET https://raw.githubusercontent.com/iot-maker/tasmota-smart-meter-scripts/main/api/list.json
```

### Vollständige Script Informationen

```
GET https://raw.githubusercontent.com/iot-maker/tasmota-smart-meter-scripts/main/api/scripts.json
```

### Einzelnes Script
```
GET https://raw.githubusercontent.com/iot-maker/tasmota-smart-meter-scripts/main/scripts/SCRIPT_NAME.txt
```

## Verwendung in Tasmota

### 1. Script Liste abrufen
```http
GET https://raw.githubusercontent.com/iot-maker/tasmota-smart-meter-scripts/main/api/list.json
```

Antwort:
```json
{
  "version": "1.0",
  "scripts": [
    {
      "name": "EMH eHZ (SML)",
      "filename": "EMH_eHZ_SML.txt"
    }
  ]
}
```

### 2. Script herunterladen
```http
GET https://raw.githubusercontent.com/iot-maker/tasmota-smart-meter-scripts/main/scripts/EMH_eHZ_SML.txt
```

## Crawler (tools/)

Der Crawler extrahiert Smart Meter Scripts automatisiert aus zwei Quellen:

- **Tasmota Wiki** – <https://tasmota.github.io/docs/Smart-Meter-Interface/>
- **Bitshake Documentation** – <https://docs.bitshake.de/script/>

Bei Duplikaten werden Bitshake-Scripts bevorzugt (bessere Qualität). Die Deduplizierung erfolgt über normalisierte Gerätenamen und Script-Ähnlichkeitsvergleich.

### Crawler ausführen

```bash
cd tools
pip install -r requirements.txt
python smart_meter_scripts_crawler.py
```

Der Crawler schreibt die Ergebnisse in einen Ordner `smart_meter_scripts/`. Von dort müssen die Dateien in das `scripts/`-Verzeichnis dieses Repos übernommen und die JSON-Dateien unter `api/` neu generiert werden.

### Hinweis: Automatisierter Cron-Job

Es gab ursprünglich einen GitHub Actions Workflow für tägliches automatisches Crawlen. Dieser wurde deaktiviert und entfernt, da er nicht funktioniert hat.

## Manuelle Anpassungen

Folgende Scripts wurden nach dem Crawlen manuell korrigiert, da die Originalquellen fehlerhafte Werte enthielten:

- **Landis_Gyr_E220_SML.txt** – Ein Wert im Script war falsch gesetzt und wurde manuell korrigiert. Bei einem erneuten Crawl-Lauf wird diese Korrektur überschrieben und muss erneut angepasst werden.

## Verfügbare Protokolle
- SML: 84 Scripts
- OBIS: 41 Scripts
- MODBus: 3 Scripts
- M-Bus: 4 Scripts
- Andere: 19 Scripts

## Letzte Aktualisierung
19.08.2025 16:03:52 UTC
