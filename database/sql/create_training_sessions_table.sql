-- Treniravimo sesijų (training_sessions) lentelės sukūrimo skriptas

-- Sukuriame training_sessions lentelę, jei ji dar neegzistuoja
CREATE TABLE IF NOT EXISTS training_sessions (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL UNIQUE,
    model_id VARCHAR(36),
    dataset_name VARCHAR(100),
    start_epoch INT DEFAULT 0,
    total_epochs INT,
    current_epoch INT DEFAULT 0,
    learning_rate FLOAT,
    batch_size INT,
    loss_function VARCHAR(50),
    validation_split FLOAT DEFAULT 0.2,
    early_stopping BOOLEAN DEFAULT FALSE,
    checkpoint_enabled BOOLEAN DEFAULT FALSE,
    training_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Išoriniai raktai
    CONSTRAINT fk_training_session FOREIGN KEY (session_id) 
        REFERENCES user_sessions(id) ON DELETE CASCADE,
    CONSTRAINT fk_training_model FOREIGN KEY (model_id) 
        REFERENCES models(id) ON DELETE SET NULL
);

-- Sukuriame indeksus efektyvesnei paieškai
CREATE INDEX IF NOT EXISTS idx_training_session_id ON training_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_training_model_id ON training_sessions(model_id);
CREATE INDEX IF NOT EXISTS idx_training_status ON training_sessions(training_status);