import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class ChartCreator:
    @staticmethod
    def price_history_chart(price_data):
        """Sukuria Bitcoin kainos istorijos grafiką"""
        fig = go.Figure()
        
        # Pridedame kainų žvakutę
        fig.add_trace(
            go.Candlestick(
                x=price_data['dates'],
                open=price_data['open'],
                high=price_data['high'],
                low=price_data['low'],
                close=price_data['close'],
                name='BTC kaina'
            )
        )
        
        # Pridedame 7 dienų slankųjį vidurkį
        window = 7 * 24 * 4  # 7 dienos (4 15-min intervalai per valandą * 24 valandos * 7 dienos)
        closes = price_data['close']
        if len(closes) >= window:
            moving_avg = pd.Series(closes).rolling(window=window).mean().iloc[window-1:].tolist()
            
            fig.add_trace(
                go.Scatter(
                    x=price_data['dates'][window-1:],
                    y=moving_avg,
                    name='7 dienų vidurkis',
                    line=dict(color='orange', width=2)
                )
            )
        
        # Pridedame tūrio (volume) grafiką
        fig.add_trace(
            go.Bar(
                x=price_data['dates'],
                y=price_data['volume'],
                name='Tūris',
                marker=dict(color='rgba(0, 0, 255, 0.3)'),
                yaxis='y2'
            )
        )
        
        # Konfigūruojame grafiką
        fig.update_layout(
            title='Bitcoin kaina',
            yaxis=dict(
                title='Kaina (USD)',
                titlefont=dict(color='#1f77b4'),
                side='left'
            ),
            yaxis2=dict(
                title='Tūris',
                titlefont=dict(color='blue'),
                side='right',
                overlaying='y',
                showgrid=False
            ),
            xaxis=dict(
                title='Data',
                rangeslider=dict(visible=True),
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label='1d', step='day', stepmode='backward'),
                        dict(count=7, label='1w', step='day', stepmode='backward'),
                        dict(count=1, label='1m', step='month', stepmode='backward'),
                        dict(step='all')
                    ])
                )
            ),
            template='plotly_white'
        )
        
        return fig
    
    @staticmethod
    def metrics_comparison_chart(metrics_df):
        """Sukuria modelių metrikų palyginimo grafiką"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "RMSE (mažesnis geriau)",
                "MAE (mažesnis geriau)",
                "MAPE % (mažesnis geriau)",
                "R² (didesnis geriau)"
            ),
            vertical_spacing=0.15,
            horizontal_spacing=0.1
        )
        
        # Spalvų paletė
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
        # RMSE palyginimas
        fig.add_trace(
            go.Bar(
                x=metrics_df['Modelis'],
                y=metrics_df['RMSE'],
                marker_color=colors[:len(metrics_df)],
                text=metrics_df['RMSE'].round(2),
                textposition='auto',
                name='RMSE'
            ),
            row=1, col=1
        )
        
        # MAE palyginimas
        fig.add_trace(
            go.Bar(
                x=metrics_df['Modelis'],
                y=metrics_df['MAE'],
                marker_color=colors[:len(metrics_df)],
                text=metrics_df['MAE'].round(2),
                textposition='auto',
                name='MAE'
            ),
            row=1, col=2
        )
        
        # MAPE palyginimas
        fig.add_trace(
            go.Bar(
                x=metrics_df['Modelis'],
                y=metrics_df['MAPE (%)'],
                marker_color=colors[:len(metrics_df)],
                text=metrics_df['MAPE (%)'].round(2),
                textposition='auto',
                name='MAPE %'
            ),
            row=2, col=1
        )
        
        # R² palyginimas
        fig.add_trace(
            go.Bar(
                x=metrics_df['Modelis'],
                y=metrics_df['R²'],
                marker_color=colors[:len(metrics_df)],
                text=metrics_df['R²'].round(4),
                textposition='auto',
                name='R²'
            ),
            row=2, col=2
        )
        
        # Konfigūruojame grafiką
        fig.update_layout(
            title="Modelių metrikų palyginimas",
            height=700,
            showlegend=False,
            template="plotly_white"
        )
        
        return fig
    
    @staticmethod
    def model_prediction_chart(model_name, predictions):
        """Sukuria modelio prognozių grafiką"""
        fig = go.Figure()
        
        # Konvertuojame datas į datetime objektus, jei jos yra string
        dates = predictions['dates']
        if isinstance(dates[0], str):
            dates = [datetime.strptime(d, '%Y-%m-%d') for d in dates]
        
        # Pridedame faktines kainas
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=predictions['actual'],
                name='Faktinė kaina',
                line=dict(color='black', width=2)
            )
        )
        
        # Pridedame modelio prognozes
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=predictions['predicted'],
                name=f'{model_name.upper()} prognozė',
                line=dict(color='blue', width=2, dash='dash')
            )
        )
        
        # Skaičiuojame prognozių tikslumą
        rmse = np.sqrt(np.mean((np.array(predictions['actual']) - np.array(predictions['predicted']))**2))
        
        # Konfigūruojame grafiką
        fig.update_layout(
            title=f"{model_name.upper()} modelio prognozės (RMSE: {rmse:.2f})",
            xaxis_title="Data",
            yaxis_title="Bitcoin kaina (USD)",
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        return fig
    
    @staticmethod
    def ensemble_prediction_chart(ensemble_data):
        """Sukuria ansamblio modelio prognozių grafiką"""
        fig = go.Figure()
        
        # Konvertuojame datas į datetime objektus, jei jos yra string
        dates = ensemble_data['dates']
        if isinstance(dates[0], str):
            dates = [datetime.strptime(d, '%Y-%m-%d') for d in dates]
        
        # Pridedame faktines kainas
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=ensemble_data['actual'],
                name='Faktinė kaina',
                line=dict(color='black', width=3)
            )
        )
        
        # Pridedame ansamblio prognozes
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=ensemble_data['ensemble'],
                name='Ansamblio prognozė',
                line=dict(color='crimson', width=3)
            )
        )
        
        # Spalvų paletė ir linijų stiliai
        colors = {
            'lstm': 'royalblue',
            'gru': 'forestgreen',
            'transformer': 'darkorange',
            'cnn': 'purple',
            'cnn_lstm': 'teal',
            'arima': 'saddlebrown'
        }
        
        line_styles = {
            'lstm': 'dash',
            'gru': 'dot',
            'transformer': 'dashdot',
            'cnn': 'longdash',
            'cnn_lstm': 'longdashdot',
            'arima': 'dash'
        }
        
        # Pridedame individualių modelių prognozes
        for model_name, predictions in ensemble_data['models'].items():
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=predictions,
                    name=f'{model_name.upper()} prognozė',
                    line=dict(
                        color=colors.get(model_name, 'gray'),
                        width=1.5,
                        dash=line_styles.get(model_name, 'solid')
                    ),
                    opacity=0.7
                )
            )
        
        # Konfigūruojame grafiką
        fig.update_layout(
            title="Ansamblio modelio prognozės",
            xaxis_title="Data",
            yaxis_title="Bitcoin kaina (USD)",
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        return fig
    
    @staticmethod
    def prediction_chart(prediction_result):
        """Sukuria realaus laiko prognozės grafiką"""
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
        
        # Dabar, dabar+15min, dabar+30min
        dates = [
            datetime.now(),
            datetime.now() + timedelta(minutes=15),
            datetime.now() + timedelta(minutes=30)
        ]
        
        # Kainos: paskutinė žinoma, paskutinė žinoma, prognozė
        prices = [
            prediction_result['last_price'],
            prediction_result['last_price'],
            prediction_result['prediction']
        ]
        
        # Pridedame faktinę kainą
        fig.add_trace(
            go.Scatter(
                x=[dates[0]],
                y=[prices[0]],
                mode='markers',
                name='Dabar',
                marker=dict(color='black', size=10, symbol='circle')
            )
        )
        
        # Pridedame prognozę
        direction_color = 'green' if prediction_result['direction'] == 'up' else 'red'
        
        fig.add_trace(
            go.Scatter(
                x=dates[1:],
                y=prices[1:],
                name='Prognozė',
                line=dict(color=direction_color, width=2, dash='dash')
            )
        )
        
        # Pridedame prognozės tašką
        fig.add_trace(
            go.Scatter(
                x=[dates[2]],
                y=[prices[2]],
                mode='markers',
                name=f"Prognozuojama ({prediction_result['change_percent']:.2f}%)",
                marker=dict(
                    color=direction_color,
                    size=12,
                    symbol='triangle-up' if prediction_result['direction'] == 'up' else 'triangle-down'
                )
            )
        )
        
        # Konfigūruojame grafiką
        fig.update_layout(
            title=f"{prediction_result['model'].upper()} modelio prognozė",
            xaxis_title="Laikas",
            yaxis_title="Bitcoin kaina (USD)",
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # Pridedame anotacijas
        fig.add_annotation(
            x=dates[2],
            y=prices[2],
            text=f"{prediction_result['change_percent']:.2f}%",
            showarrow=True,
            arrowhead=2,
            arrowcolor=direction_color,
            arrowsize=1,
            arrowwidth=2,
            ax=0,
            ay=-40 if prediction_result['direction'] == 'up' else 40
        )
        
        return fig

# Sukuriame globalų objektą
create_charts = ChartCreator()