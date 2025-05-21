"""
Kriptovaliutų prekybos sistemos web aplikacija
--------------------------------------------
Šis skriptas paleidžia Flask web serverį, kuris
teikia grafinę vartotojo sąsają kriptovaliutų prekybos sistemai.
"""

from app import create_app, socketio

# Sukuriame Flask aplikaciją
app = create_app()

if __name__ == '__main__':
    # Paleidžiame su socketio.run vietoje app.run
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)