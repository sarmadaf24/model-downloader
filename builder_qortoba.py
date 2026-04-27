# File: builder_qortoba.py

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
    """Clones the specified git repository into the CLONE_DIR."""
    print(f"Cloning repository: {REPO_URL}...")
    if os.path.exists(CLONE_DIR):
        print(f"Removing existing directory: {CLONE_DIR}")
        shutil.rmtree(CLONE_DIR)
    # Using --depth 1 for a shallow clone to save time and space
    subprocess.run(["git", "clone", "--depth", "1", REPO_URL, CLONE_DIR], check=True)
    print("Repository cloned successfully.")

def parse_sura_xml(sura_path):
    """Parses a single Sura XML file and extracts ayahs."""
    try:
        tree = ET.parse(sura_path)
        root = tree.getroot()
        sura_node = root.find("sura")
        if sura_node is None:
            return None, {}
        sura_index = sura_node.get("index")
        ayahs = {ayah.get("index"): ayah.get("text") for ayah in sura_node.findall("aya") if ayah.get("index") and ayah.get("text")}
        return sura_index, ayahs
    except ET.ParseError as e:
        print(f"  [Warning] Could not parse XML file: {os.path.basename(sura_path)}. Error: {e}")
        return None, {}
    except Exception as e:
        print(f"  [Error] An unexpected error occurred while processing {os.path.basename(sura_path)}. Error: {e}")
        return None, {}

def process_tafsir_dir(tafsir_dir_name):
    """Processes a single tafsir directory, parsing all its Sura XML files."""
    tafsir_path = os.path.join(CLONE_DIR, 'content', tafsir_dir_name)
    
    # Skip non-directories or hidden folders
    if not os.path.isdir(tafsir_path) or tafsir_dir_name.startswith('.'):
        return None

    # Find all XML files that look like suras (e.g., abdu_001.xml)
    sura_files = [f for f in os.listdir(tafsir_path) if f.endswith('.xml') and f != "front.xml"]
    
    if not sura_files:
        return None

    print(f"  -> Processing tafsir: {tafsir_dir_name}")
    tafsir_data = {"sura": {}}

    for sura_file in sura_files:
        sura_path = os.path.join(tafsir_path, sura_file)
        sura_index, ayahs = parse_sura_xml(sura_path)
        if sura_index and ayahs:
            tafsir_data["sura"][sura_index] = ayahs
    
    # Return tafsir data only if it contains any processed suras
    if tafsir_data["sura"]:
        return tafsir_dir_name, tafsir_data
    return None

def main():
    """Main function to orchestrate the cloning, processing, and packaging."""
    try:
        clone_repo()
        all_tafsirs = {}
        # The actual tafsir folders are inside the 'content' directory
        content_path = os.path.join(CLONE_DIR, 'content')
        if not os.path.exists(content_path):
            print(f"Error: 'content' directory not found in the cloned repository.")
            return

        tafsir_dirs = os.listdir(content_path)
        print(f"Found {len(tafsir_dirs)} potential tafsir directories. Starting parallel processing...")

        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            results = executor.map(process_tafsir_dir, tafsir_dirs)

        for result in results:
            if result:
                tafsir_id, tafsir_data = result
                all_tafsirs[tafsir_id] = tafsir_data
        
        if not all_tafsirs:
            print("Warning: No tafsirs were processed. The output file will be empty.")
        else:
            print(f"Successfully processed {len(all_tafsirs)} tafsirs from Qortoba.")

        print("Creating final JSON and ZIP files...")
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(all_tafsirs, f, ensure_ascii=False) # Removed indent for smaller file size
        
        with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            zf.write(OUTPUT_JSON)
        
        print(f"Successfully created {OUTPUT_ZIP}")

    finally:
        # Cleanup
        print("Cleaning up temporary files and directories...")
        if os.path.exists(CLONE_DIR):
            shutil.rmtree(CLONE_DIR)
        if os.path.exists(OUTPUT_JSON):
            os.remove(OUTPUT_JSON)

if __name__ == "__main__":
    main()
