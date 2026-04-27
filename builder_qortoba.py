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
    """Clones the specified git repository with minimal depth."""
    print(f"Cloning repository: {REPO_URL}...")
    if os.path.exists(CLONE_DIR):
        print("Repository already exists. Removing old directory.")
        shutil.rmtree(CLONE_DIR)
    
    # Use --depth 1 for a shallow clone to save time and space in CI/CD
    subprocess.run(
        ["git", "clone", "--depth", "1", REPO_URL, CLONE_DIR], 
        check=True,
        capture_output=True,
        text=True
    )
    print("Repository cloned successfully.")

def parse_metadata(tafsir_path):
    """Parses the metadata.xml file for a given tafsir."""
    metadata_file = os.path.join(tafsir_path, "metadata.xml")
    if not os.path.exists(metadata_file):
        return {}
    
    tree = ET.parse(metadata_file)
    root = tree.getroot()
    metadata = {
        "title": root.findtext("book_name", "N/A"),
        "author": root.findtext("author_name", "N/A"),
        "year": root.findtext("death", "N/A"),
    }
    return metadata

def parse_sura_xml(sura_path):
    """Parses a single sura XML file and returns a dictionary of ayahs."""
    try:
        tree = ET.parse(sura_path)
        root = tree.getroot()
        sura_node = root.find("sura")
        if sura_node is None:
            return None, {}
            
        sura_index = sura_node.get("index")
        ayahs = {
            ayah.get("index"): ayah.get("text")
            for ayah in sura_node.findall("aya")
            if ayah.get("index") and ayah.get("text")
        }
        return sura_index, ayahs
    except ET.ParseError:
        print(f"Warning: Could not parse {sura_path}")
        return None, {}

def process_tafsir_dir(tafsir_dir_name):
    """Processes a single tafsir directory."""
    tafsir_path = os.path.join(CLONE_DIR, tafsir_dir_name)
    if not os.path.isdir(tafsir_path) or not os.path.exists(os.path.join(tafsir_path, "metadata.xml")):
        return None

    print(f"  -> Processing tafsir: {tafsir_dir_name}")
    tafsir_data = {
        "metadata": parse_metadata(tafsir_path),
        "tafsir": {}
    }

    # Find all sura files (e.g., 001.xml, 002.xml ...)
    sura_files = [f for f in os.listdir(tafsir_path) if f.endswith('.xml') and f != 'metadata.xml']
    
    for sura_file in sura_files:
        sura_path = os.path.join(tafsir_path, sura_file)
        sura_index, ayahs = parse_sura_xml(sura_path)
        if sura_index and ayahs:
            tafsir_data["tafsir"][sura_index] = ayahs
    
    return tafsir_dir_name, tafsir_data


def main():
    """Main function to orchestrate the process."""
    try:
        clone_repo()

        all_tafsirs = {}
        # List all potential tafsir directories
        tafsir_dirs = os.listdir(CLONE_DIR)

        # Using ThreadPoolExecutor to process tafsirs in parallel
        print("Starting parallel processing of tafsir directories...")
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            results = executor.map(process_tafsir_dir, tafsir_dirs)

        for result in results:
            if result:
                tafsir_id, tafsir_data = result
                all_tafsirs[tafsir_id] = tafsir_data
        
        print(f"Successfully processed {len(all_tafsirs)} tafsirs.")

        # Save to a single JSON file
        print(f"Saving combined data to {OUTPUT_JSON}...")
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(all_tafsirs, f, ensure_ascii=False, indent=2)
        
        # Compress the JSON file
        print(f"Compressing data to {OUTPUT_ZIP}...")
        with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(OUTPUT_JSON)
        
        print("Compression complete.")

    finally:
        # Clean up by removing the large intermediate files and directories
        print("Cleaning up...")
        if os.path.exists(CLONE_DIR):
            shutil.rmtree(CLONE_DIR)
        if os.path.exists(OUTPUT_JSON):
            os.remove(OUTPUT_JSON)
        print("Cleanup finished. Final artifact is ready.")

if __name__ == "__main__":
    main()

