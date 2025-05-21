-- Eksperimentų rezultatų lentelės migracijos skriptas
-- Šis skriptas sukuria eksperimentų rezultatų lentelę duomenų bazėje

-- Tikriname ir kuriame eksperimentų rezultatų lentelę
CREATE TABLE IF NOT EXISTS experiment_results (
    id VARCHAR(36) PRIMARY KEY,                    -- Unikalus rezultato ID (UUID)
    experiment_id VARCHAR(36) NOT NULL,            -- Išorinis raktas į eksperimentų lentelę
    metric_name VARCHAR(100) NOT NULL,             -- Metrikos pavadinimas
    metric_value TEXT NOT NULL,                    -- Metrikos reikšmė (skaičius)
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Sukūrimo data
    stage VARCHAR(50),                             -- Etapas (treniravimas, validacija, testavimas)
    notes TEXT,                                    -- Papildomi komentarai ar pastabos
    FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE -- Ištrinus eksperimentą, ištrinami ir rezultatai
);

-- Indeksai lentelei duomenų išgavimo optimizavimui
CREATE INDEX IF NOT EXISTS idx_experiment_results_experiment_id ON experiment_results(experiment_id);
CREATE INDEX IF NOT EXISTS idx_experiment_results_metric_name ON experiment_results(metric_name);

-- Informacinis pranešimas pabaigus vykdymą
SELECT 'Eksperimentų rezultatų lentelė sukurta sėkmingai' AS rezultatas;