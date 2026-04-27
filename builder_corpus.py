import urllib.request
import json
import zipfile
import os

# لیست چندین سرور و مخزن (Mirror) برای تضمین دانلود شدن فایل
CORPUS_URLS = [
    # مخازن مختلف با در نظر گرفتن حروف کوچک/بزرگ و شاخه‌های main/master
    "https://raw.githubusercontent.com/habibiefadzli/quranic-corpus/main/quranic-corpus-morphology-0.4.txt",
    "https://raw.githubusercontent.com/kaisdu/quranic-corpus/master/quranic-corpus-morphology-0.4.txt",
    "https://raw.githubusercontent.com/fawazahmed0/quran-corpus/master/quranic-corpus-morphology-0.4.txt",
    "https://raw.githubusercontent.com/gnu-tariq/quranic-corpus/master/quranic-corpus-morphology-0.4.txt",
    "https://raw.githubusercontent.com/risan/quran-corpus/main/src/data/quranic-corpus-morphology-0.4.txt",
    # لینک مستقیم آرشیو با ساختار متفاوت
    "https://web.archive.org/web/20220101000000id_/http://corpus.quran.com/download/quranic-corpus-morphology-0.4.txt"
]


OUTPUT_JSON = "quranic_grammar_corpus.json"

print("Downloading Quranic Corpus data...")
lines = None

# تلاش برای دانلود از لینک‌های مختلف
for url in CORPUS_URLS:
    try:
        print(f"Trying to download from: {url}")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            lines = response.read().decode('utf-8').splitlines()
        print("Download successful!")
        break  # خروج از حلقه در صورت موفقیت
    except Exception as e:
        print(f"Failed to download from this URL. Error: {e}")

if not lines:
    raise Exception("Critical Error: All mirror links failed. Cannot download Corpus data.")

corpus_dict = {}

print("Parsing morphology and grammar data...")
for line in lines:
    line = line.strip()
    # نادیده گرفتن خطوط خالی، کامنت‌ها و هدر
    if not line or line.startswith('#') or line.startswith('LOCATION'):
        continue
    
    parts = line.split('\t')
    if len(parts) < 4:
        continue
        
    location = parts[0] # فرمت: (Chapter:Verse:Word:Segment)
    form = parts[1]
    tag = parts[2]
    features = parts[3]
    
    # پردازش موقعیت (سوره، آیه، کلمه)
    loc_parts = location.strip('()').split(':')
    if len(loc_parts) >= 3:
        chapter, verse, word = loc_parts[0], loc_parts[1], loc_parts[2]
        
        if chapter not in corpus_dict:
            corpus_dict[chapter] = {}
        if verse not in corpus_dict[chapter]:
            corpus_dict[chapter][verse] = {}
        if word not in corpus_dict[chapter][verse]:
            corpus_dict[chapter][verse][word] = []
            
        corpus_dict[chapter][verse][word].append({
            "segment_form": form,
            "pos_tag": tag,          # نقش کلمه (اسم، فعل، حرف و ...)
            "grammar_features": features # ریشه کلمه و سایر ویژگی‌های گرامری
        })

print("Saving parsed corpus to JSON...")
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(corpus_dict, f, ensure_ascii=False)

print("Zipping Corpus database...")
with zipfile.ZipFile("quran_corpus_db.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
    zipf.write(OUTPUT_JSON)

print("Corpus database ready: quran_corpus_db.zip")
