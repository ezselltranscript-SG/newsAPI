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
                page_size=limit * 2,  # Duplicamos el límite para tener más artículos
                q='*'
            )
            print(f"NewsAPI found {len(results.get('articles', []))} articles")
            
            return [{
                "title": article["title"],
                "url": article["url"],
                "source": article["source"]["name"],
                "published_at": article["publishedAt"]
            } for article in results.get("articles", [])][:limit * 2]
        except Exception as e:
            print(f"Error getting NewsAPI news: {str(e)}")
            return []

    async def get_guardian_news(self, limit: int) -> List[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://content.guardianapis.com/search",
                    params={
                        "api-key": self.guardian_key,
                        "page-size": limit * 2,  # Duplicamos el límite
                        "order-by": "newest",
                        "show-fields": "all"
                    }
                )
                results = response.json()
                articles = results.get("response", {}).get("results", [])
                print(f"Guardian found {len(articles)} articles")
                
                return [{
                    "title": article["webTitle"],
                    "url": article["webUrl"],
                    "source": "The Guardian",
                    "published_at": article["webPublicationDate"]
                } for article in articles][:limit * 2]
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

            all_entries.sort(key=lambda x: parser.parse(x.published), reverse=True)
            entries = all_entries[:limit * 2]  # Duplicamos el límite
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

    async def get_latest_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        # Calculamos cuántos artículos queremos de cada fuente
        per_source_limit = limit
        tasks = [
            self.get_newsapi_news(per_source_limit),
            self.get_guardian_news(per_source_limit),
            self.get_bbc_news(per_source_limit)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Organizamos las noticias por fuente
        news_by_source = {}
        for source_news in results:
            if source_news:
                source_name = source_news[0]['source']
                news_by_source[source_name] = source_news
                print(f"Got {len(source_news)} news from {source_name}")
        
        # Distribuimos equitativamente
        all_news = []
        per_source_quota = max(limit // len(news_by_source), 5)  # Mínimo 5 por fuente
        
        for source, news in news_by_source.items():
            # Ordenamos las noticias de cada fuente por fecha
            sorted_news = sorted(news, key=lambda x: x["published_at"], reverse=True)
            # Tomamos la cuota para esta fuente
            all_news.extend(sorted_news[:per_source_quota])
        
        # Ordenamos todas las noticias por fecha
        all_news.sort(key=lambda x: x["published_at"], reverse=True)
        
        print(f"Distribution of news:")
        for source in set(n["source"] for n in all_news):
            count = sum(1 for n in all_news if n["source"] == source)
            print(f"{source}: {count} articles")
        
        return all_news[:limit]
