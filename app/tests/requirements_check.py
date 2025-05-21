import logging
import importlib
import inspect
import os
import subprocess
from sqlalchemy import inspect as sa_inspect
from database.db_utils import init_db, get_engine

logger = logging.getLogger(__name__)

class RequirementsChecker:
    """
    Klasė reikalavimų patikrinimui
    Tikrina, ar visi projekto reikalavimai įgyvendinti
    """
    
    def __init__(self):
        """
        Inicializuoja patikrinimo aplinką
        """
        # Inicializuojame duomenų bazę
        self.engine, _ = init_db()
        
        # Rezultatų saugojimui
        self.results = {}
    
    def check_database_schema(self):
        """
        Tikrina duomenų bazės schemos sukūrimą
        
        Returns:
            dict: Patikrinimo rezultatai
        """
        logger.info("Tikrinama duomenų bazės schema...")
        
        # Tikriname, ar egzistuoja reikiamos lentelės
        inspector = sa_inspect(self.engine)
        tables = inspector.get_table_names()
        
        required_tables = ['predictions', 'simulations', 'trades', 'metrics']
        
        # Tikriname, ar visos reikiamos lentelės egzistuoja
        tables_exist = all(table in tables for table in required_tables)
        
        # Jei visos lentelės egzistuoja, tikriname jų stulpelius
        columns_exist = True
        if tables_exist:
            # Minimalūs reikalavimai stulpeliams kiekvienoje lentelėje
            required_columns = {
                'predictions': ['id', 'model_id', 'prediction_date', 'target_date', 'predicted_value', 'actual_value', 'interval'],
                'simulations': ['id', 'name', 'initial_capital', 'strategy_type', 'start_date', 'end_date', 'roi'],
                'trades': ['id', 'simulation_id', 'date', 'type', 'price', 'amount', 'value'],
                'metrics': ['id', 'name', 'value', 'date']
            }
            
            # Tikriname kiekvienos lentelės stulpelius
            for table, required_cols in required_columns.items():
                table_columns = [col['name'] for col in inspector.get_columns(table)]
                if not all(col in table_columns for col in required_cols):
                    columns_exist = False
                    logger.warning(f"Lentelėje {table} trūksta stulpelių. Rasti: {table_columns}, reikia: {required_cols}")
        
        # Tikriname, ar yra bent keli indeksai
        indexes_exist = True
        if tables_exist:
            for table in required_tables:
                table_indexes = inspector.get_indexes(table)
                if len(table_indexes) < 2:  # Tikimės bent pirminio rakto ir dar vieno indekso
                    indexes_exist = False
                    logger.warning(f"Lentelėje {table} trūksta indeksų. Rasta: {len(table_indexes)}")
        
        # Formuojame rezultatus
        schema_results = {
            'tables_exist': tables_exist,
            'columns_exist': columns_exist,
            'indexes_exist': indexes_exist,
            'overall': tables_exist and columns_exist and indexes_exist
        }
        
        self.results['database_schema'] = schema_results
        
        logger.info(f"Duomenų bazės schemos patikrinimas: {'Sėkmė' if schema_results['overall'] else 'Nesėkmė'}")
        
        return schema_results
    
    def check_orm_classes(self):
        """
        Tikrina ORM klasių sukūrimą
        
        Returns:
            dict: Patikrinimo rezultatai
        """
        logger.info("Tikrinamos ORM klasės...")
        
        # Tikriname, ar egzistuoja ORM modelių modulis
        try:
            models_module = importlib.import_module('database.models.results_models')
            
            # Reikalingos klasės
            required_classes = ['Prediction', 'Simulation', 'Trade', 'Metric']
            
            # Tikriname, ar visos reikiamos klasės egzistuoja
            classes_exist = all(hasattr(models_module, cls) for cls in required_classes)
            
            # Tikriname, ar klasėse yra to_dict metodai
            methods_exist = True
            for cls_name in required_classes:
                if hasattr(models_module, cls_name):
                    cls = getattr(models_module, cls_name)
                    if not hasattr(cls, 'to_dict') or not callable(getattr(cls, 'to_dict')):
                        methods_exist = False
                        logger.warning(f"Klasėje {cls_name} trūksta to_dict metodo")
            
            # Tikriname, ar yra relationship apibrėžimai
            relationships_exist = True
            if hasattr(models_module, 'Simulation') and hasattr(models_module, 'Trade'):
                simulation_class = getattr(models_module, 'Simulation')
                trade_class = getattr(models_module, 'Trade')
                
                # Tikriname, ar Simulation klasėje yra trades ryšys
                has_trades_rel = hasattr(simulation_class, 'trades')
                
                # Tikriname, ar Trade klasėje yra simulation ryšys
                has_simulation_rel = hasattr(trade_class, 'simulation')
                
                relationships_exist = has_trades_rel and has_simulation_rel
                
                if not relationships_exist:
                    logger.warning(f"Trūksta ryšių tarp Simulation ir Trade klasių")
            
            # Formuojame rezultatus
            orm_results = {
                'module_exists': True,
                'classes_exist': classes_exist,
                'methods_exist': methods_exist,
                'relationships_exist': relationships_exist,
                'overall': classes_exist and methods_exist and relationships_exist
            }
            
        except ImportError:
            logger.warning("Nerasta results_models modulio")
            orm_results = {
                'module_exists': False,
                'classes_exist': False,
                'methods_exist': False,
                'relationships_exist': False,
                'overall': False
            }
        
        self.results['orm_classes'] = orm_results
        
        logger.info(f"ORM klasių patikrinimas: {'Sėkmė' if orm_results['overall'] else 'Nesėkmė'}")
        
        return orm_results
    
    def check_data_services(self):
        """
        Tikrina duomenų servisų sukūrimą
        
        Returns:
            dict: Patikrinimo rezultatai
        """
        logger.info("Tikrinami duomenų servisai...")
        
        # Tikriname, ar egzistuoja servisų moduliai
        services_exist = True
        required_services = [
            ('app.services.results_data_service', 'ResultsDataService'),
            ('app.services.results_service', 'ResultsService'),
            ('app.services.results_analysis_service', 'ResultsAnalysisService')
        ]
        
        for module_name, class_name in required_services:
            try:
                module = importlib.import_module(module_name)
                if not hasattr(module, class_name):
                    services_exist = False
                    logger.warning(f"Nerasta klasė {class_name} modulyje {module_name}")
            except ImportError:
                services_exist = False
                logger.warning(f"Nerasta modulio {module_name}")
        
        # Tikriname, ar ResultsService turi reikiamus metodus
        methods_exist = True
        try:
            module = importlib.import_module('app.services.results_service')
            service_class = getattr(module, 'ResultsService')
            
            # Reikalingi metodai
            required_methods = ['save_prediction', 'get_prediction', 'save_simulation', 'get_simulation', 'analyze_model']
            
            # Tikriname, ar visi reikiami metodai egzistuoja
            for method_name in required_methods:
                if not hasattr(service_class, method_name) or not callable(getattr(service_class, method_name)):
                    methods_exist = False
                    logger.warning(f"ResultsService klasėje trūksta metodo {method_name}")
        except Exception as e:
            methods_exist = False
            logger.warning(f"Klaida tikrinant ResultsService metodus: {str(e)}")
        
        # Formuojame rezultatus
        services_results = {
            'services_exist': services_exist,
            'methods_exist': methods_exist,
            'overall': services_exist and methods_exist
        }
        
        self.results['data_services'] = services_results
        
        logger.info(f"Duomenų servisų patikrinimas: {'Sėkmė' if services_results['overall'] else 'Nesėkmė'}")
        
        return services_results
    
    def check_api_routes(self):
        """
        Tikrina API maršrutų sukūrimą
        
        Returns:
            dict: Patikrinimo rezultatai
        """
        logger.info("Tikrinami API maršrutai...")
        
        # Tikriname, ar egzistuoja maršrutų modulis
        try:
            routes_module = importlib.import_module('app.results.results_routes')
            
            # Tikriname, ar egzistuoja results Blueprint
            blueprint_exists = hasattr(routes_module, 'results')
            
            # Tikriname, ar yra reikalingi API maršrutai
            required_routes = [
                'api_save_prediction',
                'api_save_simulation',
                'api_analyze_model',
                'api_analyze_simulation',
                'api_compare_models'
            ]
            
            # Skaičiuojame, kiek maršrutų egzistuoja
            routes_count = sum(1 for name in dir(routes_module) if name in required_routes)
            
            # Tikriname, ar yra pakankamai maršrutų
            routes_exist = routes_count >= 3  # Tikimės bent 3 iš 5 reikalingų maršrutų
            
            # Formuojame rezultatus
            routes_results = {
                'module_exists': True,
                'blueprint_exists': blueprint_exists,
                'routes_count': routes_count,
                'routes_exist': routes_exist,
                'overall': blueprint_exists and routes_exist
            }
            
        except ImportError:
            logger.warning("Nerasta results_routes modulio")
            routes_results = {
                'module_exists': False,
                'blueprint_exists': False,
                'routes_count': 0,
                'routes_exist': False,
                'overall': False
            }
        
        self.results['api_routes'] = routes_results
        
        logger.info(f"API maršrutų patikrinimas: {'Sėkmė' if routes_results['overall'] else 'Nesėkmė'}")
        
        return routes_results
    
    def check_all_requirements(self):
        """
        Tikrina visus reikalavimus
        
        Returns:
            dict: Visų patikrinimų rezultatai
        """
        # Vykdome visus patikrinimus
        schema_results = self.check_database_schema()
        orm_results = self.check_orm_classes()
        services_results = self.check_data_services()
        routes_results = self.check_api_routes()
        
        # Bendra būsena
        overall = (
            schema_results['overall'] and
            orm_results['overall'] and
            services_results['overall'] and
            routes_results['overall']
        )
        
        # Pridedame bendrą būseną
        self.results['overall'] = overall
        
        # Spausdiname bendrą būseną
        logger.info(f"\nVisų reikalavimų įgyvendinimo būsena: {'Sėkmė' if overall else 'Nesėkmė'}")
        
        # Spausdiname detalesnę informaciją
        logger.info("\nDetalūs rezultatai:")
        logger.info(f"1. Duomenų bazės schema: {'Sėkmė' if schema_results['overall'] else 'Nesėkmė'}")
        logger.info(f"2. ORM klasės: {'Sėkmė' if orm_results['overall'] else 'Nesėkmė'}")
        logger.info(f"3. Duomenų servisai: {'Sėkmė' if services_results['overall'] else 'Nesėkmė'}")
        logger.info(f"4. API maršrutai: {'Sėkmė' if routes_results['overall'] else 'Nesėkmė'}")
        
        return self.results

if __name__ == "__main__":
    # Konfigūruojame loginimą
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Sukuriame patikrinimo objektą
    checker = RequirementsChecker()
    
    # Vykdome patikrinimą
    results = checker.check_all_requirements()
    
    # Išeiname su atitinkamu kodu
    import sys
    sys.exit(0 if results['overall'] else 1)