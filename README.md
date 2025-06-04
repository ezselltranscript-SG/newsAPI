# News Aggregator API

A FastAPI microservice that aggregates news from multiple sources including NewsAPI, The Guardian, and BBC News.

## Features

- Fetches latest news from multiple sources
- Combines and sorts news by publication date
- RESTful API endpoint
- CORS enabled for easy integration
- Docker support
- Ready for deployment on Render

## API Endpoints

- `GET /`: Welcome message
- `GET /news/latest`: Get latest news from all sources
  - Query parameter: `limit` (optional, default: 10)

## Environment Variables

The following environment variables are required:

- `NEWSAPI_KEY`: Your NewsAPI.org API key
- `GUARDIAN_KEY`: Your Guardian API key
- `REUTERS_KEY`: Your Reuters API key (optional)
- `NEWSDATA_KEY`: Your NewsData.io API key

## Local Development

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables
4. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

## Docker

Build and run with Docker:

```bash
docker build -t news-aggregator .
docker run -p 10000:10000 news-aggregator
```

## Deployment on Render

1. Fork this repository
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Add your environment variables in Render dashboard
5. Deploy!
