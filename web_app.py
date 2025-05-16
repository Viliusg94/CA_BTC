"""
Kriptovaliutų prekybos sistemos web aplikacija
--------------------------------------------
Šis skriptas paleidžia Flask web serverį, kuris
teikia grafinę vartotojo sąsają kriptovaliutų prekybos sistemai.
"""

from app import create_app

# Sukuriame Flask aplikaciją
app = create_app()

if __name__ == '__main__':
    # Paleidžiame serverį vystymo rėžime
    app.run(debug=True)