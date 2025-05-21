import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

def get_positional_encoding(seq_len, d_model):
    pos = np.arange(seq_len)[:, np.newaxis]
    i = np.arange(d_model)[np.newaxis, :]
    angle_rates = 1 / np.power(10000, (2 * (i // 2)) / np.float32(d_model))
    angle_rads = pos * angle_rates
    pos_encoding = np.zeros((seq_len, d_model))
    pos_encoding[:, 0::2] = np.sin(angle_rads[:, 0::2])
    pos_encoding[:, 1::2] = np.cos(angle_rads[:, 1::2])
    return tf.constant(pos_encoding[np.newaxis, ...], dtype=tf.float32)

class TimeSeriesTransformer(tf.keras.Model):
    def __init__(self, seq_len, num_features, d_model=64, num_heads=4, ff_dim=128, dropout=0.1):
        super().__init__()
        self.seq_len = seq_len
        self.num_features = num_features
        self.d_model = d_model
        self.num_heads = num_heads
        self.ff_dim = ff_dim
        self.dropout_rate = dropout
        
        # Embedding sluoksnis
        self.embedding = layers.Dense(d_model)
        
        # Positional encoding
        self.pos_encoding = get_positional_encoding(seq_len, d_model)
        
        # Multi-head attention
        self.attention = layers.MultiHeadAttention(num_heads=num_heads, key_dim=d_model)
        self.dropout1 = layers.Dropout(dropout)
        self.norm1 = layers.LayerNormalization(epsilon=1e-6)
        
        # Feed-forward network
        self.ffn = tf.keras.Sequential([
            layers.Dense(ff_dim, activation='relu'),
            layers.Dense(d_model),
        ])
        self.dropout2 = layers.Dropout(dropout)
        self.norm2 = layers.LayerNormalization(epsilon=1e-6)
        
        # Output layers
        self.flatten = layers.Flatten()
        self.out = layers.Dense(1)

    def call(self, x, training=False):
        # Jei įvestis neatitinka tikėtos formos, pataisome ją
        input_shape = tf.shape(x)
        if input_shape[1] != self.seq_len:
            print(f"ĮSPĖJIMAS: Įvesties sekos ilgis ({input_shape[1]}) nesutampa su modelio sekos ilgiu ({self.seq_len})")
            # Galime čia pridėti papildomą logiką prireikus
        
        # Embedding
        x = self.embedding(x)
        
        # Add positional encoding - įsitikiname, kad dimensijos sutampa
        if x.shape[1] == self.seq_len:
            x = x + self.pos_encoding
        else:
            # Jei sekos ilgis nesutampa, generuojame naują pozicijos kodavimą dinamiškai
            new_pos_encoding = get_positional_encoding(x.shape[1], self.d_model)
            x = x + new_pos_encoding
        
        # Multi-head attention
        attn_output = self.attention(x, x)
        attn_output = self.dropout1(attn_output, training=training)
        out1 = self.norm1(x + attn_output)
        
        # Feed-forward network
        ffn_output = self.ffn(out1)
        ffn_output = self.dropout2(ffn_output, training=training)
        out2 = self.norm2(out1 + ffn_output)
        
        # Output
        out2 = self.flatten(out2)
        output = self.out(out2)
        
        return output
    
    def get_config(self):
        config = super().get_config()
        config.update({
            "seq_len": self.seq_len,
            "num_features": self.num_features,
            "d_model": self.d_model,
            "num_heads": self.num_heads,
            "ff_dim": self.ff_dim,
            "dropout": self.dropout_rate,
        })
        return config

# Modelio išsaugojimo pavyzdys (naudokite po modelio apmokymo):
# Saugokite modelį į projekto modelių katalogą:
# Pilnas kelias: d:/CA_BTC/models/transformer_model.h5

# model.save(r'd:/CA_BTC/models/transformer_model.h5')