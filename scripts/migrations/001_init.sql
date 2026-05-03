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
    deleted_at TIMESTAMPTZ,
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

-- User preferences
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    is_vegetarian BOOLEAN DEFAULT false,
    cuisine_tags TEXT[] DEFAULT '{}',
    travel_style VARCHAR(50) DEFAULT 'balanced',
    budget_tier VARCHAR(20) DEFAULT 'medium',
    interest_tags TEXT[] DEFAULT '{}',
    language_pref VARCHAR(10) DEFAULT 'en',
    allow_ai_suggestions BOOLEAN DEFAULT true,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User preference vectors
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
    trip_type VARCHAR(20) DEFAULT 'explore',
    group_size INT DEFAULT 1,
    total_budget NUMERIC(12,2),
    currency VARCHAR(5) DEFAULT 'INR',
    status VARCHAR(20) DEFAULT 'planning',
    current_stage INT DEFAULT 1,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_trips_user ON trips(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_trips_status ON trips(status, created_at DESC);

-- Trip stages
CREATE TABLE trip_stages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    stage_type VARCHAR(30) NOT NULL,
    stage_order INT NOT NULL,
    day_number INT DEFAULT 1,
    data JSONB NOT NULL DEFAULT '{}',
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
    bookmark_type VARCHAR(30) NOT NULL,
    external_id VARCHAR(200),
    name VARCHAR(300) NOT NULL,
    metadata JSONB DEFAULT '{}',
    priority VARCHAR(20) DEFAULT 'backup',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_bookmarks_user ON bookmarks(user_id);

-- Chat history
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    role VARCHAR(20) NOT NULL,
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
    alert_type VARCHAR(30) NOT NULL,
    reference_id VARCHAR(200) NOT NULL,
    threshold_price NUMERIC(12,2),
    last_known_price NUMERIC(12,2),
    last_checked_at TIMESTAMPTZ,
    notified_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_alerts_active ON price_alerts(is_active, last_checked_at);

-- Search cache
CREATE TABLE search_cache (
    cache_key VARCHAR(500) PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    result JSONB NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_cache_expires ON search_cache(expires_at);
