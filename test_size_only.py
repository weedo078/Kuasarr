#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

def extract_size_from_text(text):
    """
    Erweiterte Größenextraktion aus verschiedenen Text-Formaten
    Basierend auf den HTML-Beispielen von data-load.me
    """
    if not text:
        return {"size": 0, "sizeunit": "B"}
    
    # Normalisiere den Text für bessere Erkennung
    text = text.strip()
    
    print(f"[TEST] Analysiere Text: {text[:200]}...")
    
    # SPEZIAL-CHECK: Multi-Größen Format mit "je" - Muss ZUERST kommen!
    if "je " in text.lower():
        all_sizes = re.findall(r'(\d+(?:[.,]\d+)?)\s*([KMGT]?i?B)', text, re.IGNORECASE)
        if len(all_sizes) > 1:
            # Konvertiere alle zu MB und nehme die größte
            best_size = 0
            best_unit = "B"
            best_original = 0
            
            for size_str, unit in all_sizes:
                size = float(size_str.replace(',', '.'))
                clean_unit = unit.upper().replace('IB', 'B')
                
                # Konvertiere zu MB für Vergleich
                mb_value = size
                if clean_unit == "KB":
                    mb_value = size / 1024
                elif clean_unit == "GB":
                    mb_value = size * 1024
                elif clean_unit == "TB":
                    mb_value = size * 1024 * 1024
                
                if mb_value > best_size:
                    best_size = mb_value
                    best_unit = clean_unit
                    best_original = size
            
            if best_size > 0:
                print(f"[TEST] Multi-Format mit 'je' gefunden: {best_original} {best_unit} (größte von {len(all_sizes)} Größen)")
                return {"size": best_original, "sizeunit": best_unit}
    
    # Methode 1: MediaInfo "File size" Format aus Code-Blöcken
    # "File size                                : 926 MiB"
    size_match = re.search(r'File\s+size\s*[:：]\s*(\d+(?:[.,]\d+)?)\s*([KMGT]?i?B)', text, re.IGNORECASE)
    if size_match:
        size_str = size_match.group(1).replace(',', '.')
        size = float(size_str)
        unit = size_match.group(2).upper().replace('IB', 'B')  # MiB -> MB
        print(f"[TEST] MediaInfo File size gefunden: {size} {unit}")
        return {"size": size, "sizeunit": unit}
    
    # Methode 2: "FileSize" Format mit Punkten
    # "FileSize......: 6.66 GiB"
    size_match = re.search(r'FileSize[.\s]*[:：]\s*(\d+(?:[.,]\d+)?)\s*([KMGT]?i?B)', text, re.IGNORECASE)
    if size_match:
        size_str = size_match.group(1).replace(',', '.')
        size = float(size_str)
        unit = size_match.group(2).upper().replace('IB', 'B')  # GiB -> GB
        print(f"[TEST] FileSize-Format gefunden: {size} {unit}")
        return {"size": size, "sizeunit": unit}
    
    # Methode 3: Einfaches "size:" Format
    # "size: 2.0 GiB"
    size_match = re.search(r'\bsize\s*[:：]\s*(\d+(?:[.,]\d+)?)\s*([KMGT]?i?B)', text, re.IGNORECASE)
    if size_match:
        size_str = size_match.group(1).replace(',', '.')
        size = float(size_str)
        unit = size_match.group(2).upper().replace('IB', 'B')
        print(f"[TEST] Size-Format gefunden: {size} {unit}")
        return {"size": size, "sizeunit": unit}
    
    # Methode 4: "Größe" oder "Grösse" Format (deutsche Varianten)
    # "Grösse.............: je 721 MB 1,23 GB" oder "Größe: 5.67 GB"
    # WICHTIG: Bei "je" Format mit mehreren Größen, gehe zu Multi-Format
    size_match = re.search(r'Gr[öo](?:ss|ß)e[.\s]*[:：]\s*(?!je\s)(\d+(?:[.,]\d+)?)\s*([KMGT]?i?B)', text, re.IGNORECASE)
    if size_match:
        size_str = size_match.group(1).replace(',', '.')
        size = float(size_str)
        unit = size_match.group(2).upper().replace('IB', 'B')
        print(f"[TEST] Größe-Format gefunden: {size} {unit}")
        return {"size": size, "sizeunit": unit}
    
    # Methode 5: Standard Format ohne Doppelpunkt
    # "123 MB" oder "123.45 GB"
    size_match = re.search(r'\b(\d+(?:[.,]\d+)?)\s*([KMGT]?i?B)\b', text, re.IGNORECASE)
    if size_match:
        size_str = size_match.group(1).replace(',', '.')
        size = float(size_str)
        unit = size_match.group(2).upper().replace('IB', 'B')
        print(f"[TEST] Standard-Format gefunden: {size} {unit}")
        return {"size": size, "sizeunit": unit}
    
    # Methode 6: Größe in Klammern oder als separater Text
    # "[123 MB]" oder "(1.5 GB)"
    size_match = re.search(r'[\[\(](\d+(?:[.,]\d+)?)\s*([KMGT]?i?B)[\]\)]', text, re.IGNORECASE)
    if size_match:
        size_str = size_match.group(1).replace(',', '.')
        size = float(size_str)
        unit = size_match.group(2).upper().replace('IB', 'B')
        print(f"[TEST] Klammer-Format gefunden: {size} {unit}")
        return {"size": size, "sizeunit": unit}
    
    # Methode 7: Spezielle Formate mit HTML-Tags
    # Entferne HTML-Tags für bessere Erkennung
    clean_text = re.sub(r'<[^>]+>', ' ', text)
    if clean_text != text:
        print(f"[TEST] Versuche nochmal ohne HTML-Tags")
        return extract_size_from_text(clean_text)
    
    # Methode 8: Multi-Größen Format (nehme die erste größere Größe)
    # "je 721 MB 1,23 GB" - nehme 1,23 GB
    all_sizes = re.findall(r'(\d+(?:[.,]\d+)?)\s*([KMGT]?i?B)', text, re.IGNORECASE)
    if all_sizes:
        # Konvertiere alle zu MB und nehme die größte
        best_size = 0
        best_unit = "B"
        best_original = 0
        
        for size_str, unit in all_sizes:
            size = float(size_str.replace(',', '.'))
            clean_unit = unit.upper().replace('IB', 'B')
            
            # Konvertiere zu MB für Vergleich
            mb_value = size
            if clean_unit == "KB":
                mb_value = size / 1024
            elif clean_unit == "GB":
                mb_value = size * 1024
            elif clean_unit == "TB":
                mb_value = size * 1024 * 1024
            
            if mb_value > best_size:
                best_size = mb_value
                best_unit = clean_unit
                best_original = size
        
        if best_size > 0:
            print(f"[TEST] Multi-Format gefunden: {best_original} {best_unit} (größte von {len(all_sizes)} Größen)")
            return {"size": best_original, "sizeunit": best_unit}
    
    # Fallback: Keine Größe gefunden
    print(f"[TEST] Keine Größenangabe gefunden in: {text[:100]}...")
    return {"size": 0, "sizeunit": "B"}


