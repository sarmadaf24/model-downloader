import urllib.request
import json
import zipfile
import os

# Using a reliable GitHub mirror for the Quranic Corpus morphology file
CORPUS_URL = "https://raw.githubusercontent.com/habibiefadzli/quranic-corpus/master/quranic-corpus-morphology-0.4.txt"
OUTPUT_JSON = "quranic_grammar_corpus.json"

print("Downloading Quranic Corpus data...")
req = urllib.request.Request(CORPUS_URL, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    lines = response.read().decode('utf-8').splitlines()

corpus_dict = {}

print("Parsing morphology and grammar data...")
for line in lines:
    line = line.strip()
    if not line or line.startswith('#') or line.startswith('LOCATION'):
        continue
    
    parts = line.split('\t')
    if len(parts) < 4:
        continue
        
    location = parts[0] # Format: (Chapter:Verse:Word:Segment)
    form = parts[1]
    tag = parts[2]
    features = parts[3]
    
    # Parse location
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
            "pos_tag": tag,          # Part of Speech (Noun, Verb, etc)
            "grammar_features": features # Root, gender, number, case, etc
        })

print("Saving parsed corpus to JSON...")
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(corpus_dict, f, ensure_ascii=False)

print("Zipping Corpus database...")
with zipfile.ZipFile("quran_corpus_db.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
    zipf.write(OUTPUT_JSON)

print("Corpus database ready: quran_corpus_db.zip")
