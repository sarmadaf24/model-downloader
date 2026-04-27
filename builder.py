import os
import requests
import json

# ==========================================
# Configuration and Sources
# ==========================================

# Using AlQuran.cloud API which provides clean verified Tanzil texts
TEXTS = {
    "uthmani": "http://api.alquran.cloud/v1/quran/quran-uthmani",
    "simple": "http://api.alquran.cloud/v1/quran/quran-simple",
}

TRANSLATIONS = {
    "en_sahih": "http://api.alquran.cloud/v1/quran/en.sahih",
    "fa_fooladvand": "http://api.alquran.cloud/v1/quran/fa.fooladvand"
}

FONTS = {
    "KFGQPC_Uthmanic_Script.ttf": "https://raw.githubusercontent.com/quran/quran.com-images/master/fonts/KFGQPC_Uthmanic_Script_HAFS_Regular.ttf",
    "Me_Quran.ttf": "https://raw.githubusercontent.com/quran/quran.com-images/master/fonts/me_quran.ttf"
}

# ==========================================
# Create Directory Structure
# ==========================================
directories = [
    "data/texts/individual",
    "data/translations/individual",
    "fonts"
]

for directory in directories:
    os.makedirs(directory, exist_ok=True)
    print(f"Directory ready: {directory}")

# ==========================================
# Download and Format Text & Translations
# ==========================================
def fetch_and_save_quran_api(url, filepath):
    print(f"Fetching data from {url}...")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch {url}")
        return

    data = response.json()
    output = []
    
    # Flatten the API response into a clean JSON array
    for surah in data['data']['surahs']:
        for ayah in surah['ayahs']:
            output.append({
                "surah": surah['number'],
                "ayah": ayah['numberInSurah'],
                "text": ayah['text']
            })
            
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"Saved successfully to {filepath}")

# Fetch Arabic Texts
for name, url in TEXTS.items():
    fetch_and_save_quran_api(url, f"data/texts/individual/{name}.json")

# Fetch Translations
for name, url in TRANSLATIONS.items():
    fetch_and_save_quran_api(url, f"data/translations/individual/{name}.json")

# ==========================================
# Download Fonts
# ==========================================
for name, url in FONTS.items():
    print(f"Downloading font {name}...")
    r = requests.get(url)
    if r.status_code == 200:
        with open(f"fonts/{name}", 'wb') as f:
            f.write(r.content)
        print(f"Saved font: {name}")
    else:
        print(f"Failed to download font {name}")

print("\nPhase 1 Data processing completed successfully!")

