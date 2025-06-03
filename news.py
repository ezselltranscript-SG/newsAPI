from typing import List, Dict, Any
from newsapi import NewsApiClient
import httpx
import feedparser
from datetime import datetime
from dateutil import parser
import asyncio

class NewsAggregator:
    def __init__(self, newsapi_key: str, guardian_key: str, reuters_key: str = ""):
        self.newsapi = NewsApiClient(api_key=newsapi_key)
        self.guardian_key = guardian_key
        self.reuters_key = reuters_key
        self.guardian_url = "https://content.guardianapis.com/search"
        self.reuters_url = "https://api.reuters.com/v2/feed/news"
        self.bbc_feeds = [
            "http://feeds.bbci.co.uk/news/world/rss.xml",
            "http://feeds.bbci.co.uk/news/technology/rss.xml",
            "http://feeds.bbci.co.uk/news/business/rss.xml"
        ]

    async def get_newsapi_news(self, limit: int) -> List[Dict[str, Any]]:
        try:
            print("Fetching from NewsAPI...")
            results = self.newsapi.get_everything(
                language='en',
                sort_by='publishedAt',
                page_size=limit,
                q='*'
            )
            print(f"NewsAPI response: {results}")
            
            return [{
                "title": article["title"],
                "url": article["url"],
                "source": article["source"]["name"],
                "published_at": article["publishedAt"]
            } for article in results["articles"]]
        except Exception as e:
            print(f"Error getting NewsAPI news: {str(e)}")
            return []

    async def get_guardian_news(self, limit: int) -> List[Dict[str, Any]]:
        try:
            params = {
                "api-key": self.guardian_key,
                "page-size": limit,
                "order-by": "newest"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(self.guardian_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                return [{
                    "title": article["webTitle"],
                    "url": article["webUrl"],
                    "source": "The Guardian",
                    "published_at": article["webPublicationDate"]
                } for article in data["response"]["results"]]
        except Exception as e:
            print(f"Error getting Guardian news: {str(e)}")
            return []

    async def get_bbc_news(self, limit: int) -> List[Dict[str, Any]]:
        try:
            print("Fetching from BBC...")
            all_entries = []
            for feed_url in self.bbc_feeds:
                print(f"Parsing BBC feed: {feed_url}")
                feed = feedparser.parse(feed_url)
                print(f"Found {len(feed.entries)} entries in feed")
                all_entries.extend(feed.entries)

            # Sort by date and limit
            all_entries.sort(key=lambda x: parser.parse(x.published), reverse=True)
            entries = all_entries[:limit]
            print(f"Total BBC entries after sorting and limiting: {len(entries)}")

            return [{
                "title": entry.title,
                "url": entry.link,
                "source": "BBC News",
                "published_at": parser.parse(entry.published).isoformat()
            } for entry in entries]
        except Exception as e:
            print(f"Error getting BBC news: {str(e)}")
            return []

    async def get_reuters_news(self, limit: int) -> List[Dict[str, Any]]:
        if not self.reuters_key:
            return []

        try:
            headers = {"Authorization": f"Bearer {self.reuters_key}"}
            params = {"limit": limit}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(self.reuters_url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                return [{
                    "title": article["title"],
                    "url": article["url"],
                    "source": "Reuters",
                    "published_at": article["published_at"]
                } for article in data["results"]]
        except Exception as e:
            print(f"Error getting Reuters news: {str(e)}")
            return []

    async def get_latest_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        # Get news from all sources
        tasks = [
            self.get_newsapi_news(limit),
            self.get_guardian_news(limit),
            self.get_bbc_news(limit)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Combine all news
        all_news = []
        for source_news in results:
            if source_news:  # Solo añadir si hay noticias
                print(f"Adding {len(source_news)} news from source {source_news[0]['source'] if source_news else 'unknown'}")
                all_news.extend(source_news)
        
        # Sort by date, most recent first
        try:
            all_news.sort(key=lambda x: x["published_at"], reverse=True)
        except Exception as e:
            print(f"Error sorting news: {e}")
        
        # Return requested number of news
        return all_news[:limit]
