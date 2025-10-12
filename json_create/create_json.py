import os
import json
import pandas as pd
import requests
import time
from tqdm import tqdm
import requests
from dotenv import load_dotenv
import os

load_dotenv()

# 🔑 API Keys
AI_ASSISTENT_API_KEY = os.getenv("ASSISTANT_API_KEY")
IMAGE_API_KEY = os.getenv("IMG_API_KEY")

# 🌱 Paths
DATASET_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),'..', 'dataset', 'Crop_recommendation.csv'))
OUTPUT_JSON = os.path.abspath(os.path.join(os.path.dirname(__file__),'..', 'dataset', 'cropss_info.json'))
IMAGE_FOLDER = 'rsc/image-crop'

# -------------------------------
# Retry decorator (for stable API calls)
# -------------------------------
def retry(max_attempts=3, delay=2, backoff=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    print(f"⚠️ {func.__name__} failed ({e}) | Retry {attempts}/{max_attempts} in {current_delay}s")
                    time.sleep(current_delay)
                    current_delay *= backoff
            print(f"❌ {func.__name__} failed after {max_attempts} attempts.")
            return None
        return wrapper
    return decorator

# -------------------------------
# Gemini crop info fetcher
# -------------------------------
@retry(max_attempts=3)
def fetch_crop_info_gemini(crop_name):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={AI_ASSISTENT_API_KEY}"

    prompt = f"""
    Provide only a JSON (no explanation, no markdown) with:
    {{
      "desc": "Short description about '{crop_name}' (20–25 words).",
      "price": "Average real market price in India today (₹/kg)",
      "season": "Main growing season in India (Kharif, Rabi, or Zaid)",
      "tips": "1–2 short cultivation tips for farmers."
    }}
    """

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, json=payload)
    response.raise_for_status()
    data = response.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()

    # Clean JSON (remove ```json)
    if text.startswith("```json"):
        text = text[len("```json"):].strip()
    if text.endswith("```"):
        text = text[:-3].strip()

    return json.loads(text)

# -------------------------------
# Pixabay image fetcher (16:9)
# -------------------------------
@retry(max_attempts=3)
def fetch_crop_image(crop_name):
    url = (
        f"https://pixabay.com/api/?key={IMAGE_API_KEY}"
        f"&q={crop_name}+crop"
        f"&image_type=photo"
        f"&orientation=horizontal"
        f"&safesearch=true"
        f"&per_page=5"
    )
    r = requests.get(url)
    r.raise_for_status()
    hits = r.json().get("hits", [])

    best = None
    best_diff = float("inf")
    for hit in hits:
        w = hit.get("imageWidth") or hit.get("webformatWidth")
        h = hit.get("imageHeight") or hit.get("webformatHeight")
        if w and h:
            ratio = w / h
            diff = abs(ratio - (16 / 9))
            if diff < best_diff:
                best_diff = diff
                best = hit
    if best:
        return best.get("largeImageURL") or best.get("webformatURL")
    return None

# -------------------------------
# Download image locally
# -------------------------------
@retry(max_attempts=3)
def download_image(url, crop_name):
    if not url:
        return "No image found"
    os.makedirs(IMAGE_FOLDER, exist_ok=True)
    ext = url.split('.')[-1].split('?')[0]
    filename = f"{crop_name.lower().replace(' ', '_')}.{ext}"
    path = os.path.join('rsc/image-crop', filename)

    r = requests.get(url)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)
    return path.replace("\\", "/")

# -------------------------------
# Main JSON Automation
# -------------------------------
def main():
    if not os.path.exists(DATASET_PATH):
        print(f"❌ Dataset not found at {DATASET_PATH}")
        return

    df = pd.read_csv(DATASET_PATH)
    if "label" not in df.columns:
        print("❌ 'label' column not found in dataset.")
        return

    crop_names = sorted(df["label"].unique())
    print(f"🌾 Found {len(crop_names)} unique crops.")

    # Load old JSON if exists
    if os.path.exists(OUTPUT_JSON):
        with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
            crop_data = json.load(f)
    else:
        crop_data = {}

    for crop in tqdm(crop_names, desc="🔄 Updating crops"):
        cname = crop.lower()
        existing = crop_data.get(cname, {})

        # Check missing fields
        missing_fields = [
            key for key in ["desc", "price", "season", "tips", "image"]
            if key not in existing or not existing[key] or existing[key] == "No image found"
        ]
        if not missing_fields:
            continue  # ✅ Already complete

        print(f"\n🧠 Updating {crop} (missing: {missing_fields})")

        # Get Gemini info
        if any(k in missing_fields for k in ["desc", "price", "season", "tips"]):
            info = fetch_crop_info_gemini(crop)
            if info:
                existing.update(info)

        # Get Image
        if "image" in missing_fields:
            image_url = fetch_crop_image(crop)
            local_image_path = download_image(image_url, crop)
            existing["image"] = local_image_path

        crop_data[cname] = existing
        time.sleep(2)  # Avoid rate limit

    # Save updated JSON
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(crop_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Successfully updated {OUTPUT_JSON} with {len(crop_data)} crops!")

if __name__ == "__main__":
    main()
