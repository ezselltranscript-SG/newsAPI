from typing import List, Dict, Any
from newsapi import NewsApiClient
import httpx
import feedparser
from datetime import datetime
from dateutil import parser
import asyncio
from newsdataapi import NewsDataApiClient

class NewsAggregator:
    def __init__(self, newsapi_key: str, guardian_key: str, reuters_key: str = "", newsdata_key: str = ""):
        self.newsapi = NewsApiClient(api_key=newsapi_key)
        self.guardian_key = guardian_key
        self.reuters_key = reuters_key
        self.newsdata_key = newsdata_key
        self.guardian_url = "https://content.guardianapis.com/search"
        self.reuters_url = "https://api.reuters.com/v2/feed/news"
        self.bbc_feeds = [
            "http://feeds.bbci.co.uk/news/world/rss.xml",
            "http://feeds.bbci.co.uk/news/technology/rss.xml",
            "http://feeds.bbci.co.uk/news/business/rss.xml"
        ]

    async def get_newsapi_news(self, limit: int) -> List[Dict[str, Any]]:
        try:
            print("\n=== Fetching from NewsAPI...")
            results = self.newsapi.get_everything(
                language='en',
                sort_by='publishedAt',
                page_size=limit,
                q='*'
            )
            articles = results.get("articles", [])
            print(f"NewsAPI found {len(articles)} articles")
            
            formatted_articles = [{
                "title": article["title"],
                "url": article["url"],
                "source": f"NewsAPI - {article['source']['name']}",
                "published_at": article["publishedAt"]
            } for article in articles]
            print(f"Successfully processed {len(formatted_articles)} articles from NewsAPI")
            return formatted_articles
        except Exception as e:
            print(f"Error getting NewsAPI news: {str(e)}")
            return []

    async def get_guardian_news(self, limit: int) -> List[Dict[str, Any]]:
        try:
            print("\n=== Fetching from Guardian...")
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.guardian_url,
                    params={
                        "api-key": self.guardian_key,
                        "page-size": limit,
                        "order-by": "newest",
                        "show-fields": "all"
                    }
                )
                data = response.json()
                articles = data.get("response", {}).get("results", [])
                print(f"Guardian found {len(articles)} articles")
                
                formatted_articles = [{
                    "title": article["webTitle"],
                    "url": article["webUrl"],
                    "source": "The Guardian",
                    "published_at": article["webPublicationDate"]
                } for article in articles]
                print(f"Successfully processed {len(formatted_articles)} articles from Guardian")
                return formatted_articles
        except Exception as e:
            print(f"Error getting Guardian news: {str(e)}")
            return []

    async def get_bbc_news(self, limit: int) -> List[Dict[str, Any]]:
        try:
            print("\n=== Fetching from BBC...")
            all_articles = []
            for feed_url in self.bbc_feeds:
                feed = feedparser.parse(feed_url)
                articles = feed.entries[:limit]
                all_articles.extend([{
                    "title": entry.title,
                    "url": entry.link,
                    "source": "BBC News",
                    "published_at": entry.published
                } for entry in articles])
            print(f"BBC found {len(all_articles)} articles")
            print(f"Successfully processed {len(all_articles)} articles from BBC")
            return all_articles
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

    async def get_newsdata_news(self, limit: int) -> List[Dict[str, Any]]:
        try:
            print("\n=== Fetching from NewsData.io...")
            api = NewsDataApiClient(apikey=self.newsdata_key)
            response = api.news_api(
                language="en",
                category=["world", "science", "other"],  # Categorías solicitadas
            )
            
            if response["status"] == "success":
                articles = response.get("results", [])
                print(f"NewsData.io found {len(articles)} articles")
                formatted_articles = [{
                    "title": article["title"],
                    "url": article["link"],
                    "source": f"NewsData.io - {article.get('source_id', 'Unknown')}",
                    "published_at": article["pubDate"]
                } for article in articles]
                print(f"Successfully processed {len(formatted_articles)} articles from NewsData.io")
                return formatted_articles
            else:
                print(f"NewsData.io API error: {response.get('results', {}).get('message', 'Unknown error')}")
                return []
        except Exception as e:
            print(f"Error getting NewsData.io news: {str(e)}")
            return []

    async def get_latest_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        # Aseguramos un mínimo de 20 artículos y un máximo de 30
        limit = max(20, min(limit, 30))
        # Calculamos cuántos artículos queremos de cada fuente
        # Pedimos un poco más para tener suficientes
        per_source_limit = (limit // 4) + 5  # Dividimos el límite entre las 4 fuentes
        tasks = [
            self.get_newsapi_news(per_source_limit),
            self.get_guardian_news(per_source_limit),
            self.get_bbc_news(per_source_limit),
            self.get_newsdata_news(per_source_limit)
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
        min_per_source = 5  # Mínimo 5 por fuente
        target_per_source = max(limit // len(news_by_source), min_per_source)
        
        # Primera pasada: asegurar el mínimo por fuente
        for source, news in news_by_source.items():
            sorted_news = sorted(news, key=lambda x: x["published_at"], reverse=True)
            all_news.extend(sorted_news[:min_per_source])
        
        # Segunda pasada: agregar artículos adicionales hasta alcanzar el objetivo
        remaining_slots = limit - len(all_news)
        if remaining_slots > 0:
            additional_per_source = remaining_slots // len(news_by_source)
            if additional_per_source > 0:
                for source, news in news_by_source.items():
                    sorted_news = sorted(news, key=lambda x: x["published_at"], reverse=True)
                    # Excluimos los que ya agregamos
                    remaining_news = sorted_news[min_per_source:min_per_source + additional_per_source]
                    all_news.extend(remaining_news)
        
        # Ordenamos todas las noticias por fecha
        all_news.sort(key=lambda x: x["published_at"], reverse=True)
        
        print(f"Distribution of news:")
        for source in set(n["source"] for n in all_news):
            count = sum(1 for n in all_news if n["source"] == source)
            print(f"{source}: {count} articles")
        
        return all_news[:limit]
