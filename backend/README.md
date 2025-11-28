# SaladOverflow Backend

A FastAPI backend for the SaladOverflow discussion platform using MariaDB.

## Quick Start

1. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set Up Environment**

   ```bash
   copy .env.example .env
   # Edit .env with your MariaDB database and Redis configuration
   ```

3. **Run the Application**

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Alternative Docs: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app initialization
│   └── config.py        # Application configuration
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
└── .env               # Your environment variables (do not commit)
```

## Development

- The API runs on port 8000 by default
- Auto-reload is enabled in development mode
- FastAPI provides automatic API documentation
- CORS is configured for frontend development

## Next Steps

You can extend this basic setup by adding:

- Database models and connections
- Authentication endpoints
- API routes for posts, comments, voting
- Redis caching integration
- Database migrations with Alembic
