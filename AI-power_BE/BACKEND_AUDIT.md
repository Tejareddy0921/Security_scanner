# Backend audit and stabilization

**Reviewed:** 2026-11-01
**Scope:** all application modules, project configuration, Docker setup, and tests.

## Initial diagnosis

The repository had only a minimal FastAPI root route. The implementation modules, tests, `requirements.txt`, `Dockerfile`, and `.gitignore` were empty. Several package directories and Python files had leading spaces in their names, which would have broken normal imports as soon as the intended modules were used.

The normal import-path modules initially formed only a minimal FastAPI root route. Separate older implementations existed under whitespace-prefixed names, but those files were not reachable through the application’s standard imports. The initial runtime dependency graph was therefore:

| Area | Initial state |
|---|---|
| Startup | `uvicorn → app.main → FastAPI → GET /` |
| Imports | `app.main → fastapi`; all other modules were empty |
| Database | No client, collections, repositories, or indexes |
| Authentication | No registration, login, JWT, password hashing, or user dependency |
| AI | No classifier, prompt, cloud provider client, or result validation |
| API | Only `GET /`; all requested endpoints were absent |

## Implemented dependency graphs

**Startup:** `Uvicorn → app.main → routers + configuration + middleware → lifespan → AsyncMongoClient and optional AsyncGroq client`. Mongo connections remain lazy so a process can start while MongoDB is unavailable; database-backed endpoints return a controlled `503` when they need MongoDB.

**Imports:** `main → routers → dependency factories → services → repositories`; the detection service also calls the classifier, which uses RAG, prompt, and Groq services. Repositories depend on Mongo collection interfaces. Schemas and utility mappers do not import routers or services. The running app uses standard package paths. Whitespace-prefixed legacy source files still exist as unreferenced files; they are not part of the import graph.

**Database:** `lifespan → AsyncMongoClient → DATABASE_NAME → users / scam_reports / detection_results`. Mongo `_id`, `user_id`, and `report_id` values are BSON `ObjectId`s. IDs are converted to strings only at API response boundaries. Required indexes are created once on first authenticated/database-backed use: unique `users.email`, `scam_reports.user_id`, `scam_reports.created_at`, `detection_results.user_id`, and `detection_results.report_id`.

**Authentication:** `register/login request schema → auth router → AuthService → UserRepository → users`. Password hashing and verification use pwdlib Argon2 and run in a worker thread. JWTs use HS256 with required `sub` and `exp` claims. `get_current_user` validates the token, validates the subject as an ObjectId, loads the user, and rejects inactive or missing accounts.

**AI:** `POST /detection/analyze → DetectionService → ScamClassifier → RAGService → PromptService → GroqService → Groq Chat Completions API → AIResult validation → DetectionRepository → status update`. The report is stored before inference; dependency or output failures mark it `failed`. Raw model output is not returned to clients.

## Post-migration incident findings

The supplied logs contain two separate cases. A `401` from a protected route before login is expected. On page refresh with a cached token, however, the frontend previously rendered protected pages before `/users/me` finished validating that token. This allowed history/profile requests to race session restoration and produced avoidable `401`s for expired sessions. `AuthContext` now gates protected routes until restoration succeeds, clears a genuinely invalid session, and offers a retry if validation fails for a transient reason. API requests use `Authorization: Bearer <token>`; a `401` only clears the session if it still belongs to the token that failed.

The authenticated history `503` was caused by a shared detection-service dependency that required a configured Groq client even for MongoDB reads. History and detection detail now construct the service without an AI client and query the caller's MongoDB records directly. MongoDB failures still return a database `503`; they are not disguised as successful empty history. The configured `MONGODB_DATABASE` and `CLIENT_URL` environment names are accepted as aliases for `DATABASE_NAME` and `CORS_ORIGINS`.

