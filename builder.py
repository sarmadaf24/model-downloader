import os
import requests
import json
import time

# ==========================================
# Configuration
# ==========================================
BASE_URL = "http://api.alquran.cloud/v1"
EDITIONS_URL = f"{BASE_URL}/edition"

# Target Arabic Scripts based on your request
TARGET_ARABIC_SCRIPTS = [
    "quran-uthmani",       # عثمانی استاندارد
    "quran-uthmani-min",   # عثمانی بدون علائم اضافی
    "quran-simple",        # ساده/املایی با اعراب
    "quran-simple-min",    # ساده/املایی بدون اعراب
    "quran-indopak"        # هندی-پاکستانی
]

FONTS = {
    "KFGQPC_Uthmanic_Script.ttf": "https://raw.githubusercontent.com/quran/quran.com-images/master/fonts/KFGQPC_Uthmanic_Script_HAFS_Regular.ttf",
    "Me_Quran.ttf": "https://raw.githubusercontent.com/quran/quran.com-images/master/fonts/me_quran.ttf",
    "IndoPak.ttf": "https://raw.githubusercontent.com/quran/quran.com-images/master/fonts/IndoPak.ttf"
}

# ==========================================
# Create Directory Structure
# ==========================================
dirs = [
    "data/texts/individual",
    "data/translations/individual",
    "data/transliterations/individual",
    "data/merged",
    "fonts"
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ==========================================
# Fetch all available editions dynamically
# ==========================================
print("Fetching list of all available editions from API...")
editions_response = requests.get(EDITIONS_URL).json()
all_editions = editions_response['data']

translations = [e['identifier'] for e in all_editions if e['format'] == 'text' and e['type'] == 'translation']
transliterations = [e['identifier'] for e in all_editions if e['format'] == 'text' and e['type'] == 'transliteration']

print(f"Found {len(TARGET_ARABIC_SCRIPTS)} Arabic texts, {len(translations)} translations, and {len(transliterations)} transliterations.")

# ==========================================
# Global Aggregated Database Dictionary
# ==========================================
# Structure: full_db[surah][ayah] = {"texts": {}, "translations": {}, "transliterations": {}}
full_db = {s: {a: {"texts": {}, "translations": {}, "transliterations": {}} for a in range(1, 287)} for s in range(1, 115)}

def download_edition(identifier, folder, category_key):
    url = f"{BASE_URL}/quran/{identifier}"
    print(f"Downloading {identifier}...")
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"  -> Failed to download {identifier}")
            return
        
        data = response.json()['data']
        individual_data = []
        
        for surah in data['surahs']:
            s_num = surah['number']
            for ayah in surah['ayahs']:
                a_num = ayah['numberInSurah']
                text = ayah['text']
                
                # Add to individual file list
                individual_data.append({
                    "surah": s_num,
                    "ayah": a_num,
                    "text": text
                })
                
                # Add to aggregated DB
                if a_num in full_db[s_num]:
                    full_db[s_num][a_num][category_key][identifier] = text

        # Save individual file
        filepath = f"data/{folder}/individual/{identifier}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(individual_data, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"  -> Error processing {identifier}: {e}")
    
    # Sleep briefly to avoid overwhelming the API
    time.sleep(0.5)

# 1. Download Arabic Texts
for script in TARGET_ARABIC_SCRIPTS:
    download_edition(script, "texts", "texts")

# 2. Download ALL Translations
for trans in translations:
    download_edition(trans, "translations", "translations")

# 3. Download ALL Transliterations
for trans in transliterations:
    download_edition(trans, "transliterations", "transliterations")

# ==========================================
# Save Aggregated Database
# ==========================================
print("Saving aggregated database...")
with open("data/merged/quran_full_db.json", 'w', encoding='utf-8') as f:
    json.dump(full_db, f, ensure_ascii=False, indent=2)

# ==========================================
# Download Fonts
# ==========================================
for name, url in FONTS.items():
    print(f"Downloading font {name}...")
    try:
        r = requests.get(url)
        with open(f"fonts/{name}", 'wb') as f:
            f.write(r.content)
    except:
        print(f"Failed to download {name}")

print("\nPhase 1 (Comprehensive) processing completed!")
