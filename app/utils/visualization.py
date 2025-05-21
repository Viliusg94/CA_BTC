import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Pridėta nauja klasė, kuri tarnaus kaip fasadas visoms grafikų funkcijoms
class Charts:
    @staticmethod
    def price_history_chart(price_history):
        return create_price_history_chart(price_history)
    
    @staticmethod
    def model_prediction_chart(model_name, prediction_data):
        return model_prediction_chart(model_name, prediction_data)
    
    @staticmethod
    def ensemble_prediction_chart(ensemble_data):
        return ensemble_prediction_chart(ensemble_data)
    
    @staticmethod
    def metrics_comparison_chart(metrics_df):
        return metrics_comparison_chart(metrics_df)
    
    @staticmethod
    def prediction_chart(prediction_result):
        return prediction_chart(prediction_result)

# Sukuriame objektą, kurį naudos importuojantis kodas
create_charts = Charts()

def create_price_history_chart(price_history):
    """
    Sukuria Bitcoin kainos istorijos grafiką
    
    Args:
        price_history (pd.DataFrame arba dict): Kainos istorijos duomenys
        
    Returns:
        go.Figure: Plotly grafikas
    """
    if price_history is None or len(price_history) == 0:
        # Jei nėra duomenų, grąžiname tuščią grafiką
        fig = go.Figure()
        fig.update_layout(
            title="Bitcoin kainų istorija",
            xaxis=dict(
                title=dict(
                    text="Data",
                    font=dict(size=14)
                )
            ),
            yaxis=dict(
                title=dict(
                    text="Kaina (USD)",
                    font=dict(size=14)
                )
            )
        )
        fig.add_annotation(
            text="Duomenų nerasta",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    # Konvertuojame į pandas DataFrame, jei pateiktas žodynas
    if isinstance(price_history, dict):
        # Tipiški žodyno raktai būtų 'date' ir 'close'
        if 'date' in price_history and 'close' in price_history:
            df = pd.DataFrame({
                'date': price_history['date'],
                'close': price_history['close']
            })
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
        else:
            # Jei nežinoma žodyno struktūra, kuriame tuščią DataFrame
            df = pd.DataFrame()
    else:
        # Jei jau yra DataFrame, tiesiog naudojame jį
        df = price_history
    
    # Jei konvertavus neturime duomenų, grąžiname tuščią grafiką
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            title="Bitcoin kainų istorija",
            xaxis=dict(
                title=dict(
                    text="Data",
                    font=dict(size=14)
                )
            ),
            yaxis=dict(
                title=dict(
                    text="Kaina (USD)",
                    font=dict(size=14)
                )
            )
        )
        fig.add_annotation(
            text="Duomenų formatas netinkamas",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    # Sukuriame pagrindinį grafiką
    fig = go.Figure()
    
    # Pridedame kainų liniją
    fig.add_trace(
        go.Scatter(
            x=df.index if hasattr(df, 'index') else df['date'] if 'date' in df.columns else list(range(len(df))), 
            y=df['close'] if 'close' in df.columns else df.iloc[:, 0],
            name="Kaina",
            line=dict(color='#1f77b4', width=2),
            hovertemplate='%{x|%Y-%m-%d}: %{y:$,.2f}<extra></extra>'
        )
    )
    
    # Atnaujinti išdėstymą
    fig.update_layout(
        title="Bitcoin kainų istorija",
        xaxis=dict(
            title=dict(
                text="Data",
                font=dict(size=14)
            ),
            gridcolor='#f5f5f5',
            tickformat='%Y-%m-%d'
        ),
        yaxis=dict(
            title=dict(
                text="Kaina (USD)",
                font=dict(size=14)
            ),
            gridcolor='#f5f5f5',
            tickprefix='$'
        ),
        plot_bgcolor='white',
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Roboto"
        ),
        margin=dict(l=10, r=10, t=50, b=10),
        showlegend=False
    )
    
    return fig

