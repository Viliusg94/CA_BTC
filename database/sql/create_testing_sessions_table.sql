-- Testavimo sesijų (testing_sessions) lentelės sukūrimo skriptas

-- Sukuriame testing_sessions lentelę, jei ji dar neegzistuoja
CREATE TABLE IF NOT EXISTS testing_sessions (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL UNIQUE,
    model_id VARCHAR(36),
    dataset_name VARCHAR(100),
    test_type VARCHAR(50) DEFAULT 'accuracy',
    test_params TEXT,
    results TEXT,
    testing_status VARCHAR(20) DEFAULT 'pending',
    success BOOLEAN,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Išoriniai raktai
    CONSTRAINT fk_testing_session FOREIGN KEY (session_id) 
        REFERENCES user_sessions(id) ON DELETE CASCADE,
    CONSTRAINT fk_testing_model FOREIGN KEY (model_id) 
        REFERENCES models(id) ON DELETE SET NULL
);

-- Sukuriame indeksus efektyvesnei paieškai
CREATE INDEX IF NOT EXISTS idx_testing_session_id ON testing_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_testing_model_id ON testing_sessions(model_id);
CREATE INDEX IF NOT EXISTS idx_testing_status ON testing_sessions(testing_status);