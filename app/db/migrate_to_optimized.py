import logging
from sqlalchemy import create_engine, text
from database.db_utils import init_db, get_engine
import os

# Kelias iki SQL skriptų
OPTIMIZE_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'optimize_schema.sql')
PARTITION_STRATEGY_PATH = os.path.join(os.path.dirname(__file__), 'partition_strategy.sql')

def migrate_to_optimized_schema():
    """
    Atlieka duomenų bazės schemos optimizavimą
    """
    try:
        # Gauname duomenų bazės prisijungimą
        engine, _ = init_db()
        
        logging.info("Pradedamas duomenų bazės schemos optimizavimas...")
        
        # 1. Vykdome schema optimizavimo skriptą
        with open(OPTIMIZE_SCHEMA_PATH, 'r', encoding='utf-8') as f:
            optimize_sql = f.read()
        
        # Vykdome SQL užklausas
        with engine.connect() as conn:
            logging.info("Vykdomas schemos optimizavimo skriptas...")
            conn.execute(text(optimize_sql))
            conn.commit()
            logging.info("Schemos optimizavimas baigtas sėkmingai.")
        
        # 2. Klausiame vartotojo, ar įjungti particionavimo strategiją
        enable_partitioning = input("Ar įjungti lentelių particionavimą dideliems duomenų kiekiams? (T/N): ")
        
        if enable_partitioning.upper() == 'T':
            with open(PARTITION_STRATEGY_PATH, 'r', encoding='utf-8') as f:
                partition_sql = f.read()
            
            # Vykdome SQL užklausas
            with engine.connect() as conn:
                logging.info("Vykdomas particionavimo strategijos skriptas...")
                conn.execute(text(partition_sql))
                conn.commit()
                logging.info("Particionavimo strategija sėkmingai įdiegta.")
        
        logging.info("Duomenų bazės schemos optimizavimas užbaigtas sėkmingai.")
        return True
        
    except Exception as e:
        logging.error(f"Klaida optimizuojant duomenų bazės schemą: {e}")
        return False

def check_table_sizes():
    """
    Patikrina lentelių dydžius ir grąžina rekomendacijas dėl particionavimo
    """
    try:
        # Gauname duomenų bazės prisijungimą
        engine, _ = init_db()
        
        # SQL užklausa lentelių dydžiams gauti
        size_query = text("""
        SELECT 
            table_name, 
            table_rows,
            data_length/1024/1024 as data_size_mb,
            index_length/1024/1024 as index_size_mb,
            (data_length + index_length)/1024/1024 as total_size_mb
        FROM 
            information_schema.tables
        WHERE 
            table_schema = DATABASE()
            AND table_name IN ('predictions', 'simulations', 'trades', 'metrics')
        ORDER BY 
            total_size_mb DESC;
        """)
        
        with engine.connect() as conn:
            result = conn.execute(size_query)
            rows = result.fetchall()
            
            print("\n=== LENTELIŲ DYDŽIŲ ANALIZĖ ===")
            print(f"{'Lentelė':<15} {'Eilučių':<10} {'Duomenys (MB)':<15} {'Indeksai (MB)':<15} {'Iš viso (MB)':<15} {'Rekomendacija':<20}")
            print("-" * 90)
            
            for row in rows:
                table_name = row[0]
                row_count = row[1] or 0
                data_size = float(row[2] or 0)
                index_size = float(row[3] or 0)
                total_size = float(row[4] or 0)
                
                # Rekomendacijos dėl particionavimo
                if row_count > 1000000 or total_size > 1000:
                    recommendation = "PARTICIONUOTI"
                elif row_count > 500000 or total_size > 500:
                    recommendation = "APSVARSTYKITE"
                else:
                    recommendation = "NEREIKIA"
                    
                print(f"{table_name:<15} {row_count:<10} {data_size:<15.2f} {index_size:<15.2f} {total_size:<15.2f} {recommendation:<20}")
            
            print("\nREKOMENDACIJOS:")
            print("- PARTICIONUOTI: Būtina particionuoti lentelę, kad užtikrinti efektyvų darbą")
            print("- APSVARSTYKITE: Particionavimas gali būti naudingas priklausomai nuo užklausų pobūdžio")
            print("- NEREIKIA: Particionavimas šiuo metu nereikalingas")
        
    except Exception as e:
        logging.error(f"Klaida tikrinant lentelių dydžius: {e}")

if __name__ == "__main__":
    # Nustatome loginimą
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Pirmiausia patikriname lentelių dydžius
    check_table_sizes()
    
    # Klausiame vartotojo, ar tęsti
    proceed = input("\nAr tęsti schemos optimizavimą? (T/N): ")
    
    if proceed.upper() == 'T':
        success = migrate_to_optimized_schema()
        if success:
            print("\nDuomenų bazės schema sėkmingai optimizuota!")
        else:
            print("\nKlaida optimizuojant duomenų bazės schemą. Žr. žurnalo įrašus.")
    else:
        print("\nOperacija atšaukta.")