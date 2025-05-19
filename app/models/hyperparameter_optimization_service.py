import os
import json
import itertools
import random
import numpy as np
import traceback
from datetime import datetime
from sklearn.model_selection import KFold
from app.models.optimization_session import OptimizationSession

class HyperparameterOptimizationService:
    """
    Servisas hiperparametrų optimizavimui
    """
    
    def __init__(self):
        """
        Inicializuoja hiperparametrų optimizavimo servisą
        """
        # Sesijų saugojimo katalogas
        self.sessions_dir = os.path.join("app", "data", "optimization_sessions")
        
        # Sukuriame katalogą, jei neegzistuoja
        if not os.path.exists(self.sessions_dir):
            os.makedirs(self.sessions_dir)
            
    def save_session(self, session):
        """
        Išsaugo optimizavimo sesiją į failą
        
        Args:
            session (OptimizationSession): Optimizavimo sesija
        """
        # Konvertuojame sesiją į žodyną
        session_dict = session.to_dict()
        
        # Sukuriame failo pavadinimą
        filename = f"{session.session_id}.json"
        file_path = os.path.join(self.sessions_dir, filename)
        
        # Išsaugome sesiją į failą
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(session_dict, f, ensure_ascii=False, indent=4)
            
    def load_session(self, session_id):
        """
        Užkrauna optimizavimo sesiją iš failo
        
        Args:
            session_id (str): Sesijos ID
            
        Returns:
            OptimizationSession: Užkrauta sesija arba None, jei sesija nerasta
        """
        # Sukuriame failo pavadinimą
        filename = f"{session_id}.json"
        file_path = os.path.join(self.sessions_dir, filename)
        
        # Patikriname, ar failas egzistuoja
        if not os.path.exists(file_path):
            return None
        
        # Užkrauname sesiją iš failo
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return OptimizationSession.from_dict(data)
        except Exception as e:
            print(f"Klaida užkraunant sesiją: {str(e)}")
            return None
            
    def get_all_sessions(self):
        """
        Gauna visas optimizavimo sesijas
        
        Returns:
            list: Visos optimizavimo sesijos
        """
        sessions = []
        
        # Tikriname, ar katalogas egzistuoja
        if not os.path.exists(self.sessions_dir):
            return sessions
        
        # Einame per visus failus kataloge
        for filename in os.listdir(self.sessions_dir):
            if filename.endswith(".json"):
                session_id = filename.replace(".json", "")
                session = self.load_session(session_id)
                
                if session:
                    sessions.append(session)
        
        # Rikiuojame sesijas pagal sukūrimo datą (naujausios pirma)
        sessions.sort(key=lambda s: s.created_at, reverse=True)
        
        return sessions
        
    def delete_session(self, session_id):
        """
        Ištrina optimizavimo sesiją
        
        Args:
            session_id (str): Sesijos ID
            
        Returns:
            bool: Ar pavyko ištrinti sesiją
        """
        # Sukuriame failo pavadinimą
        filename = f"{session_id}.json"
        file_path = os.path.join(self.sessions_dir, filename)
        
        # Patikriname, ar failas egzistuoja
        if not os.path.exists(file_path):
            return False
        
        # Ištriname failą
        try:
            os.remove(file_path)
            return True
        except Exception as e:
            print(f"Klaida trinant sesiją: {str(e)}")
            return False
            
    def grid_search(self, model_builder, param_grid, model_type, X_train, y_train, cv=3, name=None):
        """
        Atlieka Grid Search optimizavimą
        
        Args:
            model_builder (function): Funkcija, kuri sukuria ir grąžina modelį pagal parametrus
            param_grid (dict): Parametrų tinklelis, kuriame raktai yra parametrų pavadinimai,
                              o reikšmės yra sąrašai galimų parametrų reikšmių
            model_type (str): Modelio tipas
            X_train (array): Mokymo duomenys
            y_train (array): Mokymo tikslai
            cv (int): Kryžminio patikrinimo skaičius
            name (str): Optimizavimo sesijos pavadinimas
            
        Returns:
            OptimizationSession: Optimizavimo sesija su rezultatais
        """
        # Sukuriame naują optimizavimo sesiją
        session = OptimizationSession(
            name=name,
            algorithm="grid_search",
            model_type=model_type,
            parameters={"param_grid": param_grid, "cv": cv}
        )
        
        # Išsaugome pradinę sesiją
        self.save_session(session)
        
        # Pakeičiame sesijos būseną į "running"
        session.status = "running"
        self.save_session(session)
        
        try:
            # Sugeneruojame visas galimas parametrų kombinacijas
            keys = param_grid.keys()
            param_values = [param_grid[key] for key in keys]
            param_combinations = list(itertools.product(*param_values))
            
            # Kryžminio patikrinimo objektas
            kf = KFold(n_splits=cv, shuffle=True, random_state=42)
            
            # Einame per kiekvieną parametrų kombinaciją
            for params_tuple in param_combinations:
                params = dict(zip(keys, params_tuple))
                print(f"Testuojami parametrai: {params}")
                
                # Inicializuojame metrikos saugojimą
                cv_scores = []
                
                # Atliekame kryžminį patikrinimą
                for train_idx, val_idx in kf.split(X_train):
                    X_train_cv, X_val_cv = X_train[train_idx], X_train[val_idx]
                    y_train_cv, y_val_cv = y_train[train_idx], y_train[val_idx]
                    
                    # Sukuriame ir mokomame modelį
                    model = model_builder(**params)
                    model.fit(X_train_cv, y_train_cv)
                    
                    # Gauname tikslumą validacijos duomenyse
                    score = model.score(X_val_cv, y_val_cv)
                    cv_scores.append(score)
                
                # Apskaičiuojame vidutinį tikslumą
                mean_score = np.mean(cv_scores)
                
                # Pridedame bandymą į sesiją
                session.add_trial(
                    params=params,
                    score=mean_score,
                    metrics={"cv_scores": cv_scores}
                )
                
                # Išsaugome atnaujintą sesiją
                self.save_session(session)
            
            # Užbaigiame sesiją
            session.complete()
            print(f"Grid Search užbaigtas. Geriausi parametrai: {session.best_params}, rezultatas: {session.best_score}")
        
        except Exception as e:
            # Pažymime sesiją kaip nepavykusią
            error_message = f"Klaida vykdant Grid Search: {str(e)}"
            print(error_message)
            traceback.print_exc()
            session.fail(error_message)
        
        # Išsaugome galutinius rezultatus
        self.save_session(session)
        
        return session
        
    def random_search(self, model_builder, param_distributions, model_type, X_train, y_train, n_iter=10, cv=3, name=None):
        """
        Atlieka Random Search optimizavimą
        
        Args:
            model_builder (function): Funkcija, kuri sukuria ir grąžina modelį pagal parametrus
            param_distributions (dict): Parametrų paskirstymai, kuriuose raktai yra parametrų pavadinimai,
                                      o reikšmės yra žodynai su 'min', 'max' reikšmėmis arba 'values' sąrašas
            model_type (str): Modelio tipas
            X_train (array): Mokymo duomenys
            y_train (array): Mokymo tikslai
            n_iter (int): Bandymų skaičius
            cv (int): Kryžminio patikrinimo skaičius
            name (str): Optimizavimo sesijos pavadinimas
            
        Returns:
            OptimizationSession: Optimizavimo sesija su rezultatais
        """
        # Sukuriame naują optimizavimo sesiją
        session = OptimizationSession(
            name=name,
            algorithm="random_search",
            model_type=model_type,
            parameters={"param_distributions": param_distributions, "n_iter": n_iter, "cv": cv}
        )
        
        # Išsaugome pradinę sesiją
        self.save_session(session)
        
        # Pakeičiame sesijos būseną į "running"
        session.status = "running"
        self.save_session(session)
        
        try:
            # Funkcija atsitiktinėms parametrų reikšmėms generuoti
            def sample_param(param_config):
                if "values" in param_config:
                    # Diskretinės reikšmės
                    return random.choice(param_config["values"])
                elif "min" in param_config and "max" in param_config:
                    # Intervalas
                    param_min = param_config["min"]
                    param_max = param_config["max"]
                    
                    if isinstance(param_min, int) and isinstance(param_max, int):
                        # Sveikieji skaičiai
                        return random.randint(param_min, param_max)
                    else:
                        # Realieji skaičiai
                        return random.uniform(param_min, param_max)
                else:
                    raise ValueError(f"Neteisingas parametrų formatas: {param_config}")
            
            # Kryžminio patikrinimo objektas
            kf = KFold(n_splits=cv, shuffle=True, random_state=42)
            
            # Atliekame nurodytą skaičių bandymų
            for i in range(n_iter):
                # Generuojame atsitiktinius parametrus
                params = {}
                for param_name, param_config in param_distributions.items():
                    params[param_name] = sample_param(param_config)
                
                print(f"Bandymas {i+1}/{n_iter}: {params}")
                
                # Inicializuojame metrikos saugojimą
                cv_scores = []
                
                # Atliekame kryžminį patikrinimą
                for train_idx, val_idx in kf.split(X_train):
                    X_train_cv, X_val_cv = X_train[train_idx], X_train[val_idx]
                    y_train_cv, y_val_cv = y_train[train_idx], y_train[val_idx]
                    
                    # Sukuriame ir mokomame modelį
                    model = model_builder(**params)
                    model.fit(X_train_cv, y_train_cv)
                    
                    # Gauname tikslumą validacijos duomenyse
                    score = model.score(X_val_cv, y_val_cv)
                    cv_scores.append(score)
                
                # Apskaičiuojame vidutinį tikslumą
                mean_score = np.mean(cv_scores)
                
                # Pridedame bandymą į sesiją
                session.add_trial(
                    params=params,
                    score=mean_score,
                    metrics={"cv_scores": cv_scores}
                )
                
                # Išsaugome atnaujintą sesiją
                self.save_session(session)
            
            # Užbaigiame sesiją
            session.complete()
            print(f"Random Search užbaigtas. Geriausi parametrai: {session.best_params}, rezultatas: {session.best_score}")
        
        except Exception as e:
            # Pažymime sesiją kaip nepavykusią
            error_message = f"Klaida vykdant Random Search: {str(e)}"
            print(error_message)
            traceback.print_exc()
            session.fail(error_message)
        
        # Išsaugome galutinius rezultatus
        self.save_session(session)
        
        return session
    
    def bayesian_optimization(self, model_builder, param_bounds, model_type, X_train, y_train, n_iter=10, cv=3, name=None):
        """
        Atlieka Bayesian optimizavimą
        
        Args:
            model_builder (function): Funkcija, kuri sukuria ir grąžina modelį pagal parametrus
            param_bounds (dict): Parametrų ribos, kur raktai yra parametrų pavadinimai,
                              o reikšmės yra sąrašai [min, max]
            model_type (str): Modelio tipas
            X_train (array): Mokymo duomenys
            y_train (array): Mokymo tikslai
            n_iter (int): Bandymų skaičius
            cv (int): Kryžminio patikrinimo skaičius
            name (str): Optimizavimo sesijos pavadinimas
            
        Returns:
            OptimizationSession: Optimizavimo sesija su rezultatais
        """
        # Sukuriame naują optimizavimo sesiją
        session = OptimizationSession(
            name=name,
            algorithm="bayesian_optimization",
            model_type=model_type,
            parameters={"param_bounds": param_bounds, "n_iter": n_iter, "cv": cv}
        )
        
        # Išsaugome pradinę sesiją
        self.save_session(session)
        
        # Pakeičiame sesijos būseną į "running"
        session.status = "running"
        self.save_session(session)
        
        try:
            # Tikriname, ar turime scikit-optimize biblioteką
            try:
                from skopt import Optimizer
                from skopt.space import Real, Integer
            except ImportError:
                error_message = "Bayesian optimizavimui reikalinga scikit-optimize biblioteka. Įdiekite su 'pip install scikit-optimize'"
                session.fail(error_message)
                self.save_session(session)
                return session
            
            # Sukuriame parametrų erdvę
            space = []
            param_names = []
            
            for param_name, bounds in param_bounds.items():
                param_names.append(param_name)
                
                if isinstance(bounds[0], int) and isinstance(bounds[1], int):
                    # Sveikieji skaičiai
                    space.append(Integer(bounds[0], bounds[1], name=param_name))
                else:
                    # Realieji skaičiai
                    space.append(Real(bounds[0], bounds[1], name=param_name))
            
            # Tikslo funkcija, kurią optimizuosime
            def objective(params):
                # Sukuriame parametrų žodyną
                param_dict = {name: value for name, value in zip(param_names, params)}
                print(f"Testuojami parametrai: {param_dict}")
                
                # Kryžminio patikrinimo objektas
                kf = KFold(n_splits=cv, shuffle=True, random_state=42)
                cv_scores = []
                
                # Atliekame kryžminį patikrinimą
                for train_idx, val_idx in kf.split(X_train):
                    X_train_cv, X_val_cv = X_train[train_idx], X_train[val_idx]
                    y_train_cv, y_val_cv = y_train[train_idx], y_train[val_idx]
                    
                    # Sukuriame ir mokomame modelį
                    model = model_builder(**param_dict)
                    model.fit(X_train_cv, y_train_cv)
                    
                    # Gauname tikslumą validacijos duomenyse
                    score = model.score(X_val_cv, y_val_cv)
                    cv_scores.append(score)
                
                # Apskaičiuojame vidutinį tikslumą
                mean_score = np.mean(cv_scores)
                
                # Pridedame bandymą į sesiją
                session.add_trial(
                    params=param_dict,
                    score=mean_score,
                    metrics={"cv_scores": cv_scores}
                )
                
                # Išsaugome atnaujintą sesiją
                self.save_session(session)
                
                # Grąžiname neigiamą reikšmę, nes optimizuotojas minimizuoja
                return -mean_score
            
            # Sukuriame optimizuotoją
            optimizer = Optimizer(space, "GP", acq_func="EI")
            
            # Atliekame nurodytą skaičių bandymų
            for i in range(n_iter):
                print(f"Bayesian optimizavimo iteracija {i+1}/{n_iter}")
                
                # Gauname naujus parametrus išbandymui
                next_params = optimizer.ask()
                
                # Apskaičiuojame tikslo funkciją
                score = objective(next_params)
                
                # Informuojame optimizuotoją apie rezultatą
                optimizer.tell(next_params, score)
            
            # Užbaigiame sesiją
            session.complete()
            print(f"Bayesian optimizavimas užbaigtas. Geriausi parametrai: {session.best_params}, rezultatas: {session.best_score}")
        
        except Exception as e:
            # Pažymime sesiją kaip nepavykusią
            error_message = f"Klaida vykdant Bayesian optimizavimą: {str(e)}"
            print(error_message)
            traceback.print_exc()
            session.fail(error_message)
        
        # Išsaugome galutinius rezultatus
        self.save_session(session)
        
        return session
    
    def apply_best_params(self, session_id, model_builder):
        """
        Pritaiko geriausius parametrus modeliui
        
        Args:
            session_id (str): Optimizavimo sesijos ID
            model_builder (function): Funkcija, kuri sukuria ir grąžina modelį pagal parametrus
            
        Returns:
            object: Modelis su geriausiais parametrais arba None, jei nepavyko
        """
        # Užkrauname sesiją
        session = self.load_session(session_id)
        
        if not session:
            print(f"Nepavyko rasti sesijos su ID: {session_id}")
            return None
        
        # Patikriname, ar sesija užbaigta ir turi geriausius parametrus
        if session.status != "completed" or not session.best_params:
            print(f"Sesija neužbaigta arba neturi geriausių parametrų. Statusas: {session.status}")
            return None
        
        try:
            # Sukuriame modelį su geriausiais parametrais
            model = model_builder(**session.best_params)
            return model
        except Exception as e:
            print(f"Klaida kuriant modelį su geriausiais parametrais: {str(e)}")
            return None