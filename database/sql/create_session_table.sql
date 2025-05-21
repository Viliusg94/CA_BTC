-- Naudotojų sesijų (user_sessions) lentelės sukūrimo skriptas

-- Sukuriame user_sessions lentelę, jei ji dar neegzistuoja
CREATE TABLE IF NOT EXISTS user_sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    session_type VARCHAR(20) NOT NULL COMMENT 'Sesijos tipas (training/testing/general)',
    start_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    ip_address VARCHAR(45) NULL,
    user_agent TEXT NULL,
    metadata TEXT NULL COMMENT 'Papildoma informacija apie sesiją (JSON)',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Išorinis raktas, siejantis su users lentele
    CONSTRAINT fk_session_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE
);

-- Sukuriame indeksus efektyvesnei paieškai
CREATE INDEX IF NOT EXISTS idx_session_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_session_type ON user_sessions(session_type);
CREATE INDEX IF NOT EXISTS idx_session_status ON user_sessions(status);
CREATE INDEX IF NOT EXISTS idx_session_active ON user_sessions(is_active);