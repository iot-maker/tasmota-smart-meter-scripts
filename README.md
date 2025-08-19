# Tasmota Smart Meter Scripts Repository

Dieses Repository enthält 151 Smart Meter Scripts für Tasmota, automatisch generiert aus dem Tasmota Wiki und Bitshake Documentation.

## API Endpoints

### Script Liste für Dropdown
```
GET https://raw.githubusercontent.com/USER/REPO/main/api/list.json
```

### Vollständige Script Informationen  
```
GET https://raw.githubusercontent.com/USER/REPO/main/api/scripts.json
```

### Einzelnes Script
```
GET https://raw.githubusercontent.com/USER/REPO/main/scripts/SCRIPT_NAME.txt
```

## Verwendung in Tasmota

### 1. Script Liste abrufen
```http
GET https://raw.githubusercontent.com/USER/REPO/main/api/list.json
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
GET https://raw.githubusercontent.com/USER/REPO/main/scripts/EMH_eHZ_SML.txt
```

## Verfügbare Protokolle
- SML: 84 Scripts
- OBIS: 41 Scripts  
- MODBus: 3 Scripts
- M-Bus: 4 Scripts
- Andere: 19 Scripts

## Letzte Aktualisierung
19.08.2025 16:03:52 UTC

## Automatische Updates
Dieses Repository wird automatisch über GitHub Actions aktualisiert, wenn neue Scripts im Tasmota Wiki oder bei Bitshake verfügbar sind.
