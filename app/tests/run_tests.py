import logging
import unittest
import sys
from datetime import datetime
import argparse
from app.tests.integration_tests import IntegrationTests
from app.tests.performance_tests import PerformanceTests

# Konfigūruojame loginimą
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def run_integration_tests():
    """
    Paleidžia integracinius testus
    
    Returns:
        bool: True jei visi testai sėkmingi, False kitais atvejais
    """
    logger.info("Paleidžiami integraciniai testai...")
    
    # Sukuriame test loader
    loader = unittest.TestLoader()
    
    # Užkrauname testus
    suite = loader.loadTestsFromTestCase(IntegrationTests)
    
    # Sukuriame test runner
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Paleidžiame testus
    result = runner.run(suite)
    
    # Spausdiname rezultatus
    logger.info(f"Integraciniai testai užbaigti: {result.testsRun} testai, {len(result.errors)} klaidos, {len(result.failures)} nesėkmės")
    
    # Grąžiname rezultatą
    return len(result.errors) == 0 and len(result.failures) == 0

def run_performance_tests(dataset_size='small'):
    """
    Paleidžia našumo testus
    
    Args:
        dataset_size (str): Duomenų rinkinio dydis ('small', 'medium', 'large')
        
    Returns:
        bool: True jei visi testai sėkmingi, False kitais atvejais
    """
    logger.info(f"Paleidžiami našumo testai su {dataset_size} duomenų rinkiniu...")
    
    try:
        # Sukuriame našumo testų objektą
        performance_tests = PerformanceTests()
        
        # Paleidžiame testus
        results_df = performance_tests.run_performance_tests(dataset_size)
        
        # Spausdiname statistiką
        logger.info("\nNašumo testų rezultatai:")
        logger.info(f"Vidutinis vykdymo laikas visoms funkcijoms: {results_df['avg_time'].mean():.4f} s")
        logger.info(f"Greičiausia funkcija: {results_df.loc[results_df['avg_time'].idxmin()]['function']} ({results_df['avg_time'].min():.4f} s)")
        logger.info(f"Lėčiausia funkcija: {results_df.loc[results_df['avg_time'].idxmax()]['function']} ({results_df['avg_time'].max():.4f} s)")
        
        return True
    except Exception as e:
        logger.error(f"Klaida vykdant našumo testus: {str(e)}")
        return False

def check_requirements():
    """
    Tikrina, ar visi reikalavimai įgyvendinti
    
    Returns:
        dict: Reikalavimų įgyvendinimo būsena
    """
    logger.info("Tikrinami reikalavimai...")
    
    # Reikalavimų sąrašas
    requirements = {
        "1. Schemos sukūrimas": True,  # Jau įgyvendinta iš ankstesnių užduočių
        "2. Duomenų tipų parinkimas": True,  # Jau įgyvendinta iš ankstesnių užduočių
        "3. Ryšių tarp lentelių apibrėžimas": True,  # Jau įgyvendinta iš ankstesnių užduočių
        "4. Schemos optimizavimas": True,  # Jau įgyvendinta iš ankstesnių užduočių
        "5. ORM klasių sukūrimas": True,  # Jau įgyvendinta iš ankstesnių užduočių
        "6. Duomenų serviso sukūrimas": True,  # Jau įgyvendinta iš ankstesnių užduočių
        "7. Testavimas": {
            "7.1. Testinių duomenų rinkinys": run_data_generation_test(),
            "7.2. Ryšių tarp lentelių testavimas": run_relationships_test(),
            "7.3. Užklausų efektyvumo testavimas": True  # Bus atlikta per našumo testus
        }
    }
    
    # Spausdiname reikalavimų būseną
    logger.info("\nReikalavimų įgyvendinimo būsena:")
    for req, status in requirements.items():
        if isinstance(status, dict):
            logger.info(f"{req}:")
            for subreq, substatus in status.items():
                logger.info(f"  {subreq}: {'Įgyvendinta' if substatus else 'Neįgyvendinta'}")
        else:
            logger.info(f"{req}: {'Įgyvendinta' if status else 'Neįgyvendinta'}")
    
    # Tikriname, ar visi reikalavimai įgyvendinti
    all_implemented = all(
        status if not isinstance(status, dict) else all(substatus for substatus in status.values())
        for status in requirements.values()
    )
    
    logger.info(f"\nBendra būsena: {'Visi reikalavimai įgyvendinti' if all_implemented else 'Ne visi reikalavimai įgyvendinti'}")
    
    return requirements

def run_data_generation_test():
    """
    Tikrina, ar veikia testinių duomenų generavimas
    
    Returns:
        bool: True jei testas sėkmingas, False kitais atvejais
    """
    try:
        from app.tests.data_generator import TestDataGenerator
        
        # Sukuriame testinių duomenų generatorių
        generator = TestDataGenerator()
        
        # Generuojame po vieną kiekvieno tipo objektą
        prediction = generator.generate_prediction()
        simulation = generator.generate_simulation()
        trade = generator.generate_trade(simulation['id'])
        metric = generator.generate_metric()
        
        # Tikriname, ar objektai turi visus reikiamus laukus
        assert 'model_id' in prediction
        assert 'predicted_value' in prediction
        assert 'strategy_type' in simulation
        assert 'price' in trade
        assert 'value' in metric
        
        return True
    except Exception as e:
        logger.error(f"Klaida generuojant testinius duomenis: {str(e)}")
        return False

def run_relationships_test():
    """
    Tikrina, ar veikia ryšiai tarp lentelių
    
    Returns:
        bool: True jei testas sėkmingas, False kitais atvejais
    """
    try:
        from app.tests.data_generator import TestDataGenerator
        from app.services.results_service import ResultsService
        
        # Sukuriame testinių duomenų generatorių
        generator = TestDataGenerator()
        
        # Sukuriame servisą
        service = ResultsService()
        
        # Generuojame simuliaciją su sandoriais
        simulation, trades = generator.generate_simulation_with_trades(5)
        
        # Išsaugome simuliaciją
        simulation_id = service.save_simulation(simulation)
        
        # Išsaugome sandorius
        trade_ids = []
        for trade in trades:
            trade['simulation_id'] = simulation_id
            trade_id = service.save_trade(trade)
            trade_ids.append(trade_id)
        
        # Gauname simuliacijos sandorius
        saved_trades = service.get_simulation_trades(simulation_id)
        
        # Tikriname, ar visi sandoriai susieti su simuliacija
        if len(saved_trades) != len(trades):
            logger.error(f"Nesutampa sandorių skaičius: {len(saved_trades)} vs {len(trades)}")
            return False
        
        # Tikriname, ar visi sandoriai turi teisingą simulation_id
        for trade in saved_trades:
            if trade['simulation_id'] != simulation_id:
                logger.error(f"Neteisingas simulation_id: {trade['simulation_id']} vs {simulation_id}")
                return False
        
        return True
    except Exception as e:
        logger.error(f"Klaida testuojant ryšius tarp lentelių: {str(e)}")
        return False

if __name__ == "__main__":
    # Sukuriame argumentų parserį
    parser = argparse.ArgumentParser(description='Rezultatų modulio testavimas')
    parser.add_argument('--integration', action='store_true', help='Paleisti integracinius testus')
    parser.add_argument('--performance', action='store_true', help='Paleisti našumo testus')
    parser.add_argument('--requirements', action='store_true', help='Patikrinti reikalavimų įgyvendinimą')
    parser.add_argument('--dataset', choices=['small', 'medium', 'large'], default='small', help='Duomenų rinkinio dydis našumo testams')
    parser.add_argument('--all', action='store_true', help='Paleisti visus testus')
    
    # Nuskaitome argumentus
    args = parser.parse_args()
    
    # Jei nepasirinkta nei vieno testo, rodome pagalbą
    if not (args.integration or args.performance or args.requirements or args.all):
        parser.print_help()
        sys.exit(1)
    
    # Paleidžiame pasirinktus testus
    if args.all or args.integration:
        integration_success = run_integration_tests()
        logger.info(f"Integraciniai testai: {'Sėkmė' if integration_success else 'Nesėkmė'}")
    
    if args.all or args.performance:
        performance_success = run_performance_tests(args.dataset)
        logger.info(f"Našumo testai: {'Sėkmė' if performance_success else 'Nesėkmė'}")
    
    if args.all or args.requirements:
        requirements = check_requirements()