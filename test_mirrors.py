
import requests
import json

mirrors = [
    "https://api.consumet.org",
    "https://consumet-api-jade.vercel.app",
    "https://c.delusionz.xyz",
    "https://api.consumet.org" # Retry official
]

def test_mirror(url):
    print(f"Testing {url}...")
    try:
        # Test ZORO
        print(f"  Testing Zoro: {url}/anime/zoro/demon slayer")
        resp = requests.get(f"{url}/anime/zoro/demon slayer", timeout=5)
        if resp.status_code == 200 and "results" in resp.json() and len(resp.json()["results"]) > 0:
             print(f"✅ SUCCESS (Zoro): {url}")
             return True

        # Test ANILIST
        print(f"  Testing Anilist: {url}/meta/anilist/demon slayer")
        resp = requests.get(f"{url}/meta/anilist/demon slayer", timeout=5)
        if resp.status_code == 200 and "results" in resp.json() and len(resp.json()["results"]) > 0:
             print(f"✅ SUCCESS (Anilist): {url}")
             return True
             
    except Exception as e:
        print(f"❌ ERROR: {url} - {e}")
    return False

print("--- Finding Working Mirror ---")
for m in mirrors:
    if test_mirror(m):
        break
