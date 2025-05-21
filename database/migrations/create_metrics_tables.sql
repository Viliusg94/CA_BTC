-- Metrikų lentelių migracijos skriptas
-- Šis skriptas sukuria visas reikalingas lenteles ir indeksus metrikoms

-- -------------------------------
-- NAUDOTOJŲ METRIKŲ LENTELĖ
-- -------------------------------

-- Tikriname ir kuriame naudotojų metrikų lentelę
CREATE TABLE IF NOT EXISTS user_metrics (
    id VARCHAR(36) PRIMARY KEY,                    -- Unikalus metrikos ID
    user_id VARCHAR(36) NOT NULL,                  -- Naudotojo ID, kuriam priklauso metrika
    metric_type VARCHAR(50) NOT NULL,              -- Metrikos tipas (accuracy, usage, performance)
    metric_name VARCHAR(100) NOT NULL,             -- Metrikos pavadinimas
    numeric_value FLOAT,                           -- Skaitinė metrikos reikšmė
    string_value VARCHAR(255),                     -- Tekstinė metrikos reikšmė
    time_period VARCHAR(20),                       -- Laiko periodas (daily, weekly, monthly, yearly)
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Metrikos užregistravimo laikas
    metadata TEXT,                                 -- Papildoma informacija JSON formatu
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE -- Ištrinus naudotoją, ištrinamos jo metrikos
);

-- Indeksai naudotojų metrikų lentelei duomenų išgavimo optimizavimui
CREATE INDEX IF NOT EXISTS idx_user_metrics_user_id ON user_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_user_metrics_metric_type ON user_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_user_metrics_metric_name ON user_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_user_metrics_timestamp ON user_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_metrics_time_period ON user_metrics(time_period);

-- -------------------------------
-- MODELIŲ METRIKŲ LENTELĖ
-- -------------------------------

-- Tikriname ir kuriame modelių metrikų lentelę
CREATE TABLE IF NOT EXISTS model_metrics (
    id VARCHAR(36) PRIMARY KEY,                    -- Unikalus metrikos ID
    model_id VARCHAR(36) NOT NULL,                 -- Modelio ID, kuriam priklauso metrika
    user_id VARCHAR(36),                           -- Naudotojo ID, kuris atliko matavimą
    metric_type VARCHAR(50) NOT NULL,              -- Metrikos tipas (accuracy, training, testing)
    metric_name VARCHAR(100) NOT NULL,             -- Metrikos pavadinimas
    value FLOAT NOT NULL,                          -- Metrikos reikšmė
    dataset_name VARCHAR(100),                     -- Duomenų rinkinio pavadinimas
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Metrikos užregistravimo laikas
    metadata TEXT,                                 -- Papildoma informacija JSON formatu
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE, -- Ištrinus modelį, ištrinamos jo metrikos
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL  -- Ištrinus naudotoją, jo reikšmė nustatoma į NULL
);

-- Indeksai modelių metrikų lentelei duomenų išgavimo optimizavimui
CREATE INDEX IF NOT EXISTS idx_model_metrics_model_id ON model_metrics(model_id);
CREATE INDEX IF NOT EXISTS idx_model_metrics_user_id ON model_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_model_metrics_metric_type ON model_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_model_metrics_metric_name ON model_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_model_metrics_timestamp ON model_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_model_metrics_dataset ON model_metrics(dataset_name);

-- -------------------------------
-- SESIJŲ METRIKŲ LENTELĖ
-- -------------------------------

-- Tikriname ir kuriame sesijų metrikų lentelę
CREATE TABLE IF NOT EXISTS session_metrics (
    id VARCHAR(36) PRIMARY KEY,                    -- Unikalus metrikos ID
    session_id VARCHAR(36) NOT NULL,               -- Sesijos ID, kuriai priklauso metrika
    metric_type VARCHAR(50) NOT NULL,              -- Metrikos tipas (duration, resource, performance)
    metric_name VARCHAR(100) NOT NULL,             -- Metrikos pavadinimas
    numeric_value FLOAT,                           -- Skaitinė metrikos reikšmė
    string_value VARCHAR(255),                     -- Tekstinė metrikos reikšmė
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Metrikos užregistravimo laikas
    metadata TEXT,                                 -- Papildoma informacija JSON formatu
    FOREIGN KEY (session_id) REFERENCES user_sessions(id) ON DELETE CASCADE -- Ištrinus sesiją, ištrinamos jos metrikos
);

-- Indeksai sesijų metrikų lentelei duomenų išgavimo optimizavimui
CREATE INDEX IF NOT EXISTS idx_session_metrics_session_id ON session_metrics(session_id);
CREATE INDEX IF NOT EXISTS idx_session_metrics_metric_type ON session_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_session_metrics_metric_name ON session_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_session_metrics_timestamp ON session_metrics(timestamp);

-- Informacinis pranešimas pabaigus vykdymą
SELECT 'Metrikų lentelės ir indeksai sukurti sėkmingai' AS rezultatas;