Analysis still requires a valid backend `GROQ_API_KEY`. The backend `.env` path is now resolved relative to the application package, so IDE launch working directories do not silently skip the key. Missing key configuration is reported as a safe service-unavailable error and marks the pending report `failed`; no detection result is stored. Provider rate limits map to `429`, provider authentication/request rejection and malformed structured output map to `502`, and timeouts, connection failures, and temporary upstream outages map to `503`. Logs record safe error types/statuses without credentials, tokens, prompts, or provider response bodies. The React API layer coalesces duplicate in-flight GETs, and analysis requests are aborted when the user edits the submitted content or leaves the page.

## Legacy source paths

The workspace also contains older files under whitespace-prefixed paths such as `app/ models/`, `app/ services/`, `app/dependencies/ auth.py`, `app/repositories/ detection_repository.py`, `app/routers/ users.py`, and `app/utils/ helpers.py`. The frontend has a separate `src/pages/ Login.jsx`. These files differ from the normalized modules and have no import references; the running backend and frontend use `app/models/`, `app/services/`, `app/dependencies/auth.py`, `app/repositories/detection_repository.py`, `app/routers/users.py`, `app/utils/helpers.py`, and `src/pages/Login.jsx`. They remain untouched to preserve their contents, so edits in the whitespace-prefixed files will not change the running application.

## Priority findings and resolution

| Priority | Finding | Resolution / remaining work |
|---|---|---|
| P0 | The normal import-path modules had only a minimal app, while older implementations sat under whitespace-prefixed names and were not imported. | Implemented the active modules under standard package paths. The unreferenced legacy files remain in place and are documented below. |
| P1 | Authentication, password protection, ownership checks, and safe response filtering did not exist. | Added Argon2 hashing, HS256 JWT validation, active-account checks, user-scoped repository filters, and safe response schemas. Production configuration now requires an explicit `SECRET_KEY`. |
| P1 | Login has no built-in rate limit or brute-force lockout. | Keep enforcement at a shared API gateway or add a distributed rate limiter before public deployment; process-local limits would not protect multiple workers. |
| P2 | All requested auth, users, scam, and detection endpoints were absent. | Implemented the endpoints listed below and added validation and controlled errors. |
| P2 | MongoDB and AI provider behavior had no implementation. | Added native async PyMongo, lifecycle cleanup, indexes, Groq SDK calls, structured response parsing, and AI validation. MongoDB CRUD is covered with service fakes; no live MongoDB integration test was performed. |
| P3 | Services, repositories, schemas, models, and tests were placeholders. | Implemented the layer boundaries and service coverage. RAG remains explicitly incomplete pending a vector store. |
| P4 | No request-size cap, useful request logging, indexes, or deployment configuration existed. | Added request-size enforcement, request ID/status/duration logs, model/error logs, index initialization, `.env.example`, `.gitignore`, dependencies, and Docker configuration. |

## API map

| Method | Endpoint | Authentication | Behavior |
|---|---|---|---|
| POST | `/auth/register` | No | Normalize email, hash password, create account, return safe user |
| POST | `/auth/login` | No | Verify account and return bearer token |
| GET | `/users/me` | Yes | Return current user profile |
| PUT | `/users/me` | Yes | Update email and/or display name |
| DELETE | `/users/me` | Yes | Deactivate account; preserve related records |
| POST | `/scams/report` | Yes | Create report using the authenticated user ID |
| GET | `/scams/my-reports` | Yes | List the caller’s reports |
| GET | `/scams/{report_id}` | Yes | Return a report only when owned by the caller |
| POST | `/detection/analyze` | Yes | Store report, run validated inference, save result and update report |
| GET | `/detection/history` | Yes | List the caller’s detections |
| GET | `/detection/{detection_id}` | Yes | Return a detection only when owned by the caller |

Scam and detection lookups constrain both `_id` and `user_id` in the Mongo query. Invalid IDs produce a client error; IDs belonging to another user are reported as not found.

## File-by-file review

The table below describes the active, standard import-path modules. Those modules began as placeholders except `app/main.py`, which had only a root route. Older, divergent source files under whitespace-prefixed paths are documented separately; they are not used by the running application.

