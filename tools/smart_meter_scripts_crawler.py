#!/usr/bin/env python3
"""
Smart Meter Scripts Crawler - Final Cleaned Version

Extrahiert Smart Meter Scripts von Tasmota Wiki und Bitshake Documentation
Basiert auf dem funktionierenden ursprünglichen Skript, bereinigt von unnötigen Teilen.
"""

import requests
from bs4 import BeautifulSoup
import re
import os
from difflib import SequenceMatcher

def extract_meter_name_from_heading(heading_element):
    """Extrahiert Smart Meter Namen aus Überschrift"""
    if not heading_element:
        return None
    
    text = heading_element.get_text().strip()
    
    # Normalisiere alle Landis+Gyr Varianten BEVOR die Regex läuft
    text_lower = text.lower()
    if 'gyr' in text_lower:
        original_text = text
        # Ersetze alle Varianten durch die korrekte Schreibweise
        text = re.sub(r'\bLandis\+Gyr\b', 'Landis + Gyr', text, flags=re.IGNORECASE)
        text = re.sub(r'\bLandis\s+Gyr\b', 'Landis + Gyr', text, flags=re.IGNORECASE)
        # Gyr am Wortanfang (ohne Landis davor) wird zu Landis + Gyr
        text = re.sub(r'(?<!\+\s)\bGyr\b', 'Landis + Gyr', text, flags=re.IGNORECASE)
    
    # Verbesserte Regex Patterns für Geräte-Erkennung
    patterns = [
        # Pattern 1: Vollständiger Herstellername + vollständiger Modellname (z.B. "Engelmann SensoStar E", "Carlo Gavazzi EM340", "Landis + Gyr E220", "EMH eHZ")
        r'([A-Za-z][a-zA-Z]*(?:\s*[\+\-\&]\s*[A-Za-z][a-zA-Z]*|\s+[A-Za-z][a-zA-Z]*)*)\s+([A-Za-z][a-zA-Z0-9]*(?:[A-Z0-9\-\.\/\+]*[A-Z0-9])?)',
        # Pattern 2: Abkürzung + Vollständiger Modellname (z.B. "eBZ DD3", "EFR SGM-C2")  
        r'([a-zA-Z]{2,})\s+([A-Za-z0-9][A-Z0-9\-\.\s/]*[A-Z0-9])',
        # Pattern 3: Hersteller + Modell mit Zahlen (z.B. "Iskra MT681", "DZG DWS7410")
        r'([A-Za-z][a-zA-Z]*)\s+([A-Za-z]*[A-Z]*\d+[A-Z0-9\-\.\s/]*)',
        # Pattern 4: Fallback für kürzere Namen (mindestens 3 Zeichen Modell)
        r'([A-Za-z][a-zA-Z]+)\s+([A-Za-z0-9]{3,}[A-Z0-9\-\.\s/]*)',
        # Pattern 5: Spezialfall für abgekürzte Herstellernamen (z.B. "Engelmann Se", "Resol De")
        r'([A-Za-z][a-zA-Z]+)\s+([A-Za-z][a-z])\b',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            manufacturer = match.group(1).strip()
            model = match.group(2).strip()
            
            # Spezialbehandlung für abgekürzte Herstellernamen
            abbreviation_mapping = {
                'Se': 'SensoStar',
                'De': 'DeltaSol',
                'Po': 'Pollucom F'
            }
            
            # Prüfe ob das "Modell" eine Abkürzung ist
            if model in abbreviation_mapping:
                model = abbreviation_mapping[model]
            
            # Validierung: Modell muss mindestens 2 sinnvolle Zeichen haben (reduziert von 3)
            model_clean = re.sub(r'[\s\-\.]', '', model)
            
            if (len(manufacturer) >= 2 and 
                len(model_clean) >= 2 
                and # Reduziert auf 2 für abgekürzte Namen
                not any(word in text.lower() for word in ['script', 'view', 'example', 'alternative']) 
                and not model_clean.lower() in ['xxx', 'tbd', 'etc', 'und']):  # Keine Platzhalter
                
                return f"{manufacturer} {model}"
    
    # Reduzierte Spezialbehandlung nur für echte Edge Cases
    special_cases = {
        # Komplexe Überschriften mit Zusatzinformationen
        'sensus pollucom': 'Sensus Pollucom F',
        # Vollständige Produktnamen, die nicht aus dem Text extrahiert werden können
        'huawei r4850': 'HUAWEI R4850G2',
        # Einzelwort-Geräte ohne expliziten Hersteller
        'ehzb': 'EMH eHZB',  # Elektronischer Haushaltszähler Version B
    }
    
    text_lower = text.lower()
    
    # Spezielle Behandlung für Sensus Pollucom um technische Suffixe zu entfernen
    if 'sensus pollucom' in text_lower:
        return 'Sensus Pollucom F'
    
    # Führe Regex-Erkennung auf normalisiertem Text aus
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            manufacturer = match.group(1).strip()
            model = match.group(2).strip()
            
            # Spezialbehandlung für abgekürzte Herstellernamen
            abbreviation_mapping = {
                'Se': 'SensoStar',
                'De': 'DeltaSol',
                'Po': 'Pollucom F'
            }
            
            # Prüfe ob das "Modell" eine Abkürzung ist
            if model in abbreviation_mapping:
                return abbreviation_mapping[model]
                
            return f"{manufacturer} {model}"
    
    # Fallback auf special_cases für Edge Cases
    for key, value in special_cases.items():
        if key in text_lower:
            # Für Sensus: keine zusätzlichen Details extrahieren
            if 'sensus' in key:
                return value
            # Erweitere um weitere Details falls vorhanden (für andere Hersteller)
            remaining = text_lower.replace(key, '').strip()
            if remaining:
                # Extrahiere zusätzliche Modelldetails
                extra_match = re.search(r'([a-z0-9\-\.]+)', remaining)
                if extra_match:
                    return f"{value} {extra_match.group(1).upper()}"
            return value
    
    return None

def extract_protocol_info(script_content):
    """Extrahiert Protokoll-Information aus Script"""
    if '+1,' in script_content and 's,' in script_content:
        return 'SML'
    elif '+1,' in script_content and 'o,' in script_content:
        return 'OBIS'
    elif 'MODBus' in script_content or 'modbus' in script_content.lower():
        return 'MODBus'
    elif 'M-Bus' in script_content or 'mbus' in script_content.lower():
        return 'M-Bus'
    elif 'VBus' in script_content or 'vbus' in script_content.lower():
        return 'VBus'
    elif 'CANBus' in script_content or 'canbus' in script_content.lower():
        return 'CANBus'
    return 'Unknown'

def extract_variant_info(script_content, heading_text):
    """Extrahiert Varianten-Information aus Script oder Überschrift"""
    variant_info = []
    
    # Suche nach spezifischen Varianten-Kennzeichen
    if 'extended dataset' in heading_text.lower():
        variant_info.append('Extended')
    elif 'simplified dataset' in heading_text.lower():
        variant_info.append('Simplified')
    elif 'full dataset' in heading_text.lower():
        variant_info.append('Full')
    elif 'daily values' in heading_text.lower():
        variant_info.append('Daily Values')
    elif 'two direction' in heading_text.lower():
        variant_info.append('Bidirectional')
    elif 'alternative' in heading_text.lower():
        variant_info.append('Alternative')
    
    # Suche nach Protokoll in Überschrift
    if 'SML' in heading_text:
        variant_info.append('SML')
    elif 'OBIS' in heading_text:
        variant_info.append('OBIS')
    elif 'MODBus' in heading_text:
        variant_info.append('MODBus')
    
    return ' '.join(variant_info) if variant_info else None

def normalize_device_name(name):
    """Normalisiert Gerätenamen für Vergleich"""
    return re.sub(r'[\s\-\.\+]', '', name.lower())

def sanitize_filename(filename):
    """Bereinigt Dateinamen für Windows-Dateisystem"""
    invalid_chars = '<>:"|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '')
    
    filename = filename.replace('\\', '-').replace('/', '-')
    filename = re.sub(r'\s+', ' ', filename)
    
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename.strip()

def extract_scripts_from_element(element):
    """Extrahiert alle Tasmota Scripts aus einem Element"""
    scripts = []
    
    code_blocks = element.find_all('code')
    
    for code_block in code_blocks:
        code_text = code_block.get_text()
        
        tasmota_markers = ['>D', '>B', '>M', '+1,']
        if any(marker in code_text for marker in tasmota_markers):
            
            lines = code_text.strip().split('\n')
            cleaned_lines = []
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('//'):
                    cleaned_lines.append(line)
            
            if len(cleaned_lines) >= 3:  # Mindestens 3 Zeilen für gültiges Script
                scripts.append('\n'.join(cleaned_lines))
    
    return scripts

def similarity(a, b):
    """Berechnet Ähnlichkeit zwischen zwei Strings"""
    return SequenceMatcher(None, a, b).ratio()

def crawl_tasmota_wiki():
    """Crawlt Tasmota Wiki nach Smart Meter Scripts"""
    url = "https://tasmota.github.io/docs/Smart-Meter-Interface/"
    scripts = {}
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Finde die "Smart Meter Descriptors" Sektion
        descriptors_section = None
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
            if 'smart meter descriptors' in heading.get_text().lower():
                descriptors_section = heading
                break
        
        if not descriptors_section:
            print("Smart Meter Descriptors Sektion nicht gefunden!")
            return {}
        
        print(f"Gefunden: {descriptors_section.get_text().strip()}")
        
        # Sammle alle Elemente bis zur nächsten Hauptüberschrift
        section_elements = []
        current = descriptors_section.next_sibling
        
        while current:
            if hasattr(current, 'name') and current.name:
                # Stoppe bei nächster Hauptüberschrift (h1, h2)
                if current.name in ['h1', 'h2']:
                    break
                section_elements.append(current)
            current = current.next_sibling
        
        print(f"Analysiere {len(section_elements)} Elemente in der Sektion...")
        
        # Strategie 1: details-Elemente in der Sektion
        for element in section_elements:
            if hasattr(element, 'name') and hasattr(element, 'find_all'):
                details_elements = element.find_all('details')
                for details in details_elements:
                    summary = details.find('summary')
                    if summary:
                        meter_name = extract_meter_name_from_heading(summary)
                    if meter_name:
                        element_scripts = extract_scripts_from_element(details)
                            
                        for script in element_scripts:
                                protocol = extract_protocol_info(script)
                                variant = extract_variant_info(script, summary.get_text())
                                
                                key = normalize_device_name(meter_name)
                                if key not in scripts:
                                    scripts[key] = []
                                
                                scripts[key].append({
                                    'device_name': meter_name,
                                    'script': script,
                                    'protocol': protocol,
                                    'variant': variant,
                                    'source': 'Tasmota Wiki',
                                    'url': url
                                })
        
        # Strategie 2: Überschriften + Code in der Sektion
        for element in section_elements:
            if hasattr(element, 'name') and element.name in ['h3', 'h4', 'h5', 'h6']:
                meter_name = extract_meter_name_from_heading(element)
                if meter_name:
                    element_scripts = []
                    
                    # Sammle Scripts von diesem Element bis zur nächsten Überschrift
                    current = element.next_sibling
                    while current:
                        if hasattr(current, 'name') and current.name:
                            if current.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                                break
                        if hasattr(current, 'find_all'):
                            element_scripts.extend(extract_scripts_from_element(current))
                        current = current.next_sibling
                    
                    for script in element_scripts:
                        protocol = extract_protocol_info(script)
                        variant = extract_variant_info(script, element.get_text())
                        
                        key = normalize_device_name(meter_name)
                        if key not in scripts:
                            scripts[key] = []
                        
                        # Prüfe auf Duplikate
                        is_duplicate = False
                        for existing in scripts[key]:
                            if similarity(script, existing['script']) > 0.8:
                                is_duplicate = True
                                break
                        
                        if not is_duplicate:
                            scripts[key].append({
                                'device_name': meter_name,
                                'script': script,
                                'protocol': protocol,
                                'variant': variant,
                                'source': 'Tasmota Wiki',
                                'url': url
                            })
        
        print(f"Tasmota Wiki: {sum(len(v) for v in scripts.values())} Scripts von {len(scripts)} Geräten")
        return scripts
        
    except Exception as e:
        print(f"Fehler beim Crawlen des Tasmota Wiki: {e}")
        return {}

def crawl_bitshake():
    """Crawlt Bitshake Documentation - mit Anmerkungen als Kommentare"""
    url = "https://docs.bitshake.de/script/"
    scripts = {}
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        content = soup.get_text()
        sections = re.split(r'\n\s*-{5,}\s*\n', content)
        
        for section in sections:
            if not section.strip():
                continue
                
            lines = section.strip().split('\n')
            if not lines:
                continue
                
            device_name = lines[0].strip()
            
            if (not device_name or 
                len(device_name) > 100 or 
                len(device_name) < 3 or
                device_name.lower() in ['bitshake', 'impressum']):
                continue
            
            # Bereinige und validiere Gerätenamen
            device_name = device_name.strip()
            
            # Verwende extract_meter_name_from_heading für konsistente Normalisierung
            # Erstelle ein temporäres Element-ähnliches Objekt für die Funktion
            class TempElement:
                def __init__(self, text):
                    self.text = text
                def get_text(self):
                    return self.text
            
            temp_element = TempElement(device_name)
            normalized_name = extract_meter_name_from_heading(temp_element)
            if normalized_name:
                device_name = normalized_name
            
            # Reduzierte Spezialbehandlung für Bitshake - nur echte Edge Cases
            device_name_fixes = {
                # Mehrteilige Herstellernamen
                'Elster / Honeywell': 'Elster Honeywell',
                # Bekannte Vollnamen, die Bitshake abkürzt
                'COMBO Me': 'COMBO Meter',
                # Unklare Abkürzungen
                'HZ Ge': 'HZ Generation',
                'Web Re': 'Web Reader', 
                'Meter De': 'Meter Device',
            }
            
            for old_name, new_name in device_name_fixes.items():
                if old_name in device_name:
                    device_name = device_name.replace(old_name, new_name)
            
            script_content = '\n'.join(lines[1:]).strip()
            
            # Prüfe ob es ein Tasmota Script ist
            tasmota_markers = ['>D', '>B', '>M', '+1,']
            if not any(marker in script_content for marker in tasmota_markers):
                continue
            
            # Bereinige Script
            script_lines = script_content.split('\n')
            cleaned_lines = []
            
            for line in script_lines:
                line = line.strip()
                if line and not line.startswith('//'):
                    cleaned_lines.append(line)
            
            if len(cleaned_lines) < 3:
                continue
            
            final_script = '\n'.join(cleaned_lines)
            
            # Extrahiere versteckte Modellnummern aus dem Volltext der Sektion
            # Suche nach Honeywell/Elster Modellnummern in Anmerkungen
            if 'honeywell' in device_name.lower() or 'elster' in device_name.lower():
                model_match = re.search(r'(AS\d{4})', section)
                if model_match:
                    model = model_match.group(1)
                    if 'elster' in device_name.lower():
                        device_name = f"Elster Honeywell {model}"
                    else:
                        device_name = f"Honeywell {model}"
            
            protocol = extract_protocol_info(final_script)
            variant = extract_variant_info(final_script, device_name)
            
            key = normalize_device_name(device_name)
            if key not in scripts:
                scripts[key] = []
            
            scripts[key].append({
                'device_name': device_name,
                'script': final_script,
                'protocol': protocol,
                'variant': variant,
                'source': 'Bitshake',
                'url': url
            })
        
        print(f"Bitshake: {sum(len(v) for v in scripts.values())} Scripts von {len(scripts)} Geräten")
        return scripts
        
    except Exception as e:
        print(f"Fehler beim Crawlen von Bitshake: {e}")
        return {}

def merge_scripts(tasmota_scripts, bitshake_scripts):
    """Mergt Scripts und entfernt Duplikate intelligenter"""
    merged = {}
    
    # Füge zuerst alle Bitshake Scripts hinzu (bessere Qualität)
    for key, scripts in bitshake_scripts.items():
        merged[key] = scripts
    
    # Füge Tasmota Scripts hinzu, die nicht in Bitshake vorhanden sind
    for key, scripts in tasmota_scripts.items():
        if key not in merged:
            merged[key] = scripts
    
    return merged

def save_scripts(scripts):
    """Speichert Scripts in Dateien"""
    output_dir = "smart_meter_scripts"
    os.makedirs(output_dir, exist_ok=True)
    
    # Lösche alte Dateien
    for filename in os.listdir(output_dir):
        if filename.endswith('.txt'):
            filepath = os.path.join(output_dir, filename)
            os.remove(filepath)
    
    for device_scripts in scripts.values():
        for script_data in device_scripts:
            device_name = script_data['device_name']
            protocol = script_data['protocol']
            script_content = script_data['script']
            
            # Erstelle Dateinamen mit Protokoll falls verfügbar
            filename = device_name
            if protocol and protocol != 'Unknown':
                filename += f" ({protocol})"
            filename = sanitize_filename(filename) + ".txt"
            
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            print(f"Saved: {filename}")

def main():
    """Hauptfunktion"""
    print("=== SMART METER SCRIPT CRAWLER ===")
    print("Crawlt Tasmota Wiki und Bitshake Documentation\n")
    
    print("1. Crawle Tasmota Wiki...")
    tasmota_scripts = crawl_tasmota_wiki()
    
    print("\n2. Crawle Bitshake Documentation...")
    bitshake_scripts = crawl_bitshake()
    
    print("\n3. Merge und dedupliziere Scripts...")
    merged_scripts = merge_scripts(tasmota_scripts, bitshake_scripts)
    
    print("\n4. Speichere finale Scripts...")
    save_scripts(merged_scripts)
    
    # Statistiken
    print(f"\nStatistiken:")
    print(f"- Gesamt: {sum(len(v) for v in merged_scripts.values())} Scripts")
    print(f"- Geräte: {len(merged_scripts)}")
    print(f"- Tasmota: {sum(len(v) for v in tasmota_scripts.values())}")
    print(f"- Bitshake: {sum(len(v) for v in bitshake_scripts.values())}")
    
    print(f"\n=== FERTIG ===")
    print(f"Finale Scripts: {len(merged_scripts)}")

if __name__ == "__main__":
    main()
