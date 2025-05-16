"""
Prekybos statistikos modulis
-----------------------------
Šis modulis skaičiuoja ir analizuoja prekybos statistiką,
įskaitant pelną/nuostolius, sandorio dydžius ir kitas metrikas.
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TradingStatistics:
    """
    Prekybos statistikos klasė, kuri skaičiuoja ir analizuoja
    prekybos rezultatus.
    """
    def __init__(self):
        """
        Inicializuoja prekybos statistikos klasę.
        """
        self.trades = []
        self.metrics = {}
        logger.info("Inicializuota prekybos statistikos klasė")
    
    def add_trade(self, trade_info):
        """
        Prideda prekybos operaciją į statistikos skaičiavimą.
        
        Args:
            trade_info (dict): Prekybos operacijos informacija
        """
        self.trades.append(trade_info)
        logger.debug(f"Pridėta prekybos operacija į statistiką: {trade_info}")
    
    def calculate_metrics(self):
        """
        Apskaičiuoja prekybos statistikos metrikas.
        
        Returns:
            dict: Metrikos
        """
        if not self.trades:
            logger.warning("Nėra prekybos operacijų metrikų skaičiavimui")
            return {}
        
        trades_df = pd.DataFrame(self.trades)
        
        # Bazinius metrikas
        metrics = {
            'total_trades': len(self.trades),
            'calculation_time': datetime.now()
        }
        
        # Jei turime užbaigtas operacijas su įėjimo ir išėjimo informacija
        if 'exit_price' in trades_df.columns and 'entry_price' in trades_df.columns:
            # Skaičiuojame pelną/nuostolį
            profitable_trades = trades_df[trades_df['profit_loss'] > 0]
            losing_trades = trades_df[trades_df['profit_loss'] <= 0]
            
            metrics['profitable_trades'] = len(profitable_trades)
            metrics['losing_trades'] = len(losing_trades)
            metrics['win_rate'] = len(profitable_trades) / len(trades_df) if len(trades_df) > 0 else 0
            
            metrics['total_profit'] = profitable_trades['profit_loss'].sum() if len(profitable_trades) > 0 else 0
            metrics['total_loss'] = losing_trades['profit_loss'].sum() if len(losing_trades) > 0 else 0
            metrics['net_profit'] = metrics['total_profit'] + metrics['total_loss']
            
            metrics['average_profit'] = profitable_trades['profit_loss'].mean() if len(profitable_trades) > 0 else 0
            metrics['average_loss'] = losing_trades['profit_loss'].mean() if len(losing_trades) > 0 else 0
            
            metrics['profit_factor'] = abs(metrics['total_profit'] / metrics['total_loss']) if metrics['total_loss'] != 0 else float('inf')
            
            # Rizikos metrikos
            if 'exit_reason' in trades_df.columns:
                stop_loss_exits = trades_df[trades_df['exit_reason'] == 'stop_loss']
                take_profit_exits = trades_df[trades_df['exit_reason'] == 'take_profit']
                
                metrics['stop_loss_exits'] = len(stop_loss_exits)
                metrics['take_profit_exits'] = len(take_profit_exits)
                metrics['stop_loss_rate'] = len(stop_loss_exits) / len(trades_df) if len(trades_df) > 0 else 0
                metrics['take_profit_rate'] = len(take_profit_exits) / len(trades_df) if len(trades_df) > 0 else 0
            
            # Mokesčių ir praslydimo metrikos
            if 'fees' in trades_df.columns:
                metrics['total_fees'] = trades_df['fees'].sum()
                metrics['average_fees'] = trades_df['fees'].mean()
            
            if 'slippage' in trades_df.columns:
                metrics['total_slippage'] = trades_df['slippage'].sum()
                metrics['average_slippage'] = trades_df['slippage'].mean()
        
        # Saugome metrikas
        self.metrics = metrics
        
        logger.info(f"Apskaičiuotos prekybos statistikos metrikos: "
                   f"{len(self.trades)} operacijos, win rate: {metrics.get('win_rate', 0)*100:.2f}%, "
                   f"grynasis pelnas: ${metrics.get('net_profit', 0):.2f}")
        
        return metrics
    
    def generate_report(self, include_trades=False):
        """
        Generuoja prekybos statistikos ataskaitą.
        
        Args:
            include_trades (bool): Ar įtraukti visas prekybos operacijas į ataskaitą
        
        Returns:
            dict: Ataskaita
        """
        # Apskaičiuojame metrikas, jei dar neapskaičiuotos
        if not self.metrics:
            self.calculate_metrics()
        
        # Sukuriame bazinę ataskaitą
        report = {
            'metrics': self.metrics,
            'summary': {
                'start_date': min([t.get('entry_timestamp', t.get('timestamp')) for t in self.trades]) if self.trades else None,
                'end_date': max([t.get('exit_timestamp', t.get('timestamp')) for t in self.trades]) if self.trades else None,
                'total_trades': len(self.trades),
                'win_rate': self.metrics.get('win_rate', 0),
                'net_profit': self.metrics.get('net_profit', 0),
                'profit_factor': self.metrics.get('profit_factor', 0)
            }
        }
        
        # Jei reikia, įtraukiame visas prekybos operacijas
        if include_trades:
            report['trades'] = self.trades
        
        return report
    
    def plot_performance(self, save_path=None):
        """
        Sukuria prekybos rezultatų grafiką.
        
        Args:
            save_path (str, optional): Kelias, kur išsaugoti grafiką
        
        Returns:
            matplotlib.figure.Figure: Grafiko objektas
        """
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            if not self.trades:
                logger.warning("Nėra prekybos operacijų grafiko kūrimui")
                return None
            
            # Konvertuojame prekybos operacijas į DataFrame
            trades_df = pd.DataFrame(self.trades)
            
            if 'profit_loss' not in trades_df.columns:
                logger.warning("Trūksta profit_loss stulpelio grafiko kūrimui")
                return None
            
            # Sukuriame kaupiamojo pelno/nuostolio stulpelį
            trades_df['cumulative_profit'] = trades_df['profit_loss'].cumsum()
            
            # Sukuriame grafiką
            plt.figure(figsize=(12, 8))
            
            # Sukuriame kelis subplots
            gs = plt.GridSpec(3, 2, height_ratios=[2, 1, 1])
            
            # 1. Kaupiamasis pelnas/nuostolis
            ax1 = plt.subplot(gs[0, :])
            ax1.plot(trades_df.index, trades_df['cumulative_profit'], label='Kaupiamasis P/L')
            ax1.set_title('Kaupiamasis pelnas/nuostolis')
            ax1.set_ylabel('USD')
            ax1.legend()
            ax1.grid(True)
            
            # 2. Atskiros operacijos
            ax2 = plt.subplot(gs[1, :])
            colors = ['green' if pl > 0 else 'red' for pl in trades_df['profit_loss']]
            ax2.bar(trades_df.index, trades_df['profit_loss'], color=colors)
            ax2.set_title('Atskirų operacijų P/L')
            ax2.set_ylabel('USD')
            ax2.grid(True)
            
            # 3. Operacijų pasiskirstymas pagal dydį
            ax3 = plt.subplot(gs[2, 0])
            sns.histplot(data=trades_df, x='profit_loss', bins=20, kde=True, ax=ax3)
            ax3.set_title('P/L pasiskirstymas')
            ax3.set_xlabel('USD')
            
            # 4. Operacijų pasiskirstymas pagal tipą (jei yra)
            ax4 = plt.subplot(gs[2, 1])
            if 'exit_reason' in trades_df.columns:
                trades_df['exit_reason'].value_counts().plot(kind='pie', ax=ax4, autopct='%1.1f%%')
                ax4.set_title('Operacijų pasiskirstymas pagal tipą')
            else:
                trades_df['trade_type'].value_counts().plot(kind='pie', ax=ax4, autopct='%1.1f%%')
                ax4.set_title('Pirkimų/pardavimų pasiskirstymas')
            
            plt.tight_layout()
            
            # Išsaugome grafiką, jei nurodyta
            if save_path:
                plt.savefig(save_path)
                logger.info(f"Grafikas išsaugotas: {save_path}")
            
            return plt.gcf()
            
        except Exception as e:
            logger.error(f"Klaida kuriant prekybos rezultatų grafiką: {e}")
            return None