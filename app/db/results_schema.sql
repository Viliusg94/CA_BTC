-- Schemos skriptas rezultatų lentelėms, kuris bus pridėtas prie esamos duomenų bazės
-- Šis skriptas turėtų būti suderinamas su jūsų naudojama MySQL duomenų baze

-- Prognozių lentelė
CREATE TABLE IF NOT EXISTS predictions (
    id VARCHAR(36) PRIMARY KEY,          -- Unikalus prognozės ID (UUID formatu)
    model_id VARCHAR(36) NOT NULL,       -- Nuoroda į modelio ID
    prediction_date DATETIME NOT NULL,   -- Prognozės sukūrimo data ir laikas
    target_date DATETIME NOT NULL,       -- Prognozuojama data
    predicted_value DECIMAL(20,8) NOT NULL,  -- Prognozuojama vertė (iki 8 skaitmenų po kablelio)
    actual_value DECIMAL(20,8),          -- Faktinė vertė (gali būti NULL, jei dar nežinoma)
    interval VARCHAR(10) NOT NULL,       -- Laiko intervalas (1d, 1h, 30m, ...)
    confidence DECIMAL(5,4),             -- Pasitikėjimo lygis (0-1)
    created_at DATETIME NOT NULL,        -- Įrašo sukūrimo laikas
    
    INDEX idx_pred_model (model_id),         -- Indeksas paieškai pagal modelį
    INDEX idx_pred_target (target_date),     -- Indeksas paieškai pagal datą
    INDEX idx_pred_created (created_at)      -- Indeksas paieškai pagal sukūrimo laiką
);

-- Simuliacijų lentelė
CREATE TABLE IF NOT EXISTS simulations (
    id VARCHAR(36) PRIMARY KEY,          -- Unikalus simuliacijos ID
    name VARCHAR(100) NOT NULL,          -- Simuliacijos pavadinimas
    initial_capital DECIMAL(20,8) NOT NULL,  -- Pradinis kapitalas
    fees DECIMAL(6,5) NOT NULL,          -- Prekybos mokesčiai (procentais)
    start_date DATETIME NOT NULL,        -- Simuliacijos pradžios data
    end_date DATETIME NOT NULL,          -- Simuliacijos pabaigos data
    strategy_type VARCHAR(50) NOT NULL,  -- Strategijos tipas
    strategy_params TEXT,                -- Strategijos parametrai (JSON formatu)
    final_balance DECIMAL(20,8),         -- Galutinis balansas
    profit_loss DECIMAL(20,8),           -- Pelnas/nuostolis
    roi DECIMAL(10,4),                   -- Investicijų grąža (procentais)
    max_drawdown DECIMAL(10,4),          -- Didžiausias kritimas (procentais)
    total_trades INT DEFAULT 0,          -- Bendras sandorių skaičius
    winning_trades INT DEFAULT 0,        -- Pelningų sandorių skaičius
    losing_trades INT DEFAULT 0,         -- Nuostolingų sandorių skaičius
    is_completed BOOLEAN DEFAULT 0,      -- Ar simuliacija baigta
    created_at DATETIME NOT NULL,        -- Įrašo sukūrimo laikas
    updated_at DATETIME NOT NULL,        -- Paskutinio atnaujinimo laikas
    
    INDEX idx_sim_strategy (strategy_type),  -- Indeksas paieškai pagal strategiją
    INDEX idx_sim_dates (start_date, end_date), -- Indeksas paieškai pagal datą
    INDEX idx_sim_completed (is_completed)   -- Indeksas paieškai pagal būseną
);

-- Prekybos sandorių lentelė
CREATE TABLE IF NOT EXISTS trades (
    id VARCHAR(36) PRIMARY KEY,          -- Unikalus sandorio ID
    simulation_id VARCHAR(36) NOT NULL,  -- Nuoroda į simuliaciją
    date DATETIME NOT NULL,              -- Sandorio data ir laikas
    type ENUM('buy', 'sell') NOT NULL,   -- Sandorio tipas (pirkimas/pardavimas)
    price DECIMAL(20,8) NOT NULL,        -- Kaina
    amount DECIMAL(20,8) NOT NULL,       -- Kiekis (BTC ar kita valiuta)
    value DECIMAL(20,8) NOT NULL,        -- Vertė (USD ar kita valiuta)
    fee DECIMAL(20,8) NOT NULL,          -- Mokestis
    profit_loss DECIMAL(20,8),           -- Pelnas/nuostolis (tik pardavimo sandoriams)
    created_at DATETIME NOT NULL,        -- Įrašo sukūrimo laikas
    
    INDEX idx_trade_sim (simulation_id),     -- Indeksas paieškai pagal simuliaciją
    INDEX idx_trade_date (date),             -- Indeksas paieškai pagal datą
    INDEX idx_trade_type (type),             -- Indeksas paieškai pagal tipą
    
    FOREIGN KEY (simulation_id) REFERENCES simulations(id) ON DELETE CASCADE
);

-- Metrikų lentelė
CREATE TABLE IF NOT EXISTS metrics (
    id VARCHAR(36) PRIMARY KEY,          -- Unikalus metrikos ID
    name VARCHAR(50) NOT NULL,           -- Metrikos pavadinimas
    value DECIMAL(20,8) NOT NULL,        -- Metrikos reikšmė
    model_id VARCHAR(36),                -- Nuoroda į modelį (gali būti NULL)
    simulation_id VARCHAR(36),           -- Nuoroda į simuliaciją (gali būti NULL)
    period VARCHAR(20),                  -- Laiko periodas (daily, weekly, monthly)
    date DATETIME NOT NULL,              -- Metrikos fiksavimo data
    description TEXT,                    -- Metrikos aprašymas
    created_at DATETIME NOT NULL,        -- Įrašo sukūrimo laikas
    
    INDEX idx_metric_name (name),            -- Indeksas paieškai pagal pavadinimą
    INDEX idx_metric_model (model_id),       -- Indeksas paieškai pagal modelį
    INDEX idx_metric_sim (simulation_id),    -- Indeksas paieškai pagal simuliaciją
    INDEX idx_metric_date (date),            -- Indeksas paieškai pagal datą
    
    CHECK (model_id IS NOT NULL OR simulation_id IS NOT NULL)
);