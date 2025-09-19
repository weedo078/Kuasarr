#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test für verbesserte DL Parsing-Funktionen
Testet das neue Alter- und Größen-Parsing basierend auf HTML-Beispielen
"""

import sys
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup

# Füge Quasarr-Module hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'quasarr'))

from quasarr.search.sources.dl import extract_size_from_text, parse_date_from_html

def extract_size_from_text(text):
    """
    Erweiterte Größenextraktion aus verschiedenen Text-Formaten
    Basierend auf den HTML-Beispielen von data-load.me
    """
    if not text:
        return {"size": 0, "sizeunit": "B"}
    
    # Methode 1: Standard Format "123 MB" oder "123.45 GB"
    size_match = re.search(r'(\d+(?:[.,]\d+)?)\s*([KMGT]?B)', text, re.IGNORECASE)
    if size_match:
        size_str = size_match.group(1).replace(',', '.')  # Deutsche Dezimalstellen
        size = float(size_str)
        unit = size_match.group(2).upper()
        print(f"[TEST-SIZE] Standard-Format gefunden: {size} {unit}")
        return {"size": size, "sizeunit": unit}
    
    # Methode 2: Größe im Format "Dateigröße: 792 MiB" (MediaInfo Format)
    size_match = re.search(r'Dateigröße\s*[:：]\s*(\d+(?:[.,]\d+)?)\s*([KMGT]?iB)', text, re.IGNORECASE)
    if size_match:
        size_str = size_match.group(1).replace(',', '.')
        size = float(size_str)
        unit = size_match.group(2).upper().replace('IB', 'B')  # MiB -> MB
        print(f"[TEST-SIZE] MediaInfo-Format gefunden: {size} {unit}")
        return {"size": size, "sizeunit": unit}
    
    # Methode 3: Größe im Format "FileSize......: 6.66 GiB"
    size_match = re.search(r'FileSize[.\s]*[:：]\s*(\d+(?:[.,]\d+)?)\s*([KMGT]?iB)', text, re.IGNORECASE)
    if size_match:
        size_str = size_match.group(1).replace(',', '.')
        size = float(size_str)
        unit = size_match.group(2).upper().replace('IB', 'B')  # GiB -> GB
        print(f"[TEST-SIZE] FileSize-Format gefunden: {size} {unit}")
        return {"size": size, "sizeunit": unit}
    
    # Methode 4: Größe in Klammern oder als separater Text
    size_match = re.search(r'[\[\(](\d+(?:[.,]\d+)?)\s*([KMGT]?B)[\]\)]', text, re.IGNORECASE)
    if size_match:
        size_str = size_match.group(1).replace(',', '.')
        size = float(size_str)
        unit = size_match.group(2).upper()
        print(f"[TEST-SIZE] Klammer-Format gefunden: {size} {unit}")
        return {"size": size, "sizeunit": unit}
    
    # Fallback: Keine Größe gefunden
    print(f"[TEST-SIZE] Keine Größenangabe gefunden in: {text[:100]}...")
    return {"size": 0, "sizeunit": "B"}


def parse_date_from_html(html_elem):
    """
    Erweiterte Datumsextraktion aus HTML-Elementen
    Basierend auf den HTML-Beispielen von data-load.me
    """
    if not html_elem:
        return None
    
    # Methode 1: <time> Element mit datetime Attribut
    time_elem = html_elem.find('time', class_='u-dt')
    if time_elem:
        datetime_str = time_elem.get('datetime')
        if datetime_str:
            try:
                # Parse ISO format: 2025-01-18T14:06:58+0100
                # Entferne Zeitzone-Info für einfaches Parsing
                if '+' in datetime_str:
                    datetime_clean = datetime_str.split('+')[0]
                elif datetime_str.count('-') > 2:  # Mehr als 2 Bindestriche = Zeitzone
                    datetime_clean = datetime_str.rsplit('-', 1)[0]
                else:
                    datetime_clean = datetime_str
                
                parsed_date = datetime.fromisoformat(datetime_clean)
                formatted_date = parsed_date.strftime('%a, %d %b %Y %H:%M:%S +0000')
                print(f"[TEST-DATE] Zeit-Element gefunden: {formatted_date} (von {datetime_str})")
                return formatted_date
            except Exception as e:
                print(f"[TEST-DATE] Fehler beim Parsen von datetime '{datetime_str}': {e}")
    
    # Methode 2: <time> Element mit data-time Attribut (Unix Timestamp)
    if time_elem and time_elem.get('data-time'):
        try:
            timestamp = int(time_elem.get('data-time'))
            parsed_date = datetime.fromtimestamp(timestamp)
            formatted_date = parsed_date.strftime('%a, %d %b %Y %H:%M:%S +0000')
            print(f"[TEST-DATE] Unix-Timestamp gefunden: {formatted_date} (von {timestamp})")
            return formatted_date
        except Exception as e:
            print(f"[TEST-DATE] Fehler beim Parsen von data-time: {e}")
    
    # Methode 3: Text-Datum im time Element
    if time_elem and time_elem.text:
        date_text = time_elem.text.strip()
        try:
            # Deutsche Datumsformate: "18 Januar 2025"
            if re.match(r'\d{1,2}\s+\w+\s+\d{4}', date_text):
                # Konvertiere deutsche Monatsnamen
                month_map = {
                    'Januar': 'January', 'Februar': 'February', 'März': 'March',
                    'April': 'April', 'Mai': 'May', 'Juni': 'June',
                    'Juli': 'July', 'August': 'August', 'September': 'September',
                    'Oktober': 'October', 'November': 'November', 'Dezember': 'December'
                }
                
                english_date = date_text
                for german, english in month_map.items():
                    english_date = english_date.replace(german, english)
                
                parsed_date = datetime.strptime(english_date, '%d %B %Y')
                formatted_date = parsed_date.strftime('%a, %d %b %Y %H:%M:%S +0000')
                print(f"[TEST-DATE] Text-Datum gefunden: {formatted_date} (von '{date_text}')")
                return formatted_date
        except Exception as e:
            print(f"[TEST-DATE] Fehler beim Parsen von Text-Datum '{date_text}': {e}")
    
    # Methode 4: Suche nach beliebigen time-Elementen im Element
    all_time_elems = html_elem.find_all('time')
    for time_elem in all_time_elems:
        result = parse_date_from_html(time_elem.parent if time_elem.parent else time_elem)
        if result:
            return result
    
    print("[TEST-DATE] Kein gültiges Datum gefunden")
    return None


def test_size_extraction():
    """Teste die verbesserte Größenextraktion mit den HTML-Beispielen vom Nutzer"""
    
    print("=== TEST: Größenextraktion ===\n")
    
    test_cases = [
        # Neue Formate aus den HTML-Beispielen
        {
            "name": "MediaInfo File size Format",
            "text": "File size                                : 926 MiB",
            "expected": {"size": 926.0, "sizeunit": "MB"}
        },
        {
            "name": "FileSize mit Punkten Format",
            "text": "FileSize......: 6.66 GiB",
            "expected": {"size": 6.66, "sizeunit": "GB"}
        },
        {
            "name": "Einfaches size Format",
            "text": "size: 2.0 GiB",
            "expected": {"size": 2.0, "sizeunit": "GB"}
        },
        {
            "name": "Größe Format mit je",
            "text": "Grösse.............: je 721 MB 1,23 GB",
            "expected": {"size": 1.23, "sizeunit": "GB"}  # Nimmt die größere Größe
        },
        {
            "name": "HTML Größe Format",
            "text": "<b>Größe:</b> 5.67 GB",
            "expected": {"size": 5.67, "sizeunit": "GB"}
        },
        # Komplexere Beispiele aus dem Thread-Content
        {
            "name": "MediaInfo Block komplett",
            "text": """
            Format                                   : Matroska
            Format version                           : Version 4
            File size                                : 926 MiB
            Duration                                 : 48 min 40 s
            Overall bit rate                         : 2 660 kb/s
            """,
            "expected": {"size": 926.0, "sizeunit": "MB"}
        },
        {
            "name": "FileSize in Quote Block",
            "text": """
            Filename......: American.Primeval.S01E01.GERMAN.DL.2160p.EAC3D.DV.HDR.WEB.H265-iND.mkv 
            Video Source.........: tnx@HHWEB
            Audio Source.........: tnx@SAUERKRAUT
            FileSize......: 6.66 GiB 
            Duration......: 48 min 40 s
            """,
            "expected": {"size": 6.66, "sizeunit": "GB"}
        },
        {
            "name": "Size in Code Block",
            "text": """
            American.Primeval.S01E01.GERMAN.DL.1080p.WEB.h264-SAUERKRAUT                   
                                            2025-01-09                                            
     title: Episode 1
      size: 2.0 GiB
   runtime: 00:48:40.667
            """,
            "expected": {"size": 2.0, "sizeunit": "GB"}
        }
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"Input: {test_case['text'][:60]}...")
        
        result = extract_size_from_text(test_case['text'])
        expected = test_case['expected']
        
        success = (abs(result['size'] - expected['size']) < 0.01 and 
                  result['sizeunit'] == expected['sizeunit'])
        
        print(f"Ergebnis: {result}")
        print(f"Erwartet: {expected}")
        print(f"Status: {'✅ ERFOLG' if success else '❌ FEHLER'}")
        print("-" * 60)
        
        if success:
            success_count += 1
    
    print(f"\n=== ZUSAMMENFASSUNG ===")
    print(f"Erfolgreiche Tests: {success_count}/{total_count}")
    print(f"Erfolgsquote: {(success_count/total_count)*100:.1f}%")
    
    return success_count == total_count

def test_html_size_extraction():
    """Teste die Größenextraktion direkt aus HTML-Elementen"""
    
    print("\n=== TEST: HTML-Größenextraktion ===\n")
    
    html_examples = [
        {
            "name": "bbCodeBlock-content mit MediaInfo",
            "html": """
            <div class="bbCodeBlock-content" dir="ltr">
                <pre class="bbCodeCode" dir="ltr" data-xf-init="code-block" data-lang="">
                    <code>
                    Format                                   : Matroska
                    Format version                           : Version 4
                    File size                                : 926 MiB
                    Duration                                 : 48 min 40 s
                    </code>
                </pre>
            </div>
            """,
            "expected": {"size": 926.0, "sizeunit": "MB"}
        },
        {
            "name": "Inline Größe mit HTML-Tags",
            "html": """
            <div style="text-align: center">
                <b>Sprache:</b> Deutsch | <b>Format:</b> MKV | <b>Größe:</b> 5.67 GB | <b>Laufzeit:</b> 0:52:38 Std
            </div>
            """,
            "expected": {"size": 5.67, "sizeunit": "GB"}
        }
    ]
    
    success_count = 0
    total_count = len(html_examples)
    
    for i, example in enumerate(html_examples, 1):
        print(f"HTML Test {i}: {example['name']}")
        
        soup = BeautifulSoup(example['html'], 'html.parser')
        text_content = soup.get_text()
        
        print(f"Extrahierter Text: {text_content[:100]}...")
        
        result = extract_size_from_text(text_content)
        expected = example['expected']
        
        success = (abs(result['size'] - expected['size']) < 0.01 and 
                  result['sizeunit'] == expected['sizeunit'])
        
        print(f"Ergebnis: {result}")
        print(f"Erwartet: {expected}")
        print(f"Status: {'✅ ERFOLG' if success else '❌ FEHLER'}")
        print("-" * 60)
        
        if success:
            success_count += 1
    
    print(f"\n=== HTML ZUSAMMENFASSUNG ===")
    print(f"Erfolgreiche Tests: {success_count}/{total_count}")
    print(f"Erfolgsquote: {(success_count/total_count)*100:.1f}%")
    
    return success_count == total_count

if __name__ == "__main__":
    print("Teste verbesserte DL-Größenextraktion mit realen HTML-Beispielen\n")
    
    success1 = test_size_extraction()
    success2 = test_html_size_extraction()
    
    print(f"\n=== GESAMTERGEBNIS ===")
    if success1 and success2:
        print("🎉 ALLE TESTS ERFOLGREICH!")
        print("Die verbesserte Größenextraktion funktioniert mit allen HTML-Beispielen.")
    else:
        print("⚠️  EINIGE TESTS FEHLGESCHLAGEN!")
        print("Die Größenextraktion benötigt weitere Anpassungen.")
    
    # Zeige auch ein Beispiel der Debug-Ausgabe
    print(f"\n=== DEBUG-BEISPIEL ===")
    test_text = "FileSize......: 6.66 GiB Duration......: 48 min 40 s"
    print(f"Test-Text: {test_text}")
    result = extract_size_from_text(test_text)
    print(f"Ergebnis: {result}") 