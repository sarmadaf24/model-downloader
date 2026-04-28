import urllib.request
import json
import os
import zipfile
import time

BASE_URL = "https://api.quran.com/api/v4"
OUTPUT_DIR = "tafsir_db"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

print("Fetching available tafsirs...")
tafsirs_info = fetch_json(f"{BASE_URL}/resources/tafsirs")['tafsirs']

# Save metadata
with open(os.path.join(OUTPUT_DIR, "tafsirs_metadata.json"), "w", encoding="utf-8") as f:
    json.dump(tafsirs_info, f, ensure_ascii=False, indent=2)

print(f"Found {len(tafsirs_info)} tafsirs. Starting download...")

for tafsir in tafsirs_info:
    tafsir_id = tafsir['id']
    tafsir_name = tafsir['slug']
    print(f"Downloading Tafsir: {tafsir_name} (ID: {tafsir_id})")
    
    # We will fetch tafsir for chapter 1 to 114
    tafsir_data = {}
    for chapter in range(1, 115):
        try:
            url = f"{BASE_URL}/quran/tafsirs/{tafsir_id}?chapter_number={chapter}"
            data = fetch_json(url)
            tafsir_data[f"chapter_{chapter}"] = data['tafsirs']
            time.sleep(0.5) # Prevent rate limiting
        except Exception as e:
            print(f"Error fetching chapter {chapter} for {tafsir_name}: {e}")
            
    file_path = os.path.join(OUTPUT_DIR, f"{tafsir_name}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(tafsir_data, f, ensure_ascii=False)

print("Zipping Tafsir database...")
with zipfile.ZipFile("quran_tafsir_db.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, _, files in os.walk(OUTPUT_DIR):
        for file in files:
            zipf.write(os.path.join(root, file), arcname=file)

print("Tafsir database ready: quran_tafsir_db.zip")

