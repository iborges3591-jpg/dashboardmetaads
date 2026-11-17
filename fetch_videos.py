import os, re, json, requests

TOKEN = os.environ["META_ACCESS_TOKEN"]
G = "https://graph.facebook.com/v21.0"

src = open("update_dashboard.py", encoding="utf-8", errors="ignore").read()
ads = dict(re.findall(r'"([a-z0-9_]+)":\s*"(\d{15,})"', src))

out = {}
for key, aid in ads.items():
    try:
        r = requests.get(f"{G}/{aid}", params={
            "fields": "creative{video_id,thumbnail_url,effective_object_story_id,instagram_permalink_url,object_story_spec}",
            "access_token": TOKEN}, timeout=30).json()
        cr = r.get("creative", {}) or {}
        vid = cr.get("video_id") or ((cr.get("object_story_spec") or {}).get("video_data") or {}).get("video_id")
        item = {"poster": cr.get("thumbnail_url", "")}
        if cr.get("instagram_permalink_url"):
            item["ig"] = cr["instagram_permalink_url"]
        if cr.get("effective_object_story_id"):
            item["story"] = cr["effective_object_story_id"]
        if vid:
            v = requests.get(f"{G}/{vid}", params={
                "fields": "source,permalink_url,picture,length",
                "access_token": TOKEN}, timeout=30).json()
            item["video_id"] = vid
            item["src"] = v.get("source", "")
            item["permalink"] = v.get("permalink_url", "")
            item["poster"] = v.get("picture") or item["poster"]
            item["length"] = v.get("length", 0)
            if v.get("error"):
                item["error"] = v["error"].get("message", "")
        elif r.get("error"):
            item["error"] = r["error"].get("message", "")
        out[key] = item
    except Exception as e:
        out[key] = {"error": str(e)}

with open("videos.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("ok", len(out), "anuncios,", sum(1 for x in out.values() if x.get("src")), "com video")
