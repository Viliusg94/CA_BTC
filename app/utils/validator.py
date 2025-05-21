class ModelValidator:
    """
    Klasė, skirta modelio parametrų validavimui
    """
    
    @staticmethod
    def validate_model_name(name):
        """
        Validuoja modelio pavadinimą
        
        Args:
            name (str): Modelio pavadinimas
        
        Returns:
            tuple: (bool, str) - (ar teisingas, klaidos pranešimas)
        """
        # Tikriname, ar pavadinimas nėra tuščias
        if not name or name.strip() == '':
            return False, "Modelio pavadinimas yra privalomas."
        
        # Tikriname ilgį
        if len(name) < 3:
            return False, "Modelio pavadinimas turi būti bent 3 simbolių ilgio."
        
        if len(name) > 100:
            return False, "Modelio pavadinimas negali būti ilgesnis nei 100 simbolių."
        
        # Jei visi patikrinimai praėjo
        return True, ""
    
    @staticmethod
    def validate_model_type(model_type):
        """
        Validuoja modelio tipą
        
        Args:
            model_type (str): Modelio tipas
        
        Returns:
            tuple: (bool, str) - (ar teisingas, klaidos pranešimas)
        """
        # Leidžiami modelių tipai
        valid_types = ['lstm', 'gru', 'cnn', 'transformer']
        
        # Tikriname, ar tipas nėra tuščias
        if not model_type or model_type.strip() == '':
            return False, "Modelio tipas yra privalomas."
        
        # Tikriname, ar tipas yra leistinas
        if model_type not in valid_types:
            return False, f"Neteisingas modelio tipas. Galimi variantai: {', '.join(valid_types)}"
        
        # Jei visi patikrinimai praėjo
        return True, ""
    
    @staticmethod
    def validate_epochs(epochs):
        """
        Validuoja epochų skaičių
        
        Args:
            epochs (int): Epochų skaičius
        
        Returns:
            tuple: (bool, str) - (ar teisingas, klaidos pranešimas)
        """
        try:
            # Konvertuojame į sveikąjį skaičių
            epochs = int(epochs)
            
            # Tikriname reikšmės diapazoną
            if epochs < 1:
                return False, "Epochų skaičius negali būti mažesnis už 1."
            
            if epochs > 1000:
                return False, "Epochų skaičius negali būti didesnis už 1000."
            
            # Jei visi patikrinimai praėjo
            return True, ""
        except (ValueError, TypeError):
            return False, "Epochų skaičius turi būti sveikasis skaičius."
    
    @staticmethod
    def validate_batch_size(batch_size):
        """
        Validuoja batch dydį
        
        Args:
            batch_size (int): Batch dydis
        
        Returns:
            tuple: (bool, str) - (ar teisingas, klaidos pranešimas)
        """
        try:
            # Konvertuojame į sveikąjį skaičių
            batch_size = int(batch_size)
            
            # Tikriname reikšmės diapazoną
            if batch_size < 8:
                return False, "Batch dydis negali būti mažesnis už 8."
            
            if batch_size > 256:
                return False, "Batch dydis negali būti didesnis už 256."
            
            # Jei visi patikrinimai praėjo
            return True, ""
        except (ValueError, TypeError):
            return False, "Batch dydis turi būti sveikasis skaičius."
    
    @staticmethod
    def validate_learning_rate(learning_rate):
        """
        Validuoja mokymosi greitį
        
        Args:
            learning_rate (float): Mokymosi greitis
        
        Returns:
            tuple: (bool, str) - (ar teisingas, klaidos pranešimas)
        """
        try:
            # Konvertuojame į slankiojo taško skaičių
            learning_rate = float(learning_rate)
            
            # Tikriname reikšmės diapazoną
            if learning_rate < 0.0001:
                return False, "Mokymosi greitis negali būti mažesnis už 0.0001."
            
            if learning_rate > 0.01:
                return False, "Mokymosi greitis negali būti didesnis už 0.01."
            
            # Jei visi patikrinimai praėjo
            return True, ""
        except (ValueError, TypeError):
            return False, "Mokymosi greitis turi būti slankiojo taško skaičius."