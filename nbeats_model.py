"""
N-BEATS model — disalin persis dari notebook skripsi Kia
(NBEATS_Bitcoin_Adam.ipynb, model terbaik: RMSE 1789.95, R2 0.9969).

N-BEATS: Neural Basis Expansion Analysis for Time Series.
Tiap block memecah input jadi 'backcast' (yang dijelaskan block ini,
dikurangkan dari sisa/residual) dan 'forecast' (kontribusi prediksi,
dijumlahkan). Ditumpuk beberapa block secara residual.
"""
import tensorflow as tf
from tensorflow.keras.layers import Dense, Layer
from tensorflow.keras.models import Model


class NBeatsBlock(Layer):
    def __init__(self, units, theta_dim, **kwargs):
        super(NBeatsBlock, self).__init__(**kwargs)
        self.units = units
        self.theta_dim = theta_dim
        self.fc1 = Dense(units, activation='relu')
        self.fc2 = Dense(units, activation='relu')
        self.fc3 = Dense(units, activation='relu')
        self.fc4 = Dense(units, activation='relu')
        self.backcast_layer = Dense(theta_dim, activation=None)
        self.forecast_layer = Dense(theta_dim, activation=None)

    def call(self, inputs):
        x = self.fc1(inputs)
        x = self.fc2(x)
        x = self.fc3(x)
        x = self.fc4(x)
        backcast = self.backcast_layer(x)
        forecast = self.forecast_layer(x)
        return backcast, forecast

    def get_config(self):
        config = super().get_config()
        config.update({"units": self.units, "theta_dim": self.theta_dim})
        return config


class NBeats(Model):
    def __init__(self, lookback, horizon=1, n_blocks=3, units=128, **kwargs):
        super(NBeats, self).__init__(**kwargs)
        self.lookback = lookback
        self.horizon = horizon
        self.n_blocks = n_blocks
        self.units = units
        self.blocks = [NBeatsBlock(units, lookback) for _ in range(n_blocks)]
        self.forecast_agg = Dense(horizon, use_bias=False)
        self.backcast_agg = Dense(lookback, use_bias=False)

    def call(self, inputs):
        residuals = inputs
        forecast = tf.zeros_like(inputs[:, :self.horizon])
        for block in self.blocks:
            backcast, block_forecast = block(residuals)
            residuals = residuals - backcast
            forecast = forecast + block_forecast[:, :self.horizon]
        return forecast

    def get_config(self):
        config = super().get_config()
        config.update({
            "lookback": self.lookback,
            "horizon": self.horizon,
            "n_blocks": self.n_blocks,
            "units": self.units,
        })
        return config


# Dipakai saat load_model() agar Keras mengenali custom class.
CUSTOM_OBJECTS = {"NBeats": NBeats, "NBeatsBlock": NBeatsBlock}


def build_nbeats(lookback=10, horizon=1, n_blocks=4, units=128,
                 learning_rate=0.001):
    """Bangun + compile N-BEATS dengan hyperparameter juara skripsi."""
    model = NBeats(lookback=lookback, horizon=horizon,
                   n_blocks=n_blocks, units=units)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
        loss="mse",
    )
    # Model subclassed tidak bisa di-build via model.build();
    # paksa pembangunan graph lewat satu forward pass dummy agar
    # load_weights() menemukan variabel yang benar.
    model(tf.zeros((1, lookback)))
    return model