def model_prediction_chart(model_name, prediction_data):
    """
    Sukuria modelio prognozės grafiką
    
    Args:
        model_name (str): Modelio pavadinimas
        prediction_data (dict): Prognozės duomenys
        
    Returns:
        go.Figure: Plotly grafikas
    """
    if prediction_data is None or len(prediction_data) == 0:
        # Jei nėra duomenų, grąžiname tuščią grafiką
        fig = go.Figure()
        fig.update_layout(
            title=f"{model_name.upper()} modelio prognozė",
            xaxis=dict(
                title=dict(
                    text="Data",
                    font=dict(size=14)
                )
            ),
            yaxis=dict(
                title=dict(
                    text="Kaina (USD)",
                    font=dict(size=14)
                )
            )
        )
        fig.add_annotation(
            text="Duomenų nerasta",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    # Sukuriame pagrindinį grafiką
    fig = go.Figure()
    
    # Pridedame faktinių kainų liniją
    if 'actual_dates' in prediction_data and 'actual_prices' in prediction_data:
        fig.add_trace(
            go.Scatter(
                x=prediction_data['actual_dates'], 
                y=prediction_data['actual_prices'],
                name="Faktinė kaina",
                line=dict(color='#1f77b4', width=2),
                hovertemplate='%{x|%Y-%m-%d}: %{y:$,.2f}<extra></extra>'
            )
        )
    
    # Pridedame prognozių liniją
    if 'prediction_dates' in prediction_data and 'predicted_prices' in prediction_data:
        fig.add_trace(
            go.Scatter(
                x=prediction_data['prediction_dates'], 
                y=prediction_data['predicted_prices'],
                name="Prognozė",
                line=dict(color='#ff7f0e', width=2, dash='dash'),
                hovertemplate='%{x|%Y-%m-%d}: %{y:$,.2f}<extra></extra>'
            )
        )
    
    # Atnaujinti išdėstymą
    fig.update_layout(
        title=f"{model_name.upper()} modelio prognozė",
        xaxis=dict(
            title=dict(
                text="Data",
                font=dict(size=14)
            ),
            gridcolor='#f5f5f5',
            tickformat='%Y-%m-%d'
        ),
        yaxis=dict(
            title=dict(
                text="Kaina (USD)",
                font=dict(size=14)
            ),
            gridcolor='#f5f5f5',
            tickprefix='$'
        ),
        plot_bgcolor='white',
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Roboto"
        ),
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def ensemble_prediction_chart(ensemble_data):
    """
    Sukuria ansamblio prognozės grafiką
    
    Args:
        ensemble_data (dict): Ansamblio prognozės duomenys
        
    Returns:
        go.Figure: Plotly grafikas
    """
    if ensemble_data is None or len(ensemble_data) == 0:
        # Jei nėra duomenų, grąžiname tuščią grafiką
        fig = go.Figure()
        fig.update_layout(
            title="Ansamblio prognozė",
            xaxis=dict(
                title=dict(
                    text="Data",
                    font=dict(size=14)
                )
            ),
            yaxis=dict(
                title=dict(
                    text="Kaina (USD)",
                    font=dict(size=14)
                )
            )
        )
        fig.add_annotation(
            text="Duomenų nerasta",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    # Sukuriame pagrindinį grafiką
    fig = go.Figure()
    
    # Pridedame faktinių kainų liniją
    if 'actual_dates' in ensemble_data and 'actual_prices' in ensemble_data:
        fig.add_trace(
            go.Scatter(
                x=ensemble_data['actual_dates'], 
                y=ensemble_data['actual_prices'],
                name="Faktinė kaina",
                line=dict(color='#1f77b4', width=2),
                hovertemplate='%{x|%Y-%m-%d}: %{y:$,.2f}<extra></extra>'
            )
        )
    
    # Pridedame ansamblio prognozės liniją
    if 'prediction_dates' in ensemble_data and 'ensemble_predictions' in ensemble_data:
        fig.add_trace(
            go.Scatter(
                x=ensemble_data['prediction_dates'], 
                y=ensemble_data['ensemble_predictions'],
                name="Ansamblio prognozė",
                line=dict(color='#ff7f0e', width=2, dash='dash'),
                hovertemplate='%{x|%Y-%m-%d}: %{y:$,.2f}<extra></extra>'
            )
        )
    
    # Atnaujinti išdėstymą
    fig.update_layout(
        title="Ansamblio prognozė",
        xaxis=dict(
            title=dict(
                text="Data",
                font=dict(size=14)
            ),
            gridcolor='#f5f5f5',
            tickformat='%Y-%m-%d'
        ),
        yaxis=dict(
            title=dict(
                text="Kaina (USD)",
                font=dict(size=14)
            ),
            gridcolor='#f5f5f5',
            tickprefix='$'
        ),
        plot_bgcolor='white',
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Roboto"
        ),
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def metrics_comparison_chart(metrics_df):
    """
    Sukuria modelių metrikų palyginimo grafiką
    
    Args:
        metrics_df (pd.DataFrame): Metrikų duomenys
        
    Returns:
        go.Figure: Plotly grafikas
    """
    if metrics_df is None or len(metrics_df) == 0:
        # Jei nėra duomenų, grąžiname tuščią grafiką
        fig = go.Figure()
        fig.update_layout(
            title="Modelių metrikų palyginimas",
            xaxis=dict(
                title=dict(
                    text="Modelis",
                    font=dict(size=14)
                )
            ),
            yaxis=dict(
                title=dict(
                    text="Metrikos vertė",
                    font=dict(size=14)
                )
            )
        )
        fig.add_annotation(
            text="Duomenų nerasta",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    # Konvertuojame į DataFrame, jei tai žodynas
    if isinstance(metrics_df, dict):
        metrics_df = pd.DataFrame(metrics_df)
    
    # Sukuriame stulpelinį grafiką
    fig = go.Figure()
    
    # Pridedame MSE stulpelius
    if 'MSE' in metrics_df.columns:
        fig.add_trace(
            go.Bar(
                x=metrics_df.index,
                y=metrics_df['MSE'],
                name='MSE',
                marker_color='#1f77b4',
                hovertemplate='%{x}: %{y:.4f}<extra></extra>'
            )
        )
    
    # Pridedame MAE stulpelius
    if 'MAE' in metrics_df.columns:
        fig.add_trace(
            go.Bar(
                x=metrics_df.index,
                y=metrics_df['MAE'],
                name='MAE',
                marker_color='#ff7f0e',
                hovertemplate='%{x}: %{y:.4f}<extra></extra>'
            )
        )
    
    # Atnaujinti išdėstymą
    fig.update_layout(
        title="Modelių metrikų palyginimas",
        xaxis=dict(
            title=dict(
                text="Modelis",
                font=dict(size=14)
            ),
            gridcolor='#f5f5f5'
        ),
        yaxis=dict(
            title=dict(
                text="Metrikos vertė",
                font=dict(size=14)
            ),
            gridcolor='#f5f5f5'
        ),
        plot_bgcolor='white',
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Roboto"
        ),
        margin=dict(l=10, r=10, t=50, b=10),
        barmode='group',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def prediction_chart(prediction_result):
    """
    Sukuria prognozės grafiką
    
    Args:
        prediction_result (dict): Prognozės rezultatai
        
    Returns:
        go.Figure: Plotly grafikas
    """
    if prediction_result is None or 'prediction' not in prediction_result:
        # Jei nėra duomenų, grąžiname tuščią grafiką
        fig = go.Figure()
        fig.update_layout(
            title="Bitcoin kainos prognozė",
            xaxis=dict(
                title=dict(
                    text="Data",
                    font=dict(size=14)
                )
            ),
            yaxis=dict(
                title=dict(
                    text="Kaina (USD)",
                    font=dict(size=14)
                )
            )
        )
        fig.add_annotation(
            text="Duomenų nerasta",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    # Sukuriame pagrindinį grafiką
    fig = go.Figure()
    
    # Pridedame faktinių kainų liniją, jei yra
    if 'historical_data' in prediction_result and prediction_result['historical_data']:
        history = prediction_result['historical_data']
        fig.add_trace(
            go.Scatter(
                x=history['dates'] if 'dates' in history else pd.date_range(end=datetime.now(), periods=len(history['prices'])),
                y=history['prices'],
                name="Istorinė kaina",
                line=dict(color='#1f77b4', width=2),
                hovertemplate='%{x|%Y-%m-%d}: %{y:$,.2f}<extra></extra>'
            )
        )
    
    # Pridedame prognozės tašką
    prediction_date = prediction_result.get('prediction_date', datetime.now() + timedelta(days=1))
    prediction_value = prediction_result['prediction']
    
    fig.add_trace(
        go.Scatter(
            x=[prediction_date],
            y=[prediction_value],
            name="Prognozė",
            mode='markers',
            marker=dict(
                color='#ff7f0e',
                size=12,
                symbol='diamond'
            ),
            hovertemplate='%{x|%Y-%m-%d}: %{y:$,.2f}<extra></extra>'
        )
    )
    
    # Atnaujinti išdėstymą
    fig.update_layout(
        title="Bitcoin kainos prognozė",
        xaxis=dict(
            title=dict(
                text="Data",
                font=dict(size=14)
            ),
            gridcolor='#f5f5f5',
            tickformat='%Y-%m-%d'
        ),
        yaxis=dict(
            title=dict(
                text="Kaina (USD)",
                font=dict(size=14)
            ),
            gridcolor='#f5f5f5',
            tickprefix='$'
        ),
        plot_bgcolor='white',
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Roboto"
        ),
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig