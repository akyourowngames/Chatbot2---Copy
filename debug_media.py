
import sys
import os

# Add current directory to path so we can import Backend modules
sys.path.append(os.getcwd())

def test_spotify():
    print("\n--- Testing Spotify ---")
    try:
        from Backend.SpotifyPlayer import spotify_player
        result = spotify_player.play("Blinding Lights")
        print(f"Spotify Result: {result.get('status')}")
        if result.get('status') == 'success':
            print(f"Embed URL: {result['spotify']['embed_url']}")
        else:
            print(f"Error: {result.get('message')}")
    except Exception as e:
        print(f"Spotify Exception: {e}")

def test_anime():
    print("\n--- Testing Anime (Zoro) ---")
    import requests
    base_url = "https://consumet-api-jade.vercel.app/anime/zoro"
    
    # 1. Search
    print(f"Searching: {base_url}/demon slayer")
    resp = requests.get(f"{base_url}/demon slayer")
    if resp.status_code != 200:
        print("Search Failed")
        return
        
    data = resp.json()
    if not data.get("results"):
        print("No results")
        return
        
    first = data["results"][0]
    print(f"Search Result Keys: {first.keys()}")
    print(f"ID: {first.get('id')}")
    
    # 2. Info
    anime_id = first.get('id')
    print(f"\nGetting Info: {base_url}/info?id={anime_id}")
    resp = requests.get(f"{base_url}/info?id={anime_id}")
    info_data = resp.json()
    print(f"Info Keys: {info_data.keys()}")
    
    # 3. Stream
    if info_data.get("episodes"):
        first_ep = info_data["episodes"][0]
        ep_id = first_ep.get("id")
        print(f"\nGetting Stream: {base_url}/watch?episodeId={ep_id}")
        resp = requests.get(f"{base_url}/watch?episodeId={ep_id}")
        stream_data = resp.json()
        print(f"Stream Keys: {stream_data.keys()}")
        print(f"Sources: {len(stream_data.get('sources', []))}")
        if stream_data.get('sources'):
             print(f"First Source: {stream_data['sources'][0]}")

if __name__ == "__main__":
    test_spotify()
    test_anime()
