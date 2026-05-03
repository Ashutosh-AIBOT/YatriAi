# YATRA AI — MASTER SYSTEM BUILD GUIDE
> Full-Stack AI Travel Super-App | Java + Python + Node.js | Scale-Ready | 100% Free Tier
> Instruction file for AI agents (Claude, Gemini, GPT-4, Codex) — execute section by section

---

## AGENT EXECUTION RULES (READ FIRST — NON-NEGOTIABLE)

```
1. NEVER create all files at once. Build ONE component → test → fix → commit → next.
2. NEVER hardcode any secret. All keys go in .env files. All .env files are in .gitignore.
3. NEVER skip tests. Every service gets a test file before moving to the next service.
4. NEVER use SELECT * in any query. Always specify columns.
5. NEVER do DB calls inside loops. Always batch.
6. NEVER return unbounded lists. All endpoints are paginated.
7. After every component: run the component, verify it works, then git commit.
8. Big O check before writing any algorithm: O(n²) or worse = rewrite first.
9. Every external API call gets: timeout, retry with backoff, circuit breaker, fallback.
10. Every Redis cache entry gets explicit TTL. No TTL = bug.
```

---

## SYSTEM OVERVIEW

```
YatraAI is an AI-native travel planning super-app.
One chatbot collects all user intent via structured conversation stages.
Six specialized sub-agents run in parallel to fetch transport, hotels, food, maps, cabs, places.
Results are aggregated, ranked by user preferences using RAG, and rendered as editable itinerary cards.
Real-time updates via Kafka push price changes and ETA updates to chat.
```

**Core User Flow:**
```
Register → Preference Wizard → Start Trip Chat → 7-Stage Collection →
Parallel Agent Dispatch → Aggregate + Rank → Generate Plan →
Show Editable Stage Cards + Live Map → Real-time Updates
```

---

## MONOREPO FOLDER STRUCTURE

```
yatra-ai/
├── gateway/                    # Spring Boot — API gateway, auth, routing
│   ├── src/main/java/com/yatraai/gateway/
│   │   ├── config/             # SecurityConfig, CorsConfig, SwaggerConfig
│   │   ├── filter/             # JwtAuthFilter, RateLimitFilter, TraceIdFilter
│   │   ├── controller/         # AuthController, UserController, HealthController
│   │   ├── service/            # AuthService, UserService, TokenService
│   │   ├── model/              # User, UserPreference, RefreshToken (JPA entities)
│   │   ├── dto/                # RegisterRequest, LoginRequest, UserDTO, PreferenceDTO
│   │   ├── repository/         # UserRepository, PreferenceRepository
│   │   └── exception/          # GlobalExceptionHandler, ApiException
│   ├── src/test/java/com/yatraai/gateway/
│   └── pom.xml
│
├── orchestrator/               # FastAPI + LangGraph — AI brain
│   ├── app/
│   │   ├── main.py             # FastAPI app, lifespan, routers
│   │   ├── graph/              # LangGraph state machine
│   │   │   ├── state.py        # TripState TypedDict
│   │   │   ├── nodes.py        # All graph node functions
│   │   │   └── graph.py        # StateGraph assembly
│   │   ├── agents/             # Sub-agents
│   │   │   ├── transport.py    # Flight + train + bus
│   │   │   ├── cab.py          # Ola + Uber comparison
│   │   │   ├── hotel.py        # Hotel search + rank
│   │   │   ├── food.py         # Restaurant + meal slots
│   │   │   ├── places.py       # POI + attractions
│   │   │   └── maps.py         # Google Maps routes + waypoints
│   │   ├── rag/                # RAG pipeline
│   │   │   ├── embedder.py     # Embed user prefs
│   │   │   ├── retriever.py    # pgvector similarity search
│   │   │   └── ranker.py       # Re-rank results by user vector
│   │   ├── services/           # Business logic
│   │   │   ├── aggregator.py   # Merge agent outputs
│   │   │   ├── plan_builder.py # LLM structured plan generation
│   │   │   └── cache.py        # Redis cache-aside helpers
│   │   ├── models/             # Pydantic schemas
│   │   │   ├── trip.py         # TripRequest, TripPlan, StageModel
│   │   │   └── user.py         # UserContext, PreferenceModel
│   │   ├── db/                 # Database
│   │   │   ├── session.py      # Async SQLAlchemy engine
│   │   │   └── crud.py         # All DB operations
│   │   ├── kafka/              # Event streaming
│   │   │   ├── producer.py     # Publish events
│   │   │   └── consumer.py     # Price monitor, booking updates
│   │   └── config.py           # All env vars via pydantic-settings
│   ├── tests/
│   └── requirements.txt
│
├── notification/               # Node.js — WebSocket push service
│   ├── src/
│   │   ├── server.js           # Express + Socket.io
│   │   ├── kafka/consumer.js   # Kafka consumer → push to socket
│   │   ├── redis/session.js    # Socket session management
│   │   └── middleware/auth.js  # Verify JWT on socket connect
│   ├── tests/
│   └── package.json
│
├── frontend/                   # Next.js + React + TailwindCSS
│   ├── app/
│   │   ├── (auth)/             # Login, Register, Onboarding pages
│   │   ├── (app)/              # Protected: Chat, Map, Itinerary pages
│   │   └── layout.tsx
│   ├── components/
│   │   ├── chat/               # ChatWindow, MessageBubble, StageCard
│   │   ├── map/                # MapView, RouteOverlay, POIMarker
│   │   ├── itinerary/          # PlanCard, StageEditor, BookmarkBadge
│   │   └── comparison/         # CabTable, FlightTable, HotelGrid
│   ├── hooks/                  # useWebSocket, useTrip, useGeolocation
│   ├── lib/                    # API client, auth utils
│   └── package.json
│
├── infra/                      # Docker + deployment
│   ├── docker-compose.yml      # Local dev: all services + deps
│   ├── docker-compose.test.yml # Test environment
│   └── k8s/                    # Kubernetes manifests (production)
│
├── scripts/                    # DB migrations, seed data
│   └── migrations/
│
├── .env.example                # Template — copy to .env, fill values
├── .gitignore                  # MUST include .env, *.pem, *secret*
└── README.md
```

