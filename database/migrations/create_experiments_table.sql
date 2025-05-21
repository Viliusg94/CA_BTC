-- Eksperimentų lentelės migracijos skriptas
-- Šis skriptas sukuria eksperimentų lentelę duomenų bazėje

-- Tikriname ir kuriame eksperimentų lentelę
CREATE TABLE IF NOT EXISTS experiments (
    id VARCHAR(36) PRIMARY KEY,                    -- Unikalus eksperimento ID (UUID)
    name VARCHAR(255) NOT NULL,                    -- Eksperimento pavadinimas
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Sukūrimo data
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Paskutinio atnaujinimo data
    status VARCHAR(50) NOT NULL DEFAULT 'naujas',  -- Eksperimento statusas
    metadata TEXT,                                 -- Papildoma informacija JSON formatu
    creator_id VARCHAR(36),                        -- Eksperimento kūrėjo ID
    description TEXT,                              -- Eksperimento aprašymas
    FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE SET NULL -- Ištrinus vartotoją, nustatoma į NULL
);

-- Indeksai lentelei duomenų išgavimo optimizavimui
CREATE INDEX IF NOT EXISTS idx_experiments_name ON experiments(name);
CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status);
CREATE INDEX IF NOT EXISTS idx_experiments_creator_id ON experiments(creator_id);

-- Informacinis pranešimas pabaigus vykdymą
SELECT 'Eksperimentų lentelė sukurta sėkmingai' AS rezultatas;