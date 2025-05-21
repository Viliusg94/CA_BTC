-- Duomenų bazės schemos optimizavimo skriptas
-- Šis skriptas prideda indeksus, atlieka kitus optimizavimo veiksmus

-- ========== PROGNOZIŲ LENTELĖS OPTIMIZAVIMAS ==========

-- Indeksas dažnai naudojamiems filtravimo laukams
CREATE INDEX IF NOT EXISTS idx_predictions_combined 
ON predictions (model_id, target_date);

-- Indeksas duomenų analizei pagal intervalus
CREATE INDEX IF NOT EXISTS idx_predictions_interval 
ON predictions (interval, prediction_date);

-- Indeksas greitai pasiekti naujausias prognozes
CREATE INDEX IF NOT EXISTS idx_predictions_latest 
ON predictions (prediction_date DESC);

-- ========== SIMULIACIJŲ LENTELĖS OPTIMIZAVIMAS ==========

-- Indeksas filtravimui pagal strategiją ir pelningumą
CREATE INDEX IF NOT EXISTS idx_simulations_strategy_profit 
ON simulations (strategy_type, profit_loss);

-- Indeksas simuliacijų laiko intervalams
CREATE INDEX IF NOT EXISTS idx_simulations_timeframe 
ON simulations (start_date, end_date);

-- Indeksas greitai rasti sėkmingiausias simuliacijas
CREATE INDEX IF NOT EXISTS idx_simulations_performance 
ON simulations (roi DESC);

-- ========== SANDORIŲ LENTELĖS OPTIMIZAVIMAS ==========

-- Indeksas greitai rasti sandorius pagal datą ir tipą
CREATE INDEX IF NOT EXISTS idx_trades_date_type 
ON trades (date, type);

-- Indeksas pelningumo analizei
CREATE INDEX IF NOT EXISTS idx_trades_profit 
ON trades (profit_loss);

-- Indeksas pagal kainą (dažnai naudojama filtruojant)
CREATE INDEX IF NOT EXISTS idx_trades_price 
ON trades (price);

-- ========== METRIKŲ LENTELĖS OPTIMIZAVIMAS ==========

-- Indeksas filtravimui pagal pavadinimą ir datą
CREATE INDEX IF NOT EXISTS idx_metrics_name_date 
ON metrics (name, date);

-- Indeksas metrikoms pagal laikotarpį
CREATE INDEX IF NOT EXISTS idx_metrics_period 
ON metrics (period, date);

-- Indeksas susijusioms metrikoms
CREATE INDEX IF NOT EXISTS idx_metrics_related 
ON metrics (name, model_id, simulation_id);

-- ========== OPTIMIZUOTI VIEW DAŽNOMS UŽKLAUSOMS ==========

-- View modelių prognozių tikslumui
CREATE OR REPLACE VIEW prediction_accuracy AS
SELECT 
    model_id,
    COUNT(*) as total_predictions,
    AVG(ABS(predicted_value - actual_value) / actual_value) * 100 as avg_error_percent,
    MIN(prediction_date) as first_prediction,
    MAX(prediction_date) as last_prediction
FROM 
    predictions
WHERE 
    actual_value IS NOT NULL
GROUP BY 
    model_id;

-- View simuliacijų rezultatams
CREATE OR REPLACE VIEW simulation_results AS
SELECT 
    s.id,
    s.name,
    s.strategy_type,
    s.initial_capital,
    s.final_balance,
    s.roi,
    s.total_trades,
    s.winning_trades,
    s.losing_trades,
    (s.winning_trades / NULLIF(s.total_trades, 0)) * 100 as win_rate,
    s.start_date,
    s.end_date,
    DATEDIFF(s.end_date, s.start_date) as duration_days
FROM 
    simulations s
WHERE 
    s.is_completed = 1;

-- View prekybinikų metrikoms
CREATE OR REPLACE VIEW trading_metrics AS
SELECT 
    t.simulation_id,
    COUNT(*) as total_trades,
    SUM(CASE WHEN t.type = 'buy' THEN 1 ELSE 0 END) as buy_trades,
    SUM(CASE WHEN t.type = 'sell' THEN 1 ELSE 0 END) as sell_trades,
    AVG(t.price) as avg_price,
    AVG(CASE WHEN t.profit_loss > 0 THEN t.profit_loss ELSE NULL END) as avg_profit,
    AVG(CASE WHEN t.profit_loss < 0 THEN t.profit_loss ELSE NULL END) as avg_loss,
    MIN(t.date) as first_trade,
    MAX(t.date) as last_trade
FROM 
    trades t
GROUP BY 
    t.simulation_id;