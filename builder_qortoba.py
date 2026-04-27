import os
import json
import zipfile
import subprocess
import shutil
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

# --- Configuration ---
REPO_URL = "https://github.com/qortoba/tafsirs.git"
CLONE_DIR = "qortoba_tafsirs_repo"
OUTPUT_JSON = "qortoba_tafsirs_db.json"
OUTPUT_ZIP = "qortoba_tafsirs_db.zip"

def clone_repo():
    print(f"Cloning repository: {REPO_URL}...")
    if os.path.exists(CLONE_DIR):
        shutil.rmtree(CLONE_DIR)
    subprocess.run(["git", "clone", "--depth", "1", REPO_URL, CLONE_DIR], check=True, capture_output=True, text=True)
    print("Repository cloned successfully.")

def parse_sura_xml(sura_path):
    try:
        tree = ET.parse(sura_path)
        root = tree.getroot()
        sura_node = root.find("sura")
        if sura_node is None:
            return None, {}
        sura_index = sura_node.get("index")
        ayahs = {ayah.get("index"): ayah.get("text") for ayah in sura_node.findall("aya") if ayah.get("index") and ayah.get("text")}
        return sura_index, ayahs
    except Exception:
        return None, {}

def process_tafsir_dir(tafsir_dir_name):
    tafsir_path = os.path.join(CLONE_DIR, tafsir_dir_name)
    # Skip non-directories or hidden github folders
    if not os.path.isdir(tafsir_path) or tafsir_dir_name.startswith('.'):
        return None

    # Find all XML files that look like suras (e.g., 001.xml)
    sura_files = [f for f in os.listdir(tafsir_path) if f.endswith('.xml') and not f.lower().startswith('meta')]
    
    if not sura_files:
        return None

    print(f"  -> Processing tafsir: {tafsir_dir_name}")
    tafsir_data = {"tafsir": {}}

    for sura_file in sura_files:
        sura_path = os.path.join(tafsir_path, sura_file)
        sura_index, ayahs = parse_sura_xml(sura_path)
        if sura_index and ayahs:
            tafsir_data["tafsir"][sura_index] = ayahs
    
    return tafsir_dir_name, tafsir_data

def main():
    try:
        clone_repo()
        all_tafsirs = {}
        tafsir_dirs = os.listdir(CLONE_DIR)

        print("Starting parallel processing of tafsir directories...")
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            results = executor.map(process_tafsir_dir, tafsir_dirs)

        for result in results:
            if result:
                tafsir_id, tafsir_data = result
                all_tafsirs[tafsir_id] = tafsir_data
        
        print(f"Successfully processed {len(all_tafsirs)} tafsirs from Qortoba.")

        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(all_tafsirs, f, ensure_ascii=False, indent=2)
        
        with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(OUTPUT_JSON)

    finally:
        if os.path.exists(CLONE_DIR):
            shutil.rmtree(CLONE_DIR)
        if os.path.exists(OUTPUT_JSON):
            os.remove(OUTPUT_JSON)

if __name__ == "__main__":
    main()
