"""
Vizualizacijų modulis.
Suteikia funkcijas duomenų ir prognozių vizualizavimui.
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging

# Konfigūruojame logerį
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_comparison_chart(metrics_df):
    """
    Sukuria modelių palyginimo grafiką pagal metrikas.
    
    Args:
        metrics_df (pandas.DataFrame): Modelių metrikų DataFrame
    
    Returns:
        plotly.graph_objects.Figure: Plotly grafikas
    """
    if metrics_df is None or metrics_df.empty:
        logger.warning("Nėra duomenų modelių palyginimo grafikui")
        fig = go.Figure()
        fig.add_annotation(
            text="Nėra duomenų",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="red")
        )
        return fig
    
    # Sukuriame subplot layoutą
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("RMSE palyginimas", "MAE palyginimas", 
                         "MAPE palyginimas", "R² palyginimas"),
        vertical_spacing=0.15
    )
    
    # Spalvų paletė modeliams
    color_sequence = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
    
    # RMSE palyginimas
    fig.add_trace(
        go.Bar(
            x=metrics_df['Modelis'],
            y=metrics_df['RMSE'],
            name='RMSE',
            marker_color=color_sequence,
            text=metrics_df['RMSE'].round(2),
            textposition='auto',
        ),
        row=1, col=1
    )
    
    # MAE palyginimas
    fig.add_trace(
        go.Bar(
            x=metrics_df['Modelis'],
            y=metrics_df['MAE'],
            name='MAE',
            marker_color=color_sequence,
            text=metrics_df['MAE'].round(2),
            textposition='auto',
        ),
        row=1, col=2
    )
    
    # MAPE palyginimas
    fig.add_trace(
        go.Bar(
            x=metrics_df['Modelis'],
            y=metrics_df['MAPE (%)'],
            name='MAPE',
            marker_color=color_sequence,
            text=metrics_df['MAPE (%)'].round(2),
            textposition='auto',
        ),
        row=2, col=1
    )
    
    # R² palyginimas
    fig.add_trace(
        go.Bar(
            x=metrics_df['Modelis'],
            y=metrics_df['R²'],
            name='R²',
            marker_color=color_sequence,
            text=metrics_df['R²'].round(4),
            textposition='auto',
        ),
        row=2, col=2
    )
    
    # Atnaujina layoutą
    fig.update_layout(
        title="Visų modelių metrikų palyginimas",
        showlegend=False,
        height=700,
        template="plotly_white"
    )
    
    # Y ašių pavadinimų atnaujinimas
    fig.update_yaxes(title_text="RMSE (mažesnis geriau)", row=1, col=1)
    fig.update_yaxes(title_text="MAE (mažesnis geriau)", row=1, col=2)
    fig.update_yaxes(title_text="MAPE % (mažesnis geriau)", row=2, col=1)
    fig.update_yaxes(title_text="R² (didesnis geriau)", row=2, col=2)
    
    return fig

def create_prediction_chart(prediction_result):
    """
    Sukuria prognozės vizualizaciją.
    
    Args:
        prediction_result (dict): Prognozės rezultatai
        
    Returns:
        plotly.graph_objects.Figure: Plotly grafikas
    """
    fig = go.Figure()
    
    # Jei yra klaida, grąžiname tuščią grafiką su klaidos pranešimu
    if 'error' in prediction_result:
        fig.add_annotation(
            text=f"Klaida: {prediction_result['error']}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="red")
        )
        return fig
    
    # Pridedame paskutinę kainą ir prognozę
    last_price = prediction_result['last_price']
    prediction = prediction_result['prediction']
    dates = [datetime.now() - timedelta(minutes=15), datetime.now(), datetime.now() + timedelta(minutes=15)]
    prices = [last_price, last_price, prediction]
    
    # Vizualizuojame kainą ir prognozę
    fig.add_trace(
        go.Scatter(
            x=dates[:2],
            y=prices[:2],
            name="Faktinė kaina",
            line=dict(color="black", width=2)
        )
    )
    
    fig.add_trace(
        go.Scatter(
            x=dates[1:],
            y=prices[1:],
            name="Prognozė",
            line=dict(color="crimson" if prediction_result['direction'] == 'down' else "green", 
                     width=2, dash="dash")
        )
    )
    
    # Pridedame krypties rodyklę
    arrow_color = "green" if prediction_result['direction'] == 'up' else "crimson"
    arrow_symbol = "triangle-up" if prediction_result['direction'] == 'up' else "triangle-down"
    
    fig.add_trace(
        go.Scatter(
            x=[dates[2]],
            y=[prediction],
            mode="markers",
            marker=dict(
                color=arrow_color,
                size=15,
                symbol=arrow_symbol
            ),
            name="Kryptis"
        )
    )
    
    # Pridedame anotacijas su kainų pokyčiu
    fig.add_annotation(
        x=dates[2],
        y=prediction,
        text=f"{prediction_result['change_percent']:.2f}%",
        showarrow=True,
        arrowhead=2,
        arrowcolor=arrow_color,
        arrowsize=1,
        arrowwidth=2,
        ax=0,
        ay=-40 if prediction_result['direction'] == 'up' else 40
    )
    
    fig.update_layout(
        title="Bitcoin kainos prognozė",
        xaxis_title="Laikas",
        yaxis_title="Kaina (USD)",
        template="plotly_white"
    )
    
    return fig

def create_ensemble_chart(ensemble_data):
    """
    Sukuria ansamblio modelio vizualizaciją.
    
    Args:
        ensemble_data (dict): Ansamblio modelio duomenys
        
    Returns:
        plotly.graph_objects.Figure: Plotly grafikas
    """
    if not ensemble_data or 'dates' not in ensemble_data or 'actual' not in ensemble_data:
        logger.warning("Nėra duomenų ansamblio grafikui")
        fig = go.Figure()
        fig.add_annotation(
            text="Nėra duomenų",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="red")
        )
        return fig
    
    fig = go.Figure()
    
    # Konvertuojame datas
    try:
        dates = [datetime.strptime(d, "%Y-%m-%d") for d in ensemble_data['dates']]
    except ValueError:
        logger.warning("Negalima konvertuoti datų. Naudojami indeksai")
        dates = list(range(len(ensemble_data['actual'])))
    
    # Pridedame faktines reikšmes
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=ensemble_data['actual'],
            name="Faktinė kaina",
            line=dict(color="black", width=3)
        )
    )
    
    # Pridedame ansamblio prognozes
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=ensemble_data['ensemble'],
            name="Ansamblio prognozė",
            line=dict(color="crimson", width=3)
        )
    )
    
    # Pridedame individualių modelių prognozes
    colors = {
        'lstm': 'royalblue',
        'gru': 'forestgreen',
        'transformer': 'darkorange',
        'cnn': 'purple',
        'cnn_lstm': 'teal'
    }
    
    line_styles = {
        'lstm': 'dash',
        'gru': 'dot',
        'transformer': 'dashdot',
        'cnn': 'longdash',
        'cnn_lstm': 'longdashdot'
    }
    
    if 'models' in ensemble_data:
        for model_name, predictions in ensemble_data['models'].items():
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=predictions,
                    name=f"{model_name.upper()} prognozė",
                    line=dict(
                        color=colors.get(model_name, "gray"), 
                        width=1.5,
                        dash=line_styles.get(model_name, "solid")
                    )
                )
            )
    
    fig.update_layout(
        title="Ansamblio modelio prognozių palyginimas",
        xaxis_title="Data",
        yaxis_title="Bitcoin kaina (USD)",
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    return fig

def create_training_progress_chart(training_history):
    """
    Sukuria modelio mokymo progreso grafiką.
    
    Args:
        training_history (dict): Mokymo istorijos duomenys
        
    Returns:
        plotly.graph_objects.Figure: Plotly grafikas
    """
    if not training_history or 'loss' not in training_history:
        logger.warning("Nėra duomenų mokymo progreso grafikui")
        fig = go.Figure()
        fig.add_annotation(
            text="Nėra mokymo istorijos duomenų",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="red")
        )
        return fig
    
    # Sukuriame subplot layoutą
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Pridedame training loss
    fig.add_trace(
        go.Scatter(
            x=list(range(1, len(training_history['loss']) + 1)),
            y=training_history['loss'],
            name="Mokymo klaida",
            line=dict(color="#1f77b4", width=2)
        )
    )
    
    # Pridedame validation loss, jei yra
    if 'val_loss' in training_history:
        fig.add_trace(
            go.Scatter(
                x=list(range(1, len(training_history['val_loss']) + 1)),
                y=training_history['val_loss'],
                name="Validacijos klaida",
                line=dict(color="#ff7f0e", width=2)
            )
        )
    
    # Pridedame MAE, jei yra
    if 'mae' in training_history:
        fig.add_trace(
            go.Scatter(
                x=list(range(1, len(training_history['mae']) + 1)),
                y=training_history['mae'],
                name="MAE",
                line=dict(color="#2ca02c", width=2, dash="dash")
            ),
            secondary_y=True
        )
    
    # Atnaujina layoutą
    fig.update_layout(
        title="Modelio mokymo progresas",
        xaxis_title="Epochos",
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    # Update y-axes titles
    fig.update_yaxes(title_text="MSE klaida", secondary_y=False)
    if 'mae' in training_history:
        fig.update_yaxes(title_text="MAE klaida", secondary_y=True)
    
    return fig