# Neurix — Repository Intelligence

Neurix accepts a public GitHub repository URL, reads relevant repository files without executing repository code, and generates a clear technical explanation.

## Architecture

```text
GitHub URL
    ↓
React + Vite frontend
    ↓ HTTP
FastAPI backend
    ↓
GitPython → Repository Processor → Groq LLM
```

## Backend

```bash
python -m pip install -r requirements.txt
python backend/main.py
```

FastAPI runs on `http://127.0.0.1:8000`.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite runs on `http://localhost:3000`.

For local development, copy `frontend/.env.example` to `frontend/.env` or use the built-in Vite proxy. For a separately hosted frontend, set:

```text
VITE_BACKEND_URL=https://your-fastapi-service.example.com
```

## API

- `GET /health`
- `GET /models`
- `GET /config`
- `POST /explain`
- `POST /analyze` — compatibility alias

Example request:

```json
{
  "url": "https://github.com/owner/repository",
  "max_files": 12
}
```

## Safety

Neurix only clones and reads public repository files. It does not execute code from analyzed repositories.

Do not commit `.env` or API keys.
