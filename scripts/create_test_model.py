# filepath: d:\CA_BTC\scripts\create_test_model.py
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Dropout
import os

# Sukuriame aplanką modeliams saugoti
os.makedirs('app/data/models', exist_ok=True)

# Sukuriame paprastą LSTM modelį
model = Sequential([
    LSTM(50, return_sequences=True, input_shape=(60, 1)),
    Dropout(0.2),
    LSTM(50, return_sequences=False),
    Dropout(0.2),
    Dense(25),
    Dense(1)
])

model.compile(optimizer='adam', loss='mean_squared_error')
model.save('app/data/models/lstm_btc_price_model.h5')
print("Pavyzdinis modelis išsaugotas")