def test_all_examples():
    """Teste alle HTML-Beispiele vom Nutzer"""
    
    print("=== TESTE GRÖSSEN-EXTRAKTION MIT REALEN HTML-BEISPIELEN ===\n")
    
    test_cases = [
        # Beispiel 1: MediaInfo Block
        {
            "name": "MediaInfo File size",
            "text": "File size                                : 926 MiB",
            "expected": "926 MB"
        },
        # Beispiel 2: FileSize mit Punkten
        {
            "name": "FileSize mit Punkten",
            "text": "FileSize......: 6.66 GiB",
            "expected": "6.66 GB"
        },
        # Beispiel 3: Size in Code Block
        {
            "name": "Size in Code Block",
            "text": "size: 2.0 GiB",
            "expected": "2 GB"
        },
        # Beispiel 4: Multi-Größen mit je
        {
            "name": "Multi-Größen Format",
            "text": "Grösse.............: je 721 MB 1,23 GB",
            "expected": "1.23 GB"
        },
        # Beispiel 5: HTML Größe
        {
            "name": "HTML Größe",
            "text": "Sprache: Deutsch | Format: MKV | Größe: 5.67 GB | Laufzeit: 0:52:38 Std",
            "expected": "5.67 GB"
        },
        # Beispiel 6: Kompletter MediaInfo Block
        {
            "name": "Kompletter MediaInfo",
            "text": """Format                                   : Matroska
Format version                           : Version 4
File size                                : 926 MiB
Duration                                 : 48 min 40 s
Overall bit rate                         : 2 660 kb/s""",
            "expected": "926 MB"
        },
        # Beispiel 7: Quote Block mit FileSize
        {
            "name": "Quote Block FileSize",
            "text": """Filename......: American.Primeval.S01E01.GERMAN.DL.2160p.EAC3D.DV.HDR.WEB.H265-iND.mkv 
Video Source.........: tnx@HHWEB
Audio Source.........: tnx@SAUERKRAUT
FileSize......: 6.66 GiB 
Duration......: 48 min 40 s""",
            "expected": "6.66 GB"
        }
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"Input: {test_case['text'][:80]}...")
        print()
        
        result = extract_size_from_text(test_case['text'])
        # Formatiere das Ergebnis als String (ohne .0 für ganze Zahlen)
        if result['size'] == int(result['size']):
            result_str = f"{int(result['size'])} {result['sizeunit']}"
        else:
            result_str = f"{result['size']} {result['sizeunit']}"
        
        success = result_str == test_case['expected']
        
        print(f"Ergebnis: {result_str}")
        print(f"Erwartet: {test_case['expected']}")
        print(f"Status: {'✅ ERFOLG' if success else '❌ FEHLER'}")
        print("=" * 80)
        print()
        
        if success:
            success_count += 1
    
    print(f"ZUSAMMENFASSUNG:")
    print(f"Erfolgreiche Tests: {success_count}/{total_count}")
    print(f"Erfolgsquote: {(success_count/total_count)*100:.1f}%")
    
    if success_count == total_count:
        print("🎉 ALLE TESTS ERFOLGREICH!")
        print("Die verbesserte Größenextraktion funktioniert mit allen HTML-Beispielen.")
    else:
        print("⚠️  EINIGE TESTS FEHLGESCHLAGEN!")
        print("Die Größenextraktion benötigt weitere Anpassungen.")


if __name__ == "__main__":
    test_all_examples() 