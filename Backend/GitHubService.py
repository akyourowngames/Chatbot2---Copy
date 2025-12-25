"""
GitHub Integration Service
===========================
Provides real GitHub data using GitHub REST API.
"""

import requests
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubService:
    """GitHub integration service using GitHub REST API."""
    
    def __init__(self, access_token: str = ""):
        """
        Initialize GitHub service.
        
        Args:
            access_token: GitHub personal access token (optional for public data)
        """
        # Try environment variable first, then parameter
        self.access_token = access_token or os.getenv('GITHUB_TOKEN', '')
        self.base_url = "https://api.github.com"
        self._cache = {}
        self._cache_duration = timedelta(minutes=10)
        
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if self.access_token:
            self.headers["Authorization"] = f"token {self.access_token}"
        
        logger.info("[GITHUB] Service initialized")
    
    def get_user_repos(self, username: str, sort: str = "updated", 
                       per_page: int = 10) -> Dict[str, Any]:
        """
        Get user's public repositories.
        
        Args:
            username: GitHub username
            sort: Sort by created, updated, pushed, full_name
            per_page: Number of repos to return
            
        Returns:
            Repository data
        """
        try:
            # Check cache
            cache_key = f"repos_{username}_{sort}_{per_page}"
            if cache_key in self._cache:
                cached_data, cached_time = self._cache[cache_key]
                if datetime.now() - cached_time < self._cache_duration:
                    return cached_data
            
            url = f"{self.base_url}/users/{username}/repos"
            params = {
                "sort": sort,
                "per_page": per_page,
                "type": "owner"
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=5)
            response.raise_for_status()
            
            repos = response.json()
            
            # Parse repos
            repo_list = []
            for repo in repos:
                repo_list.append({
                    "name": repo["name"],
                    "description": repo["description"],
                    "url": repo["html_url"],
                    "stars": repo["stargazers_count"],
                    "forks": repo["forks_count"],
                    "language": repo["language"],
                    "updated_at": repo["updated_at"],
                    "is_private": repo["private"],
                    "topics": repo.get("topics", [])
                })
            
            result = {
                "status": "success",
                "username": username,
                "repos": repo_list,
                "total": len(repo_list),
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache
            self._cache[cache_key] = (result, datetime.now())
            
            logger.info(f"[GITHUB] Fetched {len(repo_list)} repos for {username}")
            return result
            
        except Exception as e:
            logger.error(f"[GITHUB] Failed to fetch repos: {e}")
            return {
                "status": "error",
                "error": "Failed to fetch repositories",
                "message": str(e)
            }
    
    def get_trending_repos(self, language: str = "", since: str = "daily") -> Dict[str, Any]:
        """
        Get trending repositories.
        
        Args:
            language: Programming language filter
            since: daily, weekly, monthly
            
        Returns:
            Trending repos
        """
        try:
            # GitHub trending scraper (GitHub doesn't have official API for trending)
            # Using GitHub search as alternative
            query = "stars:>100"
            if language:
                query += f" language:{language}"
            
            url = f"{self.base_url}/search/repositories"
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": 10
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            trending = []
            for repo in data.get("items", []):
                trending.append({
                    "name": repo["full_name"],
                    "description": repo["description"],
                    "url": repo["html_url"],
                    "stars": repo["stargazers_count"],
                    "language": repo["language"],
                    "owner": repo["owner"]["login"]
                })
            
            return {
                "status": "success",
                "language": language or "all",
                "trending": trending,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[GITHUB] Failed to fetch trending: {e}")
            return {
                "status": "error",
                "error": "Failed to fetch trending repos",
                "message": str(e)
            }
    
    def search_repos(self, query: str, per_page: int = 10) -> Dict[str, Any]:
        """
        Search GitHub repositories.
        
        Args:
            query: Search query
            per_page: Results per page
            
        Returns:
            Search results
        """
        try:
            url = f"{self.base_url}/search/repositories"
            params = {
                "q": query,
                "sort": "stars",
                "per_page": per_page
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            results = []
            for repo in data.get("items", []):
                results.append({
                    "name": repo["full_name"],
                    "description": repo["description"],
                    "url": repo["html_url"],
                    "stars": repo["stargazers_count"],
                    "language": repo["language"]
                })
            
            return {
                "status": "success",
                "query": query,
                "total_count": data.get("total_count", 0),
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[GITHUB] Search failed: {e}")
            return {
                "status": "error",
                "error": "Search failed",
                "message": str(e)
            }


# Global instance
github_service = GitHubService()


# Convenience functions
def get_repos(username: str) -> Dict[str, Any]:
    """Get user's repositories."""
    return github_service.get_user_repos(username)


def get_trending(language: str = "") -> Dict[str, Any]:
    """Get trending repositories."""
    return github_service.get_trending_repos(language)


# Test
if __name__ == "__main__":
    print("🐙 Testing GitHub Service\n")
    
    # Test trending
    trending = get_trending("python")
    if trending["status"] == "success":
        print(f"⭐ Top {len(trending['trending'])} Trending Python Repos:\n")
        for i, repo in enumerate(trending["trending"][:5], 1):
            print(f"{i}. {repo['name']} (⭐ {repo['stars']})")
            print(f"   {repo['description'][:80]}...")
            print()