| File | Status | Problem / impact | Fix in corrected code |
|---|---|---|---|
| `app/main.py` | ✅ Corrected | No routers, lifecycle, middleware, or safe error mapping; required APIs were unreachable. | Registers routers, lifespan, CORS, size limit, request logging, domain/database error handlers, and root liveness route. |
| `app/core/config.py` | ✅ Corrected | No settings or secret policy; existing MongoDB/CORS environment names were not recognized, and a relative `.env` path depended on the launch directory. | Pydantic Settings loads the backend `.env` from an absolute package-relative path, validates bounds, restricts JWT algorithm to HS256, supports `DATABASE_NAME`/`MONGODB_DATABASE` and `CORS_ORIGINS`/`CLIENT_URL`, and requires explicit production secret. |
| `app/core/database.py` | ✅ Corrected | No connection lifecycle or indexes. | Owns one async PyMongo client, shared Groq client, cleanup, and required indexes. |
| `app/core/security.py` | ✅ Corrected | No password or token handling. | Uses Argon2 and HS256 JWT; validates expiration and subject. |
| `app/core/errors.py` | ✅ Corrected | No domain error boundary. | Defines service errors mapped to safe HTTP statuses in `main.py`. |
| `app/core/middleware.py` | ✅ Corrected | Requests had no overall body-size cap. | Rejects malformed lengths and bodies larger than configured limit. |
| `app/models/user.py` | ✅ Corrected | No user document shape. | Defines the Mongo user document, including `password_hash` and timestamps. |
| `app/models/scam_report.py` | ✅ Corrected | No report shape or controlled status/source values. | Defines report document, source, and status enums. |
| `app/models/detection_result.py` | ✅ Corrected | No detection document or label set. | Defines ObjectId relations and allowed classifier labels. |
| `app/schemas/auth.py` | ✅ Corrected | No registration/login validation. | Validates email/name/password while preserving password characters; accepts `full_name`, `fullName`, or `name`; rejects unrelated extra fields. |
| `app/schemas/user.py` | ✅ Corrected | No safe profile or update schema. | Excludes hashes, validates updates, and rejects empty or unsupported changes. |
| `app/schemas/scam.py` | ✅ Corrected | No report validation; clients could have supplied unsupported fields. | Caps content, validates source, rejects blank content and extra fields such as `user_id`. |
| `app/schemas/detection.py` | ✅ Corrected | No request or untrusted AI-result validation. | Enforces labels, numeric confidence in `[0,1]`, bounded text/lists, and response shape. |
| `app/routers/auth.py` | ✅ Corrected | No auth endpoints. | Exposes registration and login with response models and status codes. |
| `app/routers/users.py` | ✅ Corrected | No profile operations. | Exposes authenticated GET/PUT and soft-deactivation DELETE. |
| `app/routers/scam.py` | ✅ Corrected | No report endpoints or ownership dependency. | Exposes create/list/get routes; user ID comes from JWT dependency. |
| `app/routers/detection.py` | ✅ Corrected | No detection routes or route ordering. | Exposes analyze/history/detail routes with history before the dynamic ID route. |
| `app/services/auth_service.py` | ✅ Corrected | No registration/login business logic. | Normalizes email, handles duplicate checks, offloads Argon2, issues JWTs, and returns safe user models. |
| `app/services/user_service.py` | ✅ Corrected | No update/deactivation logic. | Handles duplicate email checks, timestamps, profile mapping, and account deactivation. |
| `app/services/scam_service.py` | ✅ Corrected | No report lifecycle. | Creates records from the authenticated user and scopes reads by owner. |
| `app/services/detection_service.py` | ✅ Corrected | No AI orchestration or persistence. | Coordinates report, classifier, result storage, status updates, history, ownership, and safe logs. |
| `app/repositories/user_repository.py` | ✅ Corrected | No persistence operations. | Contains only user collection create/find/update/deactivate operations. |
| `app/repositories/scam_repository.py` | ✅ Corrected | No report persistence. | Contains report create, owner-scoped find/list, and status update operations. |
| `app/repositories/detection_repository.py` | ✅ Corrected | No detection persistence. | Contains detection create, owner-scoped find, and history operations. |
| `app/dependencies/auth.py` | ✅ Corrected | No current-user dependency. | Validates bearer token, ObjectId, user existence, and active status before returning the user. |
| `app/dependencies/services.py` | ✅ Corrected | No service construction boundary; history could not be built when Groq was unconfigured. | Builds services from request-scoped resources and permits history/detail reads without constructing an AI client. |
| `app/ai/classifier.py` | ✅ Corrected | No classifier orchestration. | Runs retrieval, prompt construction, and Groq classification in sequence. |
| `app/ai/prompt_service.py` | ✅ Corrected | No prompt or untrusted-input boundary. | Marks submitted text as untrusted and requests the expected JSON fields. |
| `app/ai/groq_service.py` | ✅ Corrected | No Groq client, timeout, or output validation. | Uses `AsyncGroq`, maps provider failures to safe errors, requests strict JSON schema output, and validates `AIResult`. |
| `app/ai/rag_service.py` | ⚠️ Placeholder | No vector store or retrieval implementation exists. | Explicitly returns no context; documented as incomplete and does not claim RAG works. |
| `app/utils/helpers.py` | ✅ Corrected | No ObjectId/time helpers. | Centralizes safe ObjectId parsing and UTC timestamp formatting. |
| `app/utils/mappers.py` | ✅ Corrected | Response mapping had no shared boundary. | Maps stored user documents to password-free response schema. |
| `app/__init__.py` and package `__init__.py` files | ✅ Correct | Package markers were empty. | Kept empty; they correctly mark packages without import side effects. |

