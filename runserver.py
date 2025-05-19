from app import create_app

# Sukuriame Flask aplikaciją
app = create_app()

if __name__ == '__main__':
    # Naudojame paprastą Flask serverį vietoj WebSocket
    app.run(debug=True, host='0.0.0.0', port=5000)