---

## PHASE 0 — ENVIRONMENT SETUP (Do This First)

### Step 0.1 — Prerequisites
```bash
# Verify all tools installed
java --version          # 21+ required (virtual threads)
python --version        # 3.11+ required
node --version          # 20+ required
docker --version        # for local deps
mvn --version           # Maven 3.9+
git --version

# If any missing — install before proceeding
```

### Step 0.2 — Clone and Init Monorepo
```bash
mkdir yatra-ai && cd yatra-ai
git init
echo "node_modules/\n.env\n*.pem\n*secret*\ntarget/\n__pycache__/\n.venv/\n*.pyc" > .gitignore
```

### Step 0.3 — Create .env.example
```bash
cat > .env.example << 'EOF'
# === DATABASE ===
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/yatraai
POSTGRES_URL=jdbc:postgresql://host:5432/yatraai
POSTGRES_USER=yatraai
POSTGRES_PASSWORD=changeme

# === REDIS ===
REDIS_URL=redis://default:token@host:port

# === KAFKA ===
KAFKA_BOOTSTRAP_SERVERS=host:9092
KAFKA_API_KEY=your_key
KAFKA_API_SECRET=your_secret

# === AI / LLM ===
GROQ_API_KEY=your_groq_key
GOOGLE_MAPS_API_KEY=your_maps_key

# === TRAVEL APIs ===
AMADEUS_CLIENT_ID=your_id
AMADEUS_CLIENT_SECRET=your_secret
RAPIDAPI_KEY=your_key
ZOMATO_API_KEY=your_key
OLA_API_KEY=your_key
UBER_SERVER_TOKEN=your_token

# === AUTH ===
JWT_SECRET=minimum_32_char_random_string_here
JWT_EXPIRY_MINUTES=15
REFRESH_TOKEN_EXPIRY_DAYS=7

# === APP ===
GATEWAY_PORT=8080
ORCHESTRATOR_PORT=8001
NOTIFICATION_PORT=3001
FRONTEND_PORT=3000
EOF

cp .env.example .env
# NOW fill .env with real values — never commit .env
```

### Step 0.4 — Local Dependencies via Docker
```yaml
# infra/docker-compose.yml
version: '3.9'
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: yatraai
      POSTGRES_USER: yatraai
      POSTGRES_PASSWORD: localdev
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru

  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on: [zookeeper]
    ports: ["9092:9092"]
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'true'

volumes:
  pgdata:
```

```bash
cd infra && docker-compose up -d
# Verify all containers running
docker-compose ps
```

---

## PHASE 1 — DATABASE SCHEMA (Run Before Any Service)

### Step 1.1 — Init Schema
```sql
-- scripts/migrations/001_init.sql
-- Run this ONCE on fresh DB

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    language VARCHAR(10) DEFAULT 'en',
    is_active BOOLEAN DEFAULT true,
    deleted_at TIMESTAMPTZ,                    -- soft delete
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;

-- Refresh tokens
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_refresh_user ON refresh_tokens(user_id);

-- User preferences (one row per user)
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    is_vegetarian BOOLEAN DEFAULT false,
    cuisine_tags TEXT[] DEFAULT '{}',
    travel_style VARCHAR(50) DEFAULT 'balanced',  -- budget|balanced|luxury
    budget_tier VARCHAR(20) DEFAULT 'medium',      -- low|medium|high
    interest_tags TEXT[] DEFAULT '{}',
    language_pref VARCHAR(10) DEFAULT 'en',
    allow_ai_suggestions BOOLEAN DEFAULT true,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User preference vectors (for RAG)
CREATE TABLE user_pref_vectors (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    embedding vector(768),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_pref_vectors ON user_pref_vectors USING ivfflat(embedding vector_cosine_ops);

-- Trips
CREATE TABLE trips (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    origin VARCHAR(200) NOT NULL,
    destination VARCHAR(200) NOT NULL,
    start_date DATE,
    end_date DATE,
    trip_type VARCHAR(20) DEFAULT 'explore',       -- urgent|explore
    group_size INT DEFAULT 1,
    total_budget NUMERIC(12,2),
    currency VARCHAR(5) DEFAULT 'INR',
    status VARCHAR(20) DEFAULT 'planning',          -- planning|confirmed|completed|cancelled
    current_stage INT DEFAULT 1,                    -- which collection stage we're on (1-7)
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_trips_user ON trips(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_trips_status ON trips(status, created_at DESC);

-- Trip stages (each card in the itinerary)
CREATE TABLE trip_stages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    stage_type VARCHAR(30) NOT NULL,               -- transport|hotel|food|place|cab
    stage_order INT NOT NULL,
    day_number INT DEFAULT 1,
    data JSONB NOT NULL DEFAULT '{}',              -- flexible: all provider data here
    is_confirmed BOOLEAN DEFAULT false,
    is_bookmarked BOOLEAN DEFAULT false,
    last_edited_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_stages_trip ON trip_stages(trip_id, stage_order);

-- Bookmarks
CREATE TABLE bookmarks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    trip_id UUID REFERENCES trips(id),
    bookmark_type VARCHAR(30) NOT NULL,            -- place|hotel|restaurant|route
    external_id VARCHAR(200),
    name VARCHAR(300) NOT NULL,
    metadata JSONB DEFAULT '{}',
    priority VARCHAR(20) DEFAULT 'backup',          -- must_visit|backup
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_bookmarks_user ON bookmarks(user_id);

-- Chat history
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    role VARCHAR(20) NOT NULL,                     -- user|assistant|system
    content TEXT NOT NULL,
    stage_at_time INT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_chat_trip ON chat_messages(trip_id, created_at);

-- Price alerts
CREATE TABLE price_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    trip_id UUID NOT NULL REFERENCES trips(id),
    alert_type VARCHAR(30) NOT NULL,               -- flight|hotel|cab
    reference_id VARCHAR(200) NOT NULL,
    threshold_price NUMERIC(12,2),
    last_known_price NUMERIC(12,2),
    last_checked_at TIMESTAMPTZ,
    notified_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_alerts_active ON price_alerts(is_active, last_checked_at);

-- Search result cache (DB-level, Redis is primary)
CREATE TABLE search_cache (
    cache_key VARCHAR(500) PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    result JSONB NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_cache_expires ON search_cache(expires_at);
```

