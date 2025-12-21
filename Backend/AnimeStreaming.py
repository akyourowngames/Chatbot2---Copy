"""
Anime Streaming System - Watch & Discover Anime
================================================
Search, stream, and track anime with multiple API sources.
Uses: Consumet (streaming), Jikan (MyAnimeList), Anilist (trending)
"""

import logging
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnimeStreamingSystem:
    """
    Beast-level anime streaming integration.
    Search, watch, get info, and track trending anime.
    """
    

    def __init__(self):
        # API Endpoints - Updated with working mirrors
        self.mirrors = [
            "https://api.consumet.org",             # Official (most reliable)
            "https://consumet-api-jade.vercel.app", # Vercel backup
            "https://consumet-api.onrender.com",    # Render backup
        ]
        self.consumet_base = self.mirrors[0] 
        self.jikan_base = "https://api.jikan.moe/v4"      # MyAnimeList
        self.anilist_base = "https://graphql.anilist.co"  # Trending/Tracking
        
        # Watchlist (in-memory, can be extended to Supabase)
        self.watchlist = {}
        
        logger.info("[ANIME] Anime Streaming System initialized 🎬")
    
    def _sync_request(self, url: str, method: str = "GET", 
                      json_data: dict = None, headers: dict = None) -> Optional[dict]:
        """Synchronous HTTP request."""
        import requests
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=15)
            else:
                response = requests.post(url, json=json_data, headers=headers, timeout=15)
            
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    logger.error(f"[ANIME] JSON Decode Error. Response: {response.text[:200]}...")
                    return None
            else:
                logger.warning(f"[ANIME] Request failed: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"[ANIME] Request error: {e}")
            return None
    
    def _scrape_hianime(self, anime_name: str, episode: int = 1) -> Optional[Dict[str, Any]]:
        """
        Scrape embed URL from hianime.to (formerly zoro.to).
        Returns the actual embed URL that can be used in an iframe.
        """
        import requests
        from bs4 import BeautifulSoup
        import re
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://hianime.to/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        slug = anime_name.lower().strip().replace(" ", "-").replace(":", "").replace("'", "")
        
        try:
            # Step 1: Search for anime on hianime.to
            search_url = f"https://hianime.to/search?keyword={anime_name.replace(' ', '+')}"
            logger.info(f"[ANIME] Scraping HiAnime search: {search_url}")
            
            r = requests.get(search_url, headers=headers, timeout=20)
            if not r.ok:
                logger.warning(f"[ANIME] HiAnime search failed: {r.status_code}")
                return None
            
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # Find first anime result
            result = soup.find('a', {'class': 'dynamic-name'})
            if not result:
                result = soup.select_one('.film-poster a') or soup.select_one('.flw-item a')
            
            if not result:
                logger.warning("[ANIME] No HiAnime search results found")
                return None
            
            anime_url = result.get('href', '')
            if not anime_url.startswith('http'):
                anime_url = f"https://hianime.to{anime_url}"
            
            logger.info(f"[ANIME] Found anime URL: {anime_url}")
            
            # Step 2: Get watch page with episode
            # HiAnime URLs are like: /watch/anime-name-123?ep=456
            # We need to find the episode ID
            anime_page = requests.get(anime_url, headers=headers, timeout=20)
            if not anime_page.ok:
                return None
            
            anime_soup = BeautifulSoup(anime_page.text, 'html.parser')
            
            # Find episode link
            ep_links = anime_soup.find_all('a', {'class': 'ep-item'}) or anime_soup.select('.ssl-item.ep-item a')
            
            target_ep = None
            for ep in ep_links:
                ep_num = ep.get('data-number') or ep.get('data-id') or ep.get_text(strip=True)
                try:
                    if str(episode) == str(ep_num) or int(ep_num) == episode:
                        target_ep = ep
                        break
                except:
                    continue
            
            if not target_ep and ep_links:
                target_ep = ep_links[min(episode-1, len(ep_links)-1)]
            
            if target_ep:
                ep_url = target_ep.get('href', '')
                if not ep_url.startswith('http'):
                    ep_url = f"https://hianime.to{ep_url}"
                
                # HiAnime uses megacloud.tv or similar for embeds
                # Generate embed URL pattern
                anime_id = re.search(r'-(\d+)\?', ep_url)
                ep_id = re.search(r'ep=(\d+)', ep_url)
                
                if anime_id and ep_id:
                    # HiAnime's embed pattern
                    embed_url = f"https://megacloud.tv/embed-2/e-1/{anime_id.group(1)}?ep={ep_id.group(1)}"
                    
                    return {
                        "status": "success",
                        "embed_url": embed_url,
                        "watch_url": ep_url,
                        "anime_url": anime_url,
                        "source": "hianime"
                    }
            
            # Fallback: Return watch link only
            return {
                "status": "partial",
                "watch_url": anime_url,
                "source": "hianime"
            }
            
        except Exception as e:
            logger.error(f"[ANIME] HiAnime scrape error: {e}")
            return None
    
    # ==================== SEARCH ====================
    
    def search_anime(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Search for anime using multiple sources.
        
        Args:
            query: Anime name to search
            limit: Max results
            
        Returns:
            Combined search results from multiple APIs
        """
        logger.info(f"[ANIME] Searching: {query}")
        
        results = {
            "query": query,
            "results": [],
            "sources_used": []
        }
        
        # Try Consumet first (has streaming)
        consumet_results = self._search_consumet(query, limit)
        if consumet_results:
            results["results"].extend(consumet_results)
            results["sources_used"].append("consumet")
        
        # Enhance with Jikan (MAL data)
        jikan_results = self._search_jikan(query, limit)
        if jikan_results:
            # Merge with existing or add new
            for j_item in jikan_results:
                existing = next((r for r in results["results"] 
                               if r.get("title", "").lower() == j_item.get("title", "").lower()), None)
                if existing:
                    existing.update({"mal_data": j_item})
                else:
                    results["results"].append(j_item)
            results["sources_used"].append("jikan")
        
        results["total"] = len(results["results"])
        return results
    
    def _search_consumet(self, query: str, limit: int = 10) -> List[Dict]:
        """Search via Consumet API using AnimeKai provider."""
        # AnimeKai is the most reliable provider
        try:
            # AnimeKai search endpoint: /anime/animekai/{query}
            url = f"{self.consumet_base}/anime/animekai/{query}"
            logger.info(f"[ANIME] Searching: {url}")
            data = self._sync_request(url)
            
            if data and "results" in data and len(data["results"]) > 0:
                logger.info(f"[ANIME] Found {len(data['results'])} results via animekai")
                results = []
                for item in data["results"][:limit]:
                    results.append({
                        "id": item.get("id"),
                        "title": item.get("title"),
                        "image": item.get("image"),
                        "release_date": item.get("releaseDate"),
                        "sub_or_dub": item.get("subOrDub", "sub"),
                        "source": "consumet",
                        "provider": "animekai",  # Use animekai
                        "streamable": True
                    })
                return results
        except Exception as e:
            logger.error(f"[ANIME] AnimeKai search error: {e}")
        
        return []
    
    def _search_jikan(self, query: str, limit: int = 10) -> List[Dict]:
        """Search via Jikan API (MyAnimeList)."""
        try:
            url = f"{self.jikan_base}/anime?q={query}&limit={limit}"
            data = self._sync_request(url)
            
            if data and "data" in data:
                results = []
                for item in data["data"]:
                    results.append({
                        "mal_id": item.get("mal_id"),
                        "title": item.get("title"),
                        "title_english": item.get("title_english"),
                        "image": item.get("images", {}).get("jpg", {}).get("large_image_url"),
                        "synopsis": item.get("synopsis", "")[:300] + "..." if item.get("synopsis") else "",
                        "score": item.get("score"),
                        "episodes": item.get("episodes"),
                        "status": item.get("status"),
                        "rating": item.get("rating"),
                        "genres": [g.get("name") for g in item.get("genres", [])],
                        "source": "jikan",
                        "streamable": False
                    })
                return results
        except Exception as e:
            logger.error(f"[ANIME] Jikan search error: {e}")
        return []
    
    # ==================== WATCH/STREAM ====================
    
    def get_episodes(self, anime_id: str, provider: str = "animekai") -> Dict[str, Any]:
        """Get all episodes for an anime using AnimeKai."""
        logger.info(f"[ANIME] Getting episodes for: {anime_id}")
        
        try:
            # AnimeKai info endpoint: /anime/animekai/info/{id}
            url = f"{self.consumet_base}/anime/animekai/info/{anime_id}"
            logger.info(f"[ANIME] Info URL: {url}")
            data = self._sync_request(url)
            
            if data:
                return {
                    "status": "success",
                    "id": data.get("id"),
                    "title": data.get("title"),
                    "image": data.get("image"),
                    "description": data.get("description"),
                    "type": data.get("type"),
                    "release_date": data.get("releaseDate"),
                    "anime_status": data.get("status"),
                    "total_episodes": data.get("totalEpisodes"),
                    "episodes": data.get("episodes", [])
                }
        except Exception as e:
            logger.error(f"[ANIME] Get episodes error: {e}")
        
        return {"status": "error", "message": "Failed to get episodes"}
    
    def get_streaming_links(self, episode_id: str, provider: str = "animekai", server: str = "vidstreaming") -> Dict[str, Any]:
        """Get streaming links using AnimeKai."""
        logger.info(f"[ANIME] Getting stream for: {episode_id}")
        
        try:
            # AnimeKai watch endpoint: /anime/animekai/watch/{episodeId}
            url = f"{self.consumet_base}/anime/animekai/watch/{episode_id}"
            logger.info(f"[ANIME] Watch URL: {url}")
            
            # Request with server and dub params
            import requests
            response = requests.get(url, params={"server": server, "dub": False}, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if data and "sources" in data:
                    sources = []
                    for src in data.get("sources", []):
                        sources.append({
                            "url": src.get("url"),
                            "quality": src.get("quality", "auto"),
                            "is_m3u8": src.get("isM3U8", True)
                        })
                    
                    return {
                        "status": "success",
                        "episode_id": episode_id,
                        "sources": sources,
                        "download": data.get("download"),
                        "headers": data.get("headers", {})
                    }
        except Exception as e:
            logger.error(f"[ANIME] Stream error: {e}")
        
        return {"status": "error", "message": "Failed to get streaming links"}
    
    def watch_anime(self, anime_name: str, episode: int = 1) -> Dict[str, Any]:
        """
        Complete flow: Search → Get Episode → Get Stream Link
        Falls back to embed players if API is down.
        """
        logger.info(f"[ANIME] Watch request: {anime_name} Ep {episode}")
        
        # Clean anime name for URL
        slug = anime_name.lower().strip()
        slug = slug.replace(" ", "-").replace(":", "").replace("'", "")
        
        # Try API first
        try:
            search = self.search_anime(anime_name, limit=1)
            if search.get("results"):
                anime = search["results"][0]
                anime_id = anime.get("id")
                provider = anime.get("provider", "animekai")
                
                if anime_id:
                    # Get episodes
                    episodes_data = self.get_episodes(anime_id, provider)
                    if episodes_data.get("status") != "error":
                        episodes = episodes_data.get("episodes", [])
                        if episodes and 1 <= episode <= len(episodes):
                            episode_info = episodes[episode - 1]
                            episode_id = episode_info.get("id")
                            
                            # Get stream
                            stream = self.get_streaming_links(episode_id, provider)
                            if stream.get("status") == "success" and stream.get("sources"):
                                return {
                                    "status": "success",
                                    "anime": {
                                        "title": episodes_data.get("title", anime_name),
                                        "image": episodes_data.get("image"),
                                        "total_episodes": episodes_data.get("total_episodes", len(episodes))
                                    },
                                    "episode": {"number": episode, "id": episode_id},
                                    "streams": stream.get("sources", []),
                                    "download": stream.get("download"),
                                    "message": f"🎬 Ready to watch: {episodes_data.get('title', anime_name)} - Episode {episode}"
                                }
        except Exception as e:
            logger.warning(f"[ANIME] API failed, using fallback: {e}")
        
        # FALLBACK 1: Try scraping HiAnime.to for real embed URL
        logger.info(f"[ANIME] Trying HiAnime scraper for: {anime_name} ep {episode}")
        hianime_result = self._scrape_hianime(anime_name, episode)
        
        if hianime_result and hianime_result.get("status") == "success" and hianime_result.get("embed_url"):
            logger.info(f"[ANIME] Got HiAnime embed: {hianime_result.get('embed_url')}")
            
            # Get additional info from Jikan for thumbnail
            jikan_info = self._search_jikan(anime_name, limit=1)
            anime_title = anime_name.title()
            anime_image = None
            if jikan_info:
                anime_title = jikan_info[0].get("title", anime_name)
                anime_image = jikan_info[0].get("image") or jikan_info[0].get("images", {}).get("jpg", {}).get("large_image_url")
            
            return {
                "status": "success",
                "fallback": False,
                "anime": {
                    "title": anime_title,
                    "image": anime_image
                },
                "episode": {"number": episode},
                "embed_url": hianime_result.get("embed_url"),
                "streams": [{
                    "name": "HiAnime",
                    "embed": hianime_result.get("embed_url"),
                    "quality": "HD"
                }],
                "watch_links": [
                    {"name": "HiAnime", "url": hianime_result.get("watch_url", f"https://hianime.to/search?keyword={anime_name}")},
                    {"name": "AnimeKai", "url": f"https://animekai.to/search?q={anime_name.replace(' ', '+')}"}
                ],
                "message": f"🎬 Now Streaming: {anime_title} Episode {episode}",
                "title": anime_title,
                "thumbnail": anime_image
            }
        
        # FALLBACK 2: Use VidSrc/other embeds
        logger.info(f"[ANIME] HiAnime failed, trying VidSrc fallback for: {slug} ep {episode}")
        
        # Get anime info from Jikan (this always works and gives us MAL ID)
        jikan_info = self._search_jikan(anime_name, limit=1)
        anime_title = anime_name.title()
        anime_image = None
        total_eps = "?"
        mal_id = None
        
        if jikan_info:
            anime_title = jikan_info[0].get("title", anime_name)
            anime_image = jikan_info[0].get("image") or jikan_info[0].get("images", {}).get("jpg", {}).get("large_image_url")
            total_eps = jikan_info[0].get("episodes", "?")
            mal_id = jikan_info[0].get("mal_id")
        
        # Generate embed URLs from various sources
        embed_sources = []
        
        if mal_id:
            # VidSrc supports anime by MAL ID - WORKS in iframes!
            embed_sources.append({
                "name": "VidSrc",
                "url": f"https://vidsrc.xyz/embed/anime/{mal_id}/{episode}",
                "embed": f"https://vidsrc.xyz/embed/anime/{mal_id}/{episode}",
                "quality": "auto",
                "is_m3u8": False
            })
            embed_sources.append({
                "name": "2Embed",
                "url": f"https://2embed.cc/embedanime/{mal_id}/{episode}",
                "embed": f"https://2embed.cc/embedanime/{mal_id}/{episode}",
                "quality": "auto", 
                "is_m3u8": False
            })
            embed_sources.append({
                "name": "AnimeAPI",
                "url": f"https://vidsrc.in/embed/anime/{mal_id}/{episode}",
                "embed": f"https://vidsrc.in/embed/anime/{mal_id}/{episode}",
                "quality": "auto",
                "is_m3u8": False
            })
        
        # Primary embed - VidSrc is most reliable for anime
        primary_embed = embed_sources[0]["embed"] if embed_sources else None
        
        return {
            "status": "success",
            "fallback": True if not mal_id else False,
            "anime": {
                "title": anime_title,
                "image": anime_image,
                "total_episodes": total_eps,
                "mal_id": mal_id
            },
            "episode": {"number": episode},
            "streams": embed_sources,
            "embed_url": primary_embed,
            "watch_links": [
                {"name": "GogoAnime", "url": f"https://gogoanime3.co/{slug}-episode-{episode}"},
                {"name": "Zoro", "url": f"https://zoro.to/search?keyword={slug.replace('-', '+')}"},
                {"name": "AnimePahe", "url": f"https://animepahe.ru/anime/{slug}"}
            ],
            "message": f"🎬 Now Streaming: {anime_title} Episode {episode}" if primary_embed else f"🔍 Found: {anime_title} - Use watch links below",
            "title": anime_title,
            "thumbnail": anime_image
        }
    
    # ==================== INFO ====================
    
    def get_anime_info(self, anime_name: str) -> Dict[str, Any]:
        """
        Get detailed anime information from multiple sources.
        
        Args:
            anime_name: Name of the anime
            
        Returns:
            Rich anime details
        """
        logger.info(f"[ANIME] Getting info for: {anime_name}")
        
        # Get Jikan data for detailed info
        jikan = self._search_jikan(anime_name, limit=1)
        
        if jikan:
            anime = jikan[0]
            
            # Try to get additional data
            mal_id = anime.get("mal_id")
            extra_data = {}
            
            if mal_id:
                # Get characters
                try:
                    chars_url = f"{self.jikan_base}/anime/{mal_id}/characters"
                    chars_data = self._sync_request(chars_url)
                    if chars_data and "data" in chars_data:
                        extra_data["characters"] = [
                            {
                                "name": c.get("character", {}).get("name"),
                                "role": c.get("role"),
                                "image": c.get("character", {}).get("images", {}).get("jpg", {}).get("image_url")
                            }
                            for c in chars_data["data"][:5]
                        ]
                except:
                    pass
                
                # Get recommendations
                try:
                    rec_url = f"{self.jikan_base}/anime/{mal_id}/recommendations"
                    rec_data = self._sync_request(rec_url)
                    if rec_data and "data" in rec_data:
                        extra_data["recommendations"] = [
                            {
                                "title": r.get("entry", {}).get("title"),
                                "image": r.get("entry", {}).get("images", {}).get("jpg", {}).get("image_url")
                            }
                            for r in rec_data["data"][:5]
                        ]
                except:
                    pass
            
            return {
                "status": "success",
                "anime": {
                    **anime,
                    **extra_data
                }
            }
        
        return {"status": "error", "message": f"No info found for '{anime_name}'"}
    
    # ==================== TRENDING ====================
    
    def get_trending(self, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Get trending anime from Anilist.
        
        Args:
            page: Page number
            per_page: Results per page
            
        Returns:
            Trending anime list
        """
        logger.info("[ANIME] Getting trending anime")
        
        query = '''
        query ($page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                media(sort: TRENDING_DESC, type: ANIME) {
                    id
                    title {
                        romaji
                        english
                    }
                    coverImage {
                        large
                    }
                    description
                    episodes
                    status
                    genres
                    averageScore
                    popularity
                    seasonYear
                    season
                }
            }
        }
        '''
        
        variables = {"page": page, "perPage": per_page}
        
        try:
            response = self._sync_request(
                self.anilist_base, 
                method="POST",
                json_data={"query": query, "variables": variables},
                headers={"Content-Type": "application/json"}
            )
            
            if response and "data" in response:
                media_list = response["data"]["Page"]["media"]
                
                trending = []
                for item in media_list:
                    trending.append({
                        "id": item.get("id"),
                        "title": item.get("title", {}).get("english") or item.get("title", {}).get("romaji"),
                        "title_romaji": item.get("title", {}).get("romaji"),
                        "image": item.get("coverImage", {}).get("large"),
                        "description": (item.get("description") or "")[:200].replace("<br>", " "),
                        "episodes": item.get("episodes"),
                        "status": item.get("status"),
                        "genres": item.get("genres", []),
                        "score": item.get("averageScore"),
                        "popularity": item.get("popularity"),
                        "year": item.get("seasonYear"),
                        "season": item.get("season")
                    })
                
                return {
                    "status": "success",
                    "trending": trending,
                    "total": len(trending),
                    "page": page
                }
        except Exception as e:
            logger.error(f"[ANIME] Anilist error: {e}")
        
        # Fallback to Jikan
        return self._get_trending_jikan()
    
    def _get_trending_jikan(self) -> Dict[str, Any]:
        """Fallback trending from Jikan (MAL top airing)."""
        try:
            url = f"{self.jikan_base}/top/anime?filter=airing&limit=10"
            data = self._sync_request(url)
            
            if data and "data" in data:
                trending = []
                for item in data["data"]:
                    trending.append({
                        "mal_id": item.get("mal_id"),
                        "title": item.get("title"),
                        "image": item.get("images", {}).get("jpg", {}).get("large_image_url"),
                        "score": item.get("score"),
                        "episodes": item.get("episodes"),
                        "status": "Airing",
                        "genres": [g.get("name") for g in item.get("genres", [])]
                    })
                
                return {
                    "status": "success",
                    "trending": trending,
                    "source": "jikan"
                }
        except Exception as e:
            logger.error(f"[ANIME] Jikan trending error: {e}")
        
        return {"status": "error", "message": "Failed to get trending"}
    
    def get_popular_this_season(self) -> Dict[str, Any]:
        """Get popular anime from current season."""
        query = '''
        query {
            Page(page: 1, perPage: 15) {
                media(sort: POPULARITY_DESC, type: ANIME, status: RELEASING) {
                    id
                    title {
                        romaji
                        english
                    }
                    coverImage {
                        large
                    }
                    episodes
                    genres
                    averageScore
                    nextAiringEpisode {
                        episode
                        airingAt
                    }
                }
            }
        }
        '''
        
        try:
            response = self._sync_request(
                self.anilist_base,
                method="POST",
                json_data={"query": query},
                headers={"Content-Type": "application/json"}
            )
            
            if response and "data" in response:
                media = response["data"]["Page"]["media"]
                
                anime_list = []
                for item in media:
                    next_ep = item.get("nextAiringEpisode")
                    anime_list.append({
                        "id": item.get("id"),
                        "title": item.get("title", {}).get("english") or item.get("title", {}).get("romaji"),
                        "image": item.get("coverImage", {}).get("large"),
                        "episodes": item.get("episodes"),
                        "genres": item.get("genres", []),
                        "score": item.get("averageScore"),
                        "next_episode": next_ep.get("episode") if next_ep else None
                    })
                
                return {"status": "success", "anime": anime_list}
        except Exception as e:
            logger.error(f"[ANIME] Season error: {e}")
        
        return {"status": "error", "message": "Failed to get seasonal anime"}
    
    # ==================== WATCHLIST ====================
    
    def add_to_watchlist(self, user_id: str, anime_name: str, anime_id: str = None) -> Dict[str, Any]:
        """Add anime to user's watchlist."""
        if user_id not in self.watchlist:
            self.watchlist[user_id] = []
        
        entry = {
            "name": anime_name,
            "id": anime_id,
            "added_at": datetime.now().isoformat(),
            "status": "plan_to_watch"
        }
        
        # Check if already exists
        if not any(w["name"].lower() == anime_name.lower() for w in self.watchlist[user_id]):
            self.watchlist[user_id].append(entry)
            return {"status": "success", "message": f"Added '{anime_name}' to watchlist ✓"}
        
        return {"status": "exists", "message": f"'{anime_name}' is already in your watchlist"}
    
    def get_watchlist(self, user_id: str) -> Dict[str, Any]:
        """Get user's watchlist."""
        if user_id not in self.watchlist:
            return {"status": "empty", "watchlist": [], "message": "Your watchlist is empty"}
        
        return {
            "status": "success",
            "watchlist": self.watchlist[user_id],
            "total": len(self.watchlist[user_id])
        }
    
    def remove_from_watchlist(self, user_id: str, anime_name: str) -> Dict[str, Any]:
        """Remove anime from watchlist."""
        if user_id not in self.watchlist:
            return {"status": "error", "message": "Watchlist not found"}
        
        original_len = len(self.watchlist[user_id])
        self.watchlist[user_id] = [
            w for w in self.watchlist[user_id] 
            if w["name"].lower() != anime_name.lower()
        ]
        
        if len(self.watchlist[user_id]) < original_len:
            return {"status": "success", "message": f"Removed '{anime_name}' from watchlist"}
        
        return {"status": "not_found", "message": f"'{anime_name}' not found in watchlist"}


# Global instance
anime_system = AnimeStreamingSystem()


# Convenience functions
def search_anime(query: str) -> Dict[str, Any]:
    """Search for anime."""
    return anime_system.search_anime(query)

def watch_anime(name: str, episode: int = 1) -> Dict[str, Any]:
    """Watch an anime episode."""
    return anime_system.watch_anime(name, episode)

def get_trending() -> Dict[str, Any]:
    """Get trending anime."""
    return anime_system.get_trending()

def anime_info(name: str) -> Dict[str, Any]:
    """Get anime details."""
    return anime_system.get_anime_info(name)


if __name__ == "__main__":
    # Test
    print("🎬 Testing Anime System...\n")
    
    # Test search
    results = anime_system.search_anime("Demon Slayer")
    print(f"Search results: {len(results.get('results', []))} found")
    
    # Test trending
    trending = anime_system.get_trending()
    print(f"Trending: {len(trending.get('trending', []))} anime")
