import os
import sys

def setup_path():
    """
    Nustato teisingą Python importavimo kelią
    """
    # Gauname projekto šakninį katalogą
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Pridedame šakninį katalogą į Python kelią
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"Pridėtas kelias į Python path: {project_root}")
    
    # Patikriname, ar katalogai turi __init__.py failus
    for dir_path in ['database', 'database/models', 'database/repositories']:
        full_path = os.path.join(project_root, dir_path.replace('/', os.sep))
        init_file = os.path.join(full_path, '__init__.py')
        
        # Jei katalogas neegzistuoja, sukuriame jį
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            print(f"Sukurtas katalogas: {full_path}")
        
        # Jei __init__.py neegzistuoja, sukuriame jį
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write(f'# {dir_path.split("/")[-1]} paketo inicializavimo failas\n')
            print(f"Sukurtas failas: {init_file}")
    
    return project_root

# Jei šis failas paleidžiamas tiesiogiai, nustatome kelią
if __name__ == "__main__":
    setup_path()
    print("Importavimo kelias sėkmingai nustatytas!")