```bash
# Apply migration
psql $DATABASE_URL -f scripts/migrations/001_init.sql
echo "Migration 001 applied"
```

---

## PHASE 2 — GATEWAY SERVICE (Spring Boot)

### Step 2.1 — Bootstrap
```bash
cd gateway
# pom.xml dependencies required:
# spring-boot-starter-web
# spring-boot-starter-security
# spring-boot-starter-data-jpa
# spring-boot-starter-data-redis
# spring-boot-starter-actuator
# spring-boot-starter-validation
# postgresql (driver)
# jjwt-api + jjwt-impl + jjwt-jackson (0.12.x)
# bucket4j-core + bucket4j-redis (rate limiting)
# springdoc-openapi-starter-webmvc-ui
# lombok
```

### Step 2.2 — application.yml
```yaml
# gateway/src/main/resources/application.yml
server:
  port: ${GATEWAY_PORT:8080}
  shutdown: graceful
  compression:
    enabled: true
    mime-types: application/json,text/html
    min-response-size: 1024

spring:
  datasource:
    url: ${POSTGRES_URL}
    username: ${POSTGRES_USER}
    password: ${POSTGRES_PASSWORD}
    hikari:
      maximum-pool-size: 20
      minimum-idle: 5
      connection-timeout: 30000
      idle-timeout: 600000
  jpa:
    hibernate:
      ddl-auto: validate         # NEVER use create-drop in prod
    open-in-view: false          # prevents lazy loading issues
  data:
    redis:
      url: ${REDIS_URL}
  lifecycle:
    timeout-per-shutdown-phase: 30s
  threads:
    virtual:
      enabled: true              # Java 21 virtual threads

app:
  jwt:
    secret: ${JWT_SECRET}
    expiry-minutes: ${JWT_EXPIRY_MINUTES:15}
  refresh-token:
    expiry-days: ${REFRESH_TOKEN_EXPIRY_DAYS:7}
  rate-limit:
    requests-per-minute: 100
  cors:
    allowed-origins: ${CORS_ALLOWED_ORIGINS:http://localhost:3000}

management:
  endpoints:
    web:
      exposure:
        include: health,metrics,info
  endpoint:
    health:
      show-details: when-authorized
```

### Step 2.3 — Core Files to Create (in order)

**Order matters — create and test each before next:**

```
1. AppConfig.java              — @ConfigurationProperties binding
2. User.java                   — JPA entity (id, name, email, passwordHash, isActive, deletedAt)
3. UserPreference.java         — JPA entity (userId FK, isVegetarian, cuisineTags[], etc)
4. RefreshToken.java           — JPA entity
5. UserRepository.java         — extends JpaRepository, findByEmail, findByEmailAndDeletedAtIsNull
6. UserPreferenceRepository.java
7. RefreshTokenRepository.java — findByTokenHashAndRevokedAtIsNull
8. UserDTO.java                — safe output (no passwordHash)
9. RegisterRequest.java        — @Valid annotations: @Email, @NotBlank, @Size
10. LoginRequest.java
11. PreferenceUpdateRequest.java
12. ApiResponse.java           — standard wrapper: {success, data, error, traceId}
13. ApiException.java          — extends RuntimeException with HttpStatus
14. GlobalExceptionHandler.java — @RestControllerAdvice catches all
15. TraceIdFilter.java         — generates UUID traceId, puts in MDC + response header
16. TokenService.java          — generateAccessToken, generateRefreshToken, validateToken
17. AuthService.java           — register, login, refresh, logout
18. UserService.java           — getProfile, updatePreferences, softDelete
19. JwtAuthFilter.java         — OncePerRequestFilter, extracts JWT, sets SecurityContext
20. RateLimitFilter.java       — Bucket4j + Redis, per-user 100 req/min
21. SecurityConfig.java        — permit /auth/**, /health/**, require auth elsewhere
22. CorsConfig.java            — from env CORS_ALLOWED_ORIGINS
23. AuthController.java        — POST /api/v1/auth/register, /login, /refresh, /logout
24. UserController.java        — GET /api/v1/users/me, PATCH /preferences
25. HealthController.java      — GET /health/live, /health/ready (check DB + Redis)
```

### Step 2.4 — Key Implementation Rules

```java
// TraceIdFilter.java — ALWAYS first in filter chain
@Component
@Order(1)
public class TraceIdFilter extends OncePerRequestFilter {
    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain) {
        String traceId = UUID.randomUUID().toString();
        MDC.put("traceId", traceId);
        res.setHeader("X-Trace-Id", traceId);
        try {
            chain.doFilter(req, res);
        } finally {
            MDC.clear();  // MUST clear MDC — prevents memory leak in thread pool
        }
    }
}

// GlobalExceptionHandler.java — catch everything
@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(ApiException.class)
    public ResponseEntity<ApiResponse<Void>> handleApi(ApiException ex) {
        return ResponseEntity.status(ex.getStatus())
            .body(ApiResponse.error(ex.getStatus().value(), ex.getMessage(), MDC.get("traceId")));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Void>> handleValidation(MethodArgumentNotValidException ex) {
        String msg = ex.getBindingResult().getFieldErrors().stream()
            .map(e -> e.getField() + ": " + e.getDefaultMessage())
            .collect(Collectors.joining(", "));
        return ResponseEntity.badRequest()
            .body(ApiResponse.error(400, msg, MDC.get("traceId")));
    }
    // + Exception.class fallback returning 500
}
```

### Step 2.5 — Test Gateway
```bash
cd gateway
mvn test                    # unit tests must pass
mvn spring-boot:run &       # start service

# Test sequence:
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"Test@1234"}'
# Expected: 201 with userId

curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test@1234"}'
# Expected: 200 with accessToken + refreshToken

curl http://localhost:8080/health/ready
# Expected: {"status":"UP","database":"UP","redis":"UP"}

echo "Gateway OK — git commit"
git add gateway/ && git commit -m "feat(gateway): auth, user profile, rate limiting"
```

---

## PHASE 3 — ORCHESTRATOR SERVICE (FastAPI + LangGraph)

### Step 3.1 — Bootstrap
```bash
cd orchestrator
python -m venv .venv && source .venv/bin/activate

pip install fastapi==0.115.0 uvicorn[standard]==0.30.0 \
  langgraph==0.2.0 langchain-groq==0.1.9 langchain-core==0.3.0 \
  sqlalchemy[asyncio]==2.0.35 asyncpg==0.29.0 alembic==1.13.0 \
  redis[asyncio]==5.0.8 aiokafka==0.11.0 \
  pydantic==2.8.0 pydantic-settings==2.4.0 \
  httpx==0.27.0 tenacity==9.0.0 \
  sentence-transformers==3.0.0 \
  python-jose[cryptography]==3.3.0 \
  pytest==8.3.0 pytest-asyncio==0.23.0 httpx pytest-mock

pip freeze > requirements.txt
```

### Step 3.2 — config.py (All env vars)
```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str
    kafka_bootstrap_servers: str
    kafka_api_key: str = ""
    kafka_api_secret: str = ""
    groq_api_key: str
    google_maps_api_key: str
    amadeus_client_id: str
    amadeus_client_secret: str
    rapidapi_key: str
    zomato_api_key: str
    ola_api_key: str
    uber_server_token: str
    jwt_secret: str
    gateway_base_url: str = "http://localhost:8080"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

### Step 3.3 — TripState (LangGraph State)
```python
# app/graph/state.py
from typing import TypedDict, List, Optional, Dict, Any
from datetime import date

class TripState(TypedDict):
    trip_id: str
    user_id: str
    user_prefs: Dict[str, Any]          # loaded from DB at start

    # Stage collection (filled one by one via chat)
    origin: Optional[str]
    destination: Optional[str]
    trip_type: Optional[str]            # urgent | explore
    stop_count: Optional[int]
    requested_stops: Optional[List[str]]
    transport_modes: Optional[List[str]] # flight|train|bus|cab|mixed
    start_date: Optional[str]
    end_date: Optional[str]
    total_budget: Optional[float]
    group_size: Optional[int]
    hotel_stars: Optional[int]
    is_vegetarian: Optional[bool]
    cuisine_preferences: Optional[List[str]]
    interest_tags: Optional[List[str]]
    allow_suggestions: Optional[bool]
    current_stage: int                  # 1-7

    # Chat history for context
    messages: List[Dict[str, str]]      # [{role, content}]

    # Agent results (filled after stage 7)
    transport_results: Optional[Dict]
    cab_results: Optional[Dict]
    hotel_results: Optional[Dict]
    food_results: Optional[Dict]
    places_results: Optional[Dict]
    map_results: Optional[Dict]

    # Final plan
    final_plan: Optional[Dict]
    error: Optional[str]
```

### Step 3.4 — Graph Nodes
```python
# app/graph/nodes.py
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
import asyncio
from .state import TripState
from ..agents import transport, cab, hotel, food, places, maps
from ..services import aggregator, plan_builder, cache
from ..db.crud import save_trip_state, save_chat_message

llm = ChatGroq(model="llama-3.1-70b-versatile", temperature=0.3)

STAGE_QUESTIONS = {
    1: "Where would you like to travel from and to? (e.g. Kanpur to Noida)",
    2: "Is this an urgent trip (direct route) or are you looking to explore and enjoy?",
    3: "How would you like to travel? (flight / train / bus / cab / mix)",
    4: "When are you planning to travel, what's your budget, and how many people?",
    5: "Are you vegetarian? Any cuisine preferences? What hotel star rating do you prefer?",
    6: "What kind of places interest you? (forts, nature, food streets, malls, etc.) Should I suggest more places along the way?",
    7: "Perfect! Let me generate your complete travel plan now. One moment..."
}

async def stage_router(state: TripState) -> TripState:
    """Determine next stage question based on current stage."""
    stage = state["current_stage"]
    if stage > 7:
        return state
    question = STAGE_QUESTIONS[stage]
    # If stage 2 and trip_type == explore: ask about stops
    if stage == 2 and state.get("trip_type") == "explore":
        question = "Great! How many stops would you like, and any specific places you must visit?"
    state["messages"].append({"role": "assistant", "content": question})
    await save_chat_message(state["trip_id"], state["user_id"], "assistant", question, stage)
    return state

async def extract_stage_info(state: TripState, user_input: str) -> TripState:
    """Use LLM to extract structured info from user's natural language answer."""
    stage = state["current_stage"]
    extract_prompt = f"""
Extract travel information from user input for stage {stage}.
Current state: {state}
User said: "{user_input}"
Return JSON with ONLY the fields that are clearly mentioned. 
Stage {stage} fields to extract: {get_stage_fields(stage)}
Return ONLY valid JSON, nothing else.
"""
    response = await llm.ainvoke([HumanMessage(content=extract_prompt)])
    try:
        import json, re
        extracted = json.loads(re.search(r'\{.*\}', response.content, re.DOTALL).group())
        state.update(extracted)
    except Exception:
        pass  # keep existing state if extraction fails

    state["messages"].append({"role": "user", "content": user_input})
    state["current_stage"] = stage + 1
    await save_trip_state(state)
    return state

def get_stage_fields(stage: int) -> str:
    fields = {
        1: "origin (str), destination (str)",
        2: "trip_type (urgent|explore), stop_count (int), requested_stops (list)",
        3: "transport_modes (list of: flight|train|bus|cab)",
        4: "start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), total_budget (float), group_size (int)",
        5: "is_vegetarian (bool), cuisine_preferences (list), hotel_stars (int 1-5)",
        6: "interest_tags (list), allow_suggestions (bool)",
        7: ""
    }
    return fields.get(stage, "")

async def dispatch_agents(state: TripState) -> TripState:
    """Run all 6 agents in parallel — never sequentially."""
    results = await asyncio.gather(
        transport.search(state),
        cab.compare(state),
        hotel.search(state),
        food.find(state),
        places.discover(state),
        maps.build_route(state),
        return_exceptions=True     # don't fail all if one agent fails
    )
    labels = ["transport_results", "cab_results", "hotel_results",
              "food_results", "places_results", "map_results"]
    for label, result in zip(labels, results):
        if isinstance(result, Exception):
            state[label] = {"error": str(result), "data": []}
        else:
            state[label] = result
    return state

async def build_plan(state: TripState) -> TripState:
    """Generate structured itinerary from aggregated results."""
    aggregated = await aggregator.merge(state)
    ranked = await aggregator.rank_by_preferences(aggregated, state["user_prefs"])
    final_plan = await plan_builder.generate(state, ranked)
    state["final_plan"] = final_plan
    return state
```

### Step 3.5 — Graph Assembly
```python
# app/graph/graph.py
from langgraph.graph import StateGraph, END
from .state import TripState
from .nodes import stage_router, extract_stage_info, dispatch_agents, build_plan

def should_collect_more(state: TripState) -> str:
    return "collect" if state["current_stage"] <= 7 else "dispatch"

def build_trip_graph():
    g = StateGraph(TripState)
    g.add_node("route",    stage_router)
    g.add_node("extract",  extract_stage_info)
    g.add_node("dispatch", dispatch_agents)
    g.add_node("plan",     build_plan)

    g.set_entry_point("route")
    g.add_edge("route", "extract")
    g.add_conditional_edges("extract", should_collect_more, {
        "collect": "route",
        "dispatch": "dispatch"
    })
    g.add_edge("dispatch", "plan")
    g.add_edge("plan", END)
    return g.compile()

trip_graph = build_trip_graph()
```

### Step 3.6 — Agent Pattern (follow for ALL 6 agents)
```python
# app/agents/transport.py — template pattern for all agents
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from ..config import settings
from ..services.cache import get_cached, set_cached

TIMEOUT = httpx.Timeout(10.0, connect=3.0)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def _fetch_flights(origin: str, dest: str, date: str) -> list:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        # Amadeus free tier
        token = await _get_amadeus_token(client)
        r = await client.get(
            "https://test.api.amadeus.com/v2/shopping/flight-offers",
            headers={"Authorization": f"Bearer {token}"},
            params={"originLocationCode": origin, "destinationLocationCode": dest,
                    "departureDate": date, "adults": 1, "max": 5}
        )
        r.raise_for_status()
        return r.json().get("data", [])

async def search(state: dict) -> dict:
    origin = state["origin"]
    dest = state["destination"]
    date = state.get("start_date", "")
    modes = state.get("transport_modes", ["train", "bus"])

    cache_key = f"transport:{origin}:{dest}:{date}"
    if cached := await get_cached(cache_key):
        return cached

    results = {"flights": [], "trains": [], "buses": [], "error": None}

    try:
        if "flight" in modes:
            results["flights"] = await _fetch_flights(origin, dest, date)
    except Exception as e:
        results["error"] = f"Flight search failed: {e}"
        results["flights"] = []    # fallback: empty, don't crash

    # Add train/bus similarly...

    await set_cached(cache_key, results, ttl=1800)  # 30 min cache
    return results
```

### Step 3.7 — Redis Cache Helper
```python
# app/services/cache.py
import json
import redis.asyncio as aioredis
from ..config import settings

_redis = None

async def get_redis():
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis

async def get_cached(key: str):
    r = await get_redis()
    val = await r.get(key)
    return json.loads(val) if val else None

async def set_cached(key: str, value, ttl: int = 3600):
    r = await get_redis()
    await r.set(key, json.dumps(value), ex=ttl)  # ALWAYS set TTL

async def delete_cached(key: str):
    r = await get_redis()
    await r.delete(key)
```

### Step 3.8 — main.py
```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .db.session import engine, Base
from .kafka.producer import kafka_producer
from .kafka.consumer import start_price_monitor
from .graph.graph import trip_graph
from .models.trip import ChatRequest, ChatResponse
from .services.cache import get_redis
import asyncio, uuid

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await kafka_producer.start()
    asyncio.create_task(start_price_monitor())
    yield
    # Shutdown
    await kafka_producer.stop()

app = FastAPI(title="YatraAI Orchestrator", version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware,
    allow_origins=[settings.gateway_base_url],
    allow_methods=["*"], allow_headers=["*"])

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, bg: BackgroundTasks):
    """Main chat endpoint — routes user message through LangGraph."""
    # Load or init trip state
    r = await get_redis()
    state_key = f"trip_state:{req.trip_id}"
    raw = await r.get(state_key)

    if raw:
        import json
        state = json.loads(raw)
    else:
        state = _init_state(req)

    # Inject user message and run graph
    state["messages"].append({"role": "user", "content": req.message})
    result = await trip_graph.ainvoke(state)

    # Persist updated state
    await r.set(state_key, json.dumps(result), ex=86400)  # 24h TTL

    # Extract last assistant message
    assistant_msgs = [m for m in result["messages"] if m["role"] == "assistant"]
    last_msg = assistant_msgs[-1]["content"] if assistant_msgs else ""

    return ChatResponse(
        trip_id=req.trip_id,
        message=last_msg,
        stage=result["current_stage"],
        plan=result.get("final_plan")
    )

def _init_state(req: ChatRequest) -> dict:
    return {
        "trip_id": req.trip_id,
        "user_id": req.user_id,
        "user_prefs": req.user_prefs or {},
        "current_stage": 1,
        "messages": [],
        "origin": None, "destination": None,
        "trip_type": None, "stop_count": None,
        "requested_stops": None, "transport_modes": None,
        "start_date": None, "end_date": None,
        "total_budget": None, "group_size": 1,
        "hotel_stars": None, "is_vegetarian": None,
        "cuisine_preferences": None, "interest_tags": None,
        "allow_suggestions": True,
        "transport_results": None, "cab_results": None,
        "hotel_results": None, "food_results": None,
        "places_results": None, "map_results": None,
        "final_plan": None, "error": None
    }

@app.get("/health")
async def health():
    return {"status": "ok", "service": "orchestrator"}
```

### Step 3.9 — Test Orchestrator
```bash
cd orchestrator
source .venv/bin/activate
pytest tests/ -v              # all tests must pass

uvicorn app.main:app --reload --port 8001 &

# Test chat
curl -X POST http://localhost:8001/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"trip_id":"test-1","user_id":"user-1","message":"I want to travel from Kanpur to Noida","user_prefs":{}}'
# Expected: stage 1 extraction + stage 2 question in response

echo "Orchestrator OK"
git add orchestrator/ && git commit -m "feat(orchestrator): LangGraph stage engine + parallel agents"
```

---

## PHASE 4 — NOTIFICATION SERVICE (Node.js + Socket.io)

### Step 4.1 — Bootstrap
```bash
cd notification
npm init -y
npm install express socket.io aiokafka kafkajs redis jsonwebtoken dotenv
npm install --save-dev jest supertest nodemon
```

### Step 4.2 — server.js
```javascript
// notification/src/server.js
require('dotenv').config();
const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');
const { startKafkaConsumer } = require('./kafka/consumer');
const { verifyToken } = require('./middleware/auth');

const app = express();
const httpServer = createServer(app);

const io = new Server(httpServer, {
  cors: { origin: process.env.FRONTEND_URL, methods: ["GET", "POST"] }
});

// Socket rooms keyed by userId — supports multiple devices
const userSockets = new Map();   // userId -> Set<socketId>

io.use(async (socket, next) => {
  const token = socket.handshake.auth.token;
  const user = await verifyToken(token);
  if (!user) return next(new Error("Unauthorized"));
  socket.userId = user.id;
  next();
});

io.on('connection', (socket) => {
  const uid = socket.userId;
  if (!userSockets.has(uid)) userSockets.set(uid, new Set());
  userSockets.get(uid).add(socket.id);

  socket.on('disconnect', () => {
    userSockets.get(uid)?.delete(socket.id);
  });
});

// Called by Kafka consumer to push to user
function pushToUser(userId, event) {
  const sockets = userSockets.get(userId);
  if (sockets) {
    sockets.forEach(sid => io.to(sid).emit('travel_update', event));
  }
}

app.get('/health', (_, res) => res.json({ status: 'ok' }));

const PORT = process.env.NOTIFICATION_PORT || 3001;
httpServer.listen(PORT, async () => {
  console.log(`Notification service on :${PORT}`);
  await startKafkaConsumer(pushToUser);
});

module.exports = { app, pushToUser };
```

### Step 4.3 — Kafka Consumer
```javascript
// notification/src/kafka/consumer.js
const { Kafka } = require('kafkajs');

const kafka = new Kafka({
  clientId: 'notification-service',
  brokers: [process.env.KAFKA_BOOTSTRAP_SERVERS],
  ssl: process.env.KAFKA_API_KEY ? true : false,
  sasl: process.env.KAFKA_API_KEY ? {
    mechanism: 'plain',
    username: process.env.KAFKA_API_KEY,
    password: process.env.KAFKA_API_SECRET
  } : undefined
});

const TOPICS = ['price.alert', 'booking.confirmed', 'cab.eta.update'];

async function startKafkaConsumer(pushFn) {
  const consumer = kafka.consumer({ groupId: 'notification-group' });
  await consumer.connect();
  await consumer.subscribe({ topics: TOPICS, fromBeginning: false });

  await consumer.run({
    eachMessage: async ({ topic, message }) => {
      try {
        const event = JSON.parse(message.value.toString());
        if (event.userId) {
          pushFn(event.userId, { topic, ...event });
        }
      } catch (err) {
        console.error('Kafka message parse error:', err);
        // Dead letter: log and continue — never crash consumer
      }
    }
  });
}

module.exports = { startKafkaConsumer };
```

### Step 4.4 — Test Notification Service
```bash
cd notification
npm test
node src/server.js &
curl http://localhost:3001/health
echo "Notification OK"
git add notification/ && git commit -m "feat(notification): WebSocket push via Kafka"
```

---

## PHASE 5 — FRONTEND (Next.js + React)

### Step 5.1 — Bootstrap
```bash
cd frontend
npx create-next-app@latest . --typescript --tailwind --app --src-dir=false
npm install socket.io-client axios @tanstack/react-query zustand
npm install @googlemaps/js-api-loader
npm install --save-dev @testing-library/react @testing-library/jest-dom jest
```

### Step 5.2 — Key Components to Build (in order)

```
1. lib/api.ts                  — axios instance with JWT interceptor, auto-refresh
2. lib/socket.ts               — socket.io client, connect with JWT, event handlers
3. store/authStore.ts          — Zustand: user, token, setToken, logout
4. store/tripStore.ts          — Zustand: tripId, messages, plan, currentStage
5. app/(auth)/register/page.tsx  — Preference wizard (veg?, cuisine, interests)
6. app/(auth)/login/page.tsx
7. hooks/useGeolocation.ts     — navigator.geolocation with error handling
8. hooks/useWebSocket.ts       — connect, subscribe to travel_update events
9. hooks/useChat.ts            — send message, append to messages, call orchestrator
10. components/chat/ChatWindow.tsx      — message list + input box
11. components/chat/MessageBubble.tsx   — user vs assistant styling
12. components/chat/StageCard.tsx       — itinerary card with Edit button
13. components/map/MapView.tsx          — Google Maps embed, plot waypoints
14. components/comparison/CabTable.tsx  — Ola vs Uber side by side
15. components/comparison/FlightTable.tsx
16. components/comparison/HotelGrid.tsx
17. components/itinerary/BookmarkBadge.tsx
18. app/(app)/chat/page.tsx    — main chat page, combines all components
```

### Step 5.3 — API Client
```typescript
// lib/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_GATEWAY_URL,
  timeout: 15000,
});

// Attach JWT to every request
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
  res => res,
  async err => {
    if (err.response?.status === 401 && !err.config._retry) {
      err.config._retry = true;
      const refresh = localStorage.getItem('refresh_token');
      const { data } = await axios.post(`${process.env.NEXT_PUBLIC_GATEWAY_URL}/api/v1/auth/refresh`,
        { refreshToken: refresh });
      localStorage.setItem('access_token', data.data.accessToken);
      err.config.headers.Authorization = `Bearer ${data.data.accessToken}`;
      return api(err.config);
    }
    return Promise.reject(err);
  }
);

export default api;
```

### Step 5.4 — Chat Page Core
```typescript
// app/(app)/chat/page.tsx
'use client';
import { useState, useEffect, useRef } from 'react';
import { useChat } from '@/hooks/useChat';
import { useWebSocket } from '@/hooks/useWebSocket';
import { ChatWindow } from '@/components/chat/ChatWindow';
import { MapView } from '@/components/map/MapView';
import { PlanView } from '@/components/itinerary/PlanView';

export default function ChatPage() {
  const { messages, plan, currentStage, sendMessage, isLoading } = useChat();
  const { updates } = useWebSocket();

  return (
    <div className="flex h-screen">
      {/* Left: Chat */}
      <div className="w-1/2 flex flex-col border-r">
        <ChatWindow messages={messages} onSend={sendMessage} isLoading={isLoading} />
      </div>
      {/* Right: Map + Plan */}
      <div className="w-1/2 flex flex-col">
        {plan ? <PlanView plan={plan} updates={updates} /> : <MapView />}
      </div>
    </div>
  );
}
```

### Step 5.5 — Test Frontend
```bash
cd frontend
npm run build          # must build with 0 errors
npm run dev &
# Open http://localhost:3000
# Test: register → login → start chat → complete all 7 stages → verify plan renders
echo "Frontend OK"
git add frontend/ && git commit -m "feat(frontend): chat UI, map, itinerary cards"
```

---

## PHASE 6 — KAFKA TOPICS SETUP

```bash
# Create topics with 12 partitions (divisible by 1,2,3,4,6,12 consumers)
kafka-topics.sh --create --bootstrap-server localhost:9092 --topic trip.started        --partitions 12 --replication-factor 1
kafka-topics.sh --create --bootstrap-server localhost:9092 --topic plan.generated      --partitions 12 --replication-factor 1
kafka-topics.sh --create --bootstrap-server localhost:9092 --topic price.alert         --partitions 6  --replication-factor 1
kafka-topics.sh --create --bootstrap-server localhost:9092 --topic booking.confirmed   --partitions 6  --replication-factor 1
kafka-topics.sh --create --bootstrap-server localhost:9092 --topic cab.eta.update      --partitions 6  --replication-factor 1
kafka-topics.sh --create --bootstrap-server localhost:9092 --topic price.alert.DLT     --partitions 3  --replication-factor 1

kafka-topics.sh --list --bootstrap-server localhost:9092
echo "Kafka topics created"
git commit --allow-empty -m "ops: kafka topics provisioned"
```

---

## PHASE 7 — PRICE MONITOR (FastAPI Background Service)

```python
# app/kafka/consumer.py — runs as asyncio background task
from aiokafka import AIOKafkaProducer
from ..db.crud import get_active_alerts, update_alert_price
from ..agents.transport import get_current_price
from ..config import settings
import asyncio, json

kafka_producer = AIOKafkaProducer(
    bootstrap_servers=settings.kafka_bootstrap_servers
)

async def start_price_monitor():
    """Poll price alerts every 30 minutes — runs forever as background task."""
    while True:
        try:
            alerts = await get_active_alerts()  # SELECT only is_active=true
            for alert in alerts:
                current = await get_current_price(alert)
                if current and abs(current - alert.last_known_price) / alert.last_known_price > 0.1:
                    event = {
                        "userId": str(alert.user_id),
                        "tripId": str(alert.trip_id),
                        "type": alert.alert_type,
                        "oldPrice": float(alert.last_known_price),
                        "newPrice": float(current),
                        "message": f"Price changed from ₹{alert.last_known_price:.0f} to ₹{current:.0f}"
                    }
                    await kafka_producer.send(
                        "price.alert",
                        key=str(alert.user_id).encode(),
                        value=json.dumps(event).encode()
                    )
                    await update_alert_price(alert.id, current)
        except Exception as e:
            print(f"Price monitor error: {e}")
        await asyncio.sleep(1800)  # 30 minutes
```

---

## PHASE 8 — INTEGRATION TEST (Full Flow)

```bash
# Run this BEFORE calling any phase done

# 1. Start all services
cd infra && docker-compose up -d
cd ../gateway && mvn spring-boot:run &
cd ../orchestrator && uvicorn app.main:app --port 8001 &
cd ../notification && node src/server.js &
cd ../frontend && npm run dev &

sleep 10  # wait for all to boot

# 2. Health checks
curl http://localhost:8080/health/ready    | python3 -m json.tool
curl http://localhost:8001/health          | python3 -m json.tool
curl http://localhost:3001/health          | python3 -m json.tool

# 3. Register user
REGISTER=$(curl -s -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Ashutosh","email":"ash@test.com","password":"Test@1234"}')
echo $REGISTER

# 4. Login
LOGIN=$(curl -s -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ash@test.com","password":"Test@1234"}')
TOKEN=$(echo $LOGIN | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['accessToken'])")
TRIP_ID=$(python3 -c "import uuid; print(str(uuid.uuid4()))")
USER_ID=$(echo $LOGIN | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['userId'])")

# 5. Full chat flow — simulate all 7 stages
for MSG in \
  "Kanpur to Noida" \
  "I want to explore and enjoy the journey with 2 stops" \
  "Train and cab" \
  "This weekend, budget 5000 rupees, 2 people" \
  "Vegetarian, North Indian food, 3 star hotel" \
  "Forts and street food, yes suggest more places" \
  "Yes go ahead generate the plan"; do
  
  curl -s -X POST http://localhost:8001/api/v1/chat \
    -H "Content-Type: application/json" \
    -d "{\"trip_id\":\"$TRIP_ID\",\"user_id\":\"$USER_ID\",\"message\":\"$MSG\",\"user_prefs\":{}}" \
    | python3 -m json.tool
  sleep 2
done

echo "=== FULL INTEGRATION TEST COMPLETE ==="
git add . && git commit -m "test: full 7-stage trip flow verified"
```

---

## PHASE 9 — PERFORMANCE CHECKLIST (Before Any Deployment)

```bash
# Install k6
sudo apt install k6

# Load test — 1000 concurrent users for 5 minutes
cat > load_test.js << 'EOF'
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '1m', target: 100 },
    { duration: '3m', target: 1000 },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'],
  }
};

export default function () {
  let res = http.get('http://localhost:8080/health/ready');
  check(res, { 'status 200': r => r.status === 200 });
  sleep(1);
}
EOF

k6 run load_test.js
# p95 must be < 500ms, error rate < 1%
# If failing: check Redis hit rate, DB indexes, connection pools
```

---

## PHASE 10 — MULTI-LANGUAGE (Add Last)

```python
# app/services/translator.py
import httpx
from ..config import settings

SUPPORTED_LANGUAGES = ["hi", "ta", "te", "bn", "mr", "gu", "kn", "pa", "en"]

async def translate_to_english(text: str, source_lang: str) -> str:
    """Translate user input to English before processing."""
    if source_lang == "en":
        return text
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.post(
            "https://translation.googleapis.com/language/translate/v2",
            params={"key": settings.google_maps_api_key},  # same key, different API
            json={"q": text, "source": source_lang, "target": "en", "format": "text"}
        )
        return r.json()["data"]["translations"][0]["translatedText"]

async def translate_from_english(text: str, target_lang: str) -> str:
    """Translate assistant response from English to user's language."""
    if target_lang == "en":
        return text
    # Same pattern as above, swap source/target
    ...
```

---

## SECURITY FINAL CHECKLIST

```
[ ] All .env values filled — no placeholder strings in production
[ ] .gitignore covers: .env, *.pem, *secret*, target/, __pycache__/
[ ] JWT secret is 32+ random characters
[ ] CORS only allows your frontend domain (not *)
[ ] Rate limiting active on all public endpoints
[ ] All user inputs validated with @Valid / Pydantic validators
[ ] Password hashed with BCrypt (never MD5, never plain)
[ ] Soft deletes on users — never hard DELETE
[ ] All DB queries use prepared statements (no string concat)
[ ] File uploads: MIME check, UUID rename, store outside webroot
[ ] Refresh tokens stored as hash in DB (not plaintext)
[ ] All API responses strip internal fields (use DTOs)
```

---

## FREE TIER LIMITS — STAY WITHIN

| Service | Free Limit | Our Usage |
|---|---|---|
| Groq API | 30 req/min, 14400/day | Rate limit in orchestrator |
| Google Maps | $200/month credit | ~500K map loads free |
| Amadeus | Test env unlimited | Use sandbox until launch |
| Confluent Kafka | 10 GB/month | Well within for dev |
| Neon PostgreSQL | 0.5 GB, 3 branches | Fine for MVP |
| Upstash Redis | 10K req/day free | Cache aggressively |
| Vercel | 100 GB bandwidth | Fine for MVP |
| Render | 750 hrs/month | Use for gateway + orchestrator |

---

## GIT COMMIT DISCIPLINE

```bash
# Format: type(scope): description
# Types: feat | fix | test | refactor | ops | docs

# After every component:
git add <files>
git commit -m "feat(gateway): JWT auth + rate limiting"

# After every phase:
git tag -a v0.X -m "Phase X complete"
git push origin main --tags
```

---

## PHASE COMPLETION ORDER

```
Phase 0  → Environment + Docker deps         [1 day]
Phase 1  → DB schema applied                 [0.5 day]
Phase 2  → Gateway: auth, profile, rate limit [1 week]
Phase 3  → Orchestrator: LangGraph + agents  [2 weeks]
Phase 4  → Notification: WebSocket + Kafka   [3 days]
Phase 5  → Frontend: chat + map + itinerary  [2 weeks]
Phase 6  → Kafka topics                      [1 day]
Phase 7  → Price monitor                     [3 days]
Phase 8  → Integration test — full flow      [2 days]
Phase 9  → Load test + performance tuning    [3 days]
Phase 10 → Multi-language (Hindi first)      [1 week]

TOTAL MVP: ~10-12 weeks solo
```

---

*Generated for YatraAI — build phase by phase, test before moving on, commit after every component.*
