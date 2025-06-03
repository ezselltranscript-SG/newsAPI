from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from config import Settings
from news import NewsAggregator

app = FastAPI(title="News Aggregator API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load settings
settings = Settings()
news_aggregator = NewsAggregator(settings.newsapi_key, settings.guardian_key, "")

@app.get("/")
def read_root():
    return {"message": "Welcome to News Aggregator API"}

@app.get("/news/latest")
async def get_latest_news(limit: Optional[int] = 10):
    news = await news_aggregator.get_latest_news(limit)
    return {"news": news}
