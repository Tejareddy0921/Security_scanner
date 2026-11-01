# ScamGuard – AI-Powered Scam Detection System

ScamGuard uses a React frontend and a FastAPI backend. MongoDB stores accounts, scam reports, detection results, and scan history. The backend sends message analysis requests to Groq using the official asynchronous Python SDK. The Groq API key stays on the backend.

## Requirements

- Python 3.10 or newer
- Node.js and npm
- MongoDB
- A Groq API key

## Configure and run locally

From the project root, configure the backend:

```sh
cd AI-power_BE
[ -f .env ] || cp .env.example .env
```

Edit `AI-power_BE/.env` and set `GROQ_API_KEY` to your key and `SECRET_KEY` to a unique random value of at least 32 characters. Keep `.env` private; never add the Groq key to a frontend variable such as `VITE_*`.

Start the backend after MongoDB is available:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

In another terminal, start the frontend:

```sh
cd "AI_power_FB/AI-Powered Scam Detection System"
npm install
npm run dev
```

The Vite development server forwards API requests to `http://127.0.0.1:8000`. Set `VITE_API_URL` to the backend origin when the frontend and backend run on separate hosts. Add the frontend origin to backend `CORS_ORIGINS`.

## Detection API

Authenticated users submit a message to `POST /detection/analyze`. The backend validates the Groq response, stores the report and detection result in MongoDB, and returns the existing detection response fields. `GET /detection/history` returns the caller’s saved scans. The React scan page displays risk level, category, explanation, indicators, recommendations, and a model confidence estimate; the estimate is not a calibrated probability.

The configured default model is `openai/gpt-oss-20b`. Override it with the backend-only `GROQ_MODEL` setting. `GROQ_TIMEOUT_SECONDS` controls the provider request timeout. Missing API-key configuration leaves the rest of the backend available, while scan requests return a safe service-unavailable response.

## Docker deployment

Build and run the backend from the project root. Supply a private environment file at runtime; do not bake secrets into the image:

```sh
docker build -t scamguard-backend AI-power_BE
docker run --rm -p 8000:8000 --env-file AI-power_BE/.env scamguard-backend
```

The configured MongoDB address must be reachable from the container. For deployments, provide `GROQ_API_KEY`, `GROQ_MODEL`, `GROQ_TIMEOUT_SECONDS`, `MONGODB_URL`, `DATABASE_NAME`, `SECRET_KEY`, and `CORS_ORIGINS` through the deployment platform’s backend secret/environment settings.

Build the frontend image with the public backend origin:

```sh
docker build -f AI_power_FB/Dockerfile \
  --build-arg VITE_API_URL=https://api.example.com \
  -t scamguard-frontend AI_power_FB
docker run --rm -p 8080:8080 scamguard-frontend
```

`VITE_API_URL` is compiled into the public frontend bundle and must contain no secrets. Allow the frontend’s deployed origin in the backend `CORS_ORIGINS` setting.

## Verification

Run backend tests from `AI-power_BE`:

```sh
python -m pytest -q
```

The provider behavior is tested with mocked Groq SDK responses. A live Groq request requires a valid backend `GROQ_API_KEY` and is not part of the automated test suite.