Configuration and test files were empty too. `requirements.txt` now contains only runtime dependencies; `requirements-dev.txt` adds pytest. The Dockerfile uses Python 3.12, installs runtime dependencies, sets production mode, and starts Uvicorn without embedding secrets. `.gitignore` excludes `.env`, environments, bytecode, and pytest artifacts; `.dockerignore` prevents local secrets and development files from entering the image. `.env.example` documents all required settings.

## Security, async, and operational notes

- Repositories accept explicit BSON IDs and never use client-supplied Mongo filters. All related IDs stay `ObjectId` in Mongo.
- Passwords, hashes, tokens, secrets, message bodies, Mongo URIs, and raw LLM output are not written to logs or responses.
- Password hashing is moved off the event loop with `asyncio.to_thread`; MongoDB and Groq calls are async. The rest of request processing uses in-memory validation/mapping.
- `DELETE /users/me` performs soft deactivation. This keeps report history and foreign-key-like references intact; the tradeoff is that personal data remains in Mongo and requires a separate retention/deletion policy.
- RAG is a placeholder until a vector database and retrieval policy are selected.
- No live MongoDB CRUD was exercised. Configure `MONGODB_URL`, `DATABASE_NAME`, and `SECRET_KEY` before production; ensure existing duplicate emails are resolved before the unique index is created.
- Apply shared rate limits to registration and login at the gateway or in a distributed limiter before public exposure. Add monitoring/readiness checks for MongoDB if deployment health must represent database availability.
- Frontend session restoration and token rejection are handled in `AI_power_FB/AI-Powered Scam Detection System/src/context/AuthContext.jsx`, `src/App.jsx`, and `src/services/api.js`; analysis cancellation is handled in `src/pages/ScamInput.jsx` and passed through `src/services/scamService.js`.
- The migration incident changes also update `app/core/errors.py`, `app/dependencies/services.py`, `app/services/detection_service.py`, `app/ai/groq_service.py`, `app/main.py`, `app/dependencies/auth.py`, `app/core/config.py`, and regression cases in `tests/test_api.py`, `tests/test_config.py`, and `tests/test_detection.py`.

## Verification

- `env/bin/python -m pytest -q` — **55 passed**, including backend-relative `.env` resolution, JWT expiry/invalid-token cases, ownership checks, history without Groq, database failure handling, mocked provider rate-limit/provider failures, malformed AI output, and analysis persistence behavior.
- `env/bin/python -m compileall -q app tests` — passed.
- `env/bin/python -m pip check` — no broken requirements.
- Frontend `npm run build` — passed with Vite.
- No live Groq request, live MongoDB CRUD, or browser-driven React flow was exercised. Automated backend tests use provider and repository fakes; the frontend verification was a production build.
