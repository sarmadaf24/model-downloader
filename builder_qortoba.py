import os
import glob
import json
import zipfile
import xmltodict
import shutil

REPO_URL = "https://github.com/qortoba/tafsirs.git"
CLONE_DIR = "qortoba_tafsirs_repo"
OUTPUT_ZIP = "qortoba_tafsirs_db.zip"

def process_qortoba():
    # 1. Clone the repository if it doesn't exist
    if not os.path.exists(CLONE_DIR):
        print(f"Cloning repository: {REPO_URL}...")
        os.system(f"git clone {REPO_URL} {CLONE_DIR}")
    
    tafsir_data = {}
    
    # 2. Find all directories (tafsirs) in the cloned repo
    # تغییر مسیر پایه به پوشه content
    base_path = os.path.join(CLONE_DIR, "content")
    if not os.path.exists(base_path):
        # اگر content پیدا نشد، در خود روت بگرد
        base_path = CLONE_DIR 

    directories = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d)) and not d.startswith('.')]
    
    print(f"Found {len(directories)} potential tafsir directories in {base_path}.")
    
    for tafsir_name in directories:
        tafsir_dir = os.path.join(base_path, tafsir_name)
        # جستجو در تمام زیرپوشه‌ها برای فایل‌های xml در صورت نیاز، یا فقط در خود پوشه تفسیر
        xml_files = glob.glob(os.path.join(tafsir_dir, "*.xml"))
        
        tafsir_content = []
        for xml_file in xml_files:
            # نادیده گرفتن فایل‌های نامرتبط
            if "front.xml" in xml_file.lower():
                continue
                
            try:
                with open(xml_file, 'r', encoding='utf-8') as f:
                    xml_string = f.read()
                    parsed_dict = xmltodict.parse(xml_string)
                    tafsir_content.append({
                        "file_name": os.path.basename(xml_file),
                        "content": parsed_dict
                    })
            except Exception as e:
                print(f"Error parsing {xml_file}: {e}")
                
        if tafsir_content:
            tafsir_data[tafsir_name] = tafsir_content
            print(f"  -> Successfully processed: {tafsir_name} ({len(tafsir_content)} files)")
        else:
            print(f"  -> No valid XML data found for: {tafsir_name}")

    if not tafsir_data:
        print("Warning: No tafsirs were processed. Check XML parsing logic or directory structure.")
        return

    # 3. Save to JSON and ZIP
    print("Creating final JSON and ZIP files...")
    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for tafsir, content in tafsir_data.items():
            json_filename = f"{tafsir}.json"
            json_str = json.dumps(content, ensure_ascii=False, indent=2)
            zipf.writestr(json_filename, json_str)
            
    print(f"Successfully created {OUTPUT_ZIP}")

if __name__ == "__main__":
    process_qortoba()
