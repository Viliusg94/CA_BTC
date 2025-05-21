-- Particionavimo strategija dideliems duomenų kiekiams
-- Pastaba: MySQL reikalauja InnoDB lentelių particionavimui PRIMARY KEY laukų įtraukimo į particionavimo išraišką

-- ========== PROGNOZIŲ LENTELĖS PARTICIONAVIMAS PAGAL DATĄ ==========

-- Sukuriame atskirą prognozių lentelę su particionavimu
-- Particionuojame pagal prediction_date (prognozės sukūrimo datą)
CREATE TABLE IF NOT EXISTS predictions_partitioned (
    id VARCHAR(36) NOT NULL,
    model_id VARCHAR(36) NOT NULL,
    prediction_date DATETIME NOT NULL,
    target_date DATETIME NOT NULL,
    predicted_value DECIMAL(20,8) NOT NULL,
    actual_value DECIMAL(20,8),
    interval VARCHAR(10) NOT NULL,
    confidence DECIMAL(5,4),
    error_margin DECIMAL(10,4),
    metadata TEXT,
    created_at DATETIME NOT NULL,
    
    PRIMARY KEY (id, prediction_date),
    INDEX idx_pred_model (model_id),
    INDEX idx_pred_target (target_date),
    INDEX idx_pred_interval (interval)
)
-- Particionuojame duomenis pagal metus ir mėnesius
PARTITION BY RANGE (YEAR(prediction_date) * 100 + MONTH(prediction_date)) (
    -- Pradiniai particionai (galima pridėti daugiau pagal poreikį)
    PARTITION p_before_2023 VALUES LESS THAN (202301),
    PARTITION p_2023_01 VALUES LESS THAN (202302),
    PARTITION p_2023_02 VALUES LESS THAN (202303),
    PARTITION p_2023_03 VALUES LESS THAN (202304),
    PARTITION p_2023_04 VALUES LESS THAN (202305),
    PARTITION p_2023_05 VALUES LESS THAN (202306),
    PARTITION p_2023_06 VALUES LESS THAN (202307),
    PARTITION p_2023_07 VALUES LESS THAN (202308),
    PARTITION p_2023_08 VALUES LESS THAN (202309),
    PARTITION p_2023_09 VALUES LESS THAN (202310),
    PARTITION p_2023_10 VALUES LESS THAN (202311),
    PARTITION p_2023_11 VALUES LESS THAN (202312),
    PARTITION p_2023_12 VALUES LESS THAN (202401),
    PARTITION p_2024_01 VALUES LESS THAN (202402),
    PARTITION p_2024_02 VALUES LESS THAN (202403),
    PARTITION p_2024_03 VALUES LESS THAN (202404),
    PARTITION p_2024_04 VALUES LESS THAN (202405),
    PARTITION p_2024_05 VALUES LESS THAN (202406),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- ========== SANDORIŲ LENTELĖS PARTICIONAVIMAS PAGAL SIMULIACIJĄ IR DATĄ ==========

-- Sukuriame atskirą sandorių lentelę su particionavimu
-- Particionuojame pagal simulation_id (galima suskirstyti sandorius pagal simuliacijas)
CREATE TABLE IF NOT EXISTS trades_partitioned (
    id VARCHAR(36) NOT NULL,
    simulation_id VARCHAR(36) NOT NULL,
    date DATETIME NOT NULL,
    type VARCHAR(4) NOT NULL,
    price DECIMAL(20,8) NOT NULL,
    amount DECIMAL(20,8) NOT NULL,
    value DECIMAL(20,8) NOT NULL,
    fee DECIMAL(20,8) NOT NULL,
    profit_loss DECIMAL(20,8),
    position_id VARCHAR(36),
    market_conditions TEXT,
    created_at DATETIME NOT NULL,
    
    PRIMARY KEY (id, simulation_id),
    INDEX idx_trade_date (date),
    INDEX idx_trade_type (type),
    INDEX idx_trade_profit (profit_loss)
)
-- Naudojame HASH particionavimą pagal simulation_id, kad tolygiai paskirstytume duomenis
PARTITION BY HASH(CONV(SUBSTRING(simulation_id, 1, 8), 16, 10))
PARTITIONS 10;

-- ========== PROCEDŪRA NAUJŲ PARTICIONŲ KŪRIMUI ==========

DELIMITER //

-- Procedūra sukurti naujus particionus ateinantiems mėnesiams
CREATE PROCEDURE add_prediction_partitions()
BEGIN
    DECLARE next_year INT;
    DECLARE next_month INT;
    DECLARE partition_name VARCHAR(50);
    DECLARE partition_value INT;

    -- Nustatome paskutinio particion metus ir mėnesį
    SELECT MAX(CONVERT(SUBSTRING(partition_name, 4), SIGNED))
    INTO partition_value
    FROM information_schema.partitions
    WHERE table_name = 'predictions_partitioned'
    AND partition_name != 'p_future'
    AND partition_name LIKE 'p_%';

    -- Apskaičiuojame kitą mėnesį
    SET next_year = partition_value DIV 100;
    SET next_month = partition_value MOD 100;
    
    IF next_month = 12 THEN
        SET next_year = next_year + 1;
        SET next_month = 1;
    ELSE
        SET next_month = next_month + 1;
    END IF;
    
    -- Formuojame naujo particiono pavadinimą
    SET partition_name = CONCAT('p_', next_year, '_', LPAD(next_month, 2, '0'));
    
    -- Apskaičiuojame naują particiono reikšmę
    SET partition_value = next_year * 100 + next_month;
    
    -- Sukuriame naują particioną
    SET @sql = CONCAT(
        'ALTER TABLE predictions_partitioned REORGANIZE PARTITION p_future INTO (',
        'PARTITION ', partition_name, ' VALUES LESS THAN (', partition_value, '),',
        'PARTITION p_future VALUES LESS THAN MAXVALUE)'
    );
    
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
    
    SELECT CONCAT('Sukurtas naujas particionas: ', partition_name) AS message;
END //

DELIMITER ;

-- ========== PASTABOS DĖL PARTICIONAVIMO ==========

-- PASTABA: Particionavimas naudingas, kai:
-- 1. Duomenų bazė turi didelį kiekį duomenų (milijonus eilučių)
-- 2. Užklausos dažnai filtruoja pagal laukus, pagal kuriuos vykdomas particionavimas
-- 3. Seni duomenys gali būti archyvuojami arba ištrinti

-- Įvykdžius šį skriptą, particionavimo strategija būtų paruošta, tačiau
-- norint perkelti egzistuojančius duomenis į particionuotas lenteles, reikėtų
-- atlikti duomenų migravimą. Particionuotos lentelės pravartu naudoti tik 
-- su dideliais duomenų kiekiais (milijonais įrašų).

-- Duomenų perkėlimo pavyzdys:
-- INSERT INTO predictions_partitioned SELECT * FROM predictions;