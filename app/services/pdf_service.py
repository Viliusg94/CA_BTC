import os
import io
import matplotlib
matplotlib.use('Agg')  # Nenaudoti GUI
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from datetime import datetime
import logging
from reportlab.lib.pagesizes import A4  # ŠI EILUTĖ SUKELIA KLAIDĄ
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm, inch
from reportlab.platypus import PageBreak, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import base64

class PdfGenerator:
    """
    Klasė, skirta generuoti PDF ataskaitas su modelio treniravimo rezultatais
    """
    
    def __init__(self):
        """
        Inicializuoja PDF generatorių
        """
        # Nustatome kelią iki laikinų failų direktorijos
        self.temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp')
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Stilių rinkinys
        self.styles = getSampleStyleSheet()
        
        # Sukuriame papildomus stilius
        self.styles.add(ParagraphStyle(name='Title', 
                                   parent=self.styles['Heading1'], 
                                   fontSize=18, 
                                   spaceAfter=10))
        
        self.styles.add(ParagraphStyle(name='Subtitle', 
                                   parent=self.styles['Heading2'], 
                                   fontSize=16, 
                                   spaceAfter=8))
        
        self.styles.add(ParagraphStyle(name='Section', 
                                   parent=self.styles['Heading3'], 
                                   fontSize=14, 
                                   spaceAfter=6))
        
        self.styles.add(ParagraphStyle(name='Normal_Justify', 
                                   parent=self.styles['Normal'], 
                                   alignment=4))  # 4 = justify
        
        self.styles.add(ParagraphStyle(name='Small', 
                                   parent=self.styles['Normal'], 
                                   fontSize=8))
        
        self.styles.add(ParagraphStyle(name='TableHeader', 
                                   parent=self.styles['Normal'], 
                                   fontSize=10, 
                                   alignment=1))  # 1 = center
    
    def generate_model_report(self, model_config, metrics, output_file):
        """
        Generuoja PDF ataskaitą su modelio treniravimo rezultatais
        
        Args:
            model_config (dict): Modelio konfigūracija
            metrics (list): Metrikų sąrašas pagal epochas
            output_file (str): Išvesties PDF failo kelias
            
        Returns:
            bool: True, jei ataskaita sukurta sėkmingai, False priešingu atveju
        """
        try:
            # Sukuriame PDF dokumentą
            doc = SimpleDocTemplate(
                output_file,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            # Turinio elementų sąrašas
            elements = []
            
            # Antraštė
            title = f"Modelio treniravimo ataskaita"
            elements.append(Paragraph(title, self.styles['Title']))
            
            # Modelio apžvalga
            elements.append(Paragraph("Modelio informacija", self.styles['Subtitle']))
            
            # Pagrindinė modelio informacija
            model_info_data = [
                ["Pavadinimas:", model_config.get('name', 'Nenurodyta')],
                ["Tipas:", model_config.get('type', 'Nenurodyta').upper()],
                ["ID:", model_config.get('training_id', 'Nenurodyta')],
                ["Sukurtas:", model_config.get('created_at', 'Nenurodyta')]
            ]
            
            if 'description' in model_config and model_config['description']:
                model_info_data.append(["Aprašymas:", model_config.get('description')])
            
            # Modelio informacijos lentelė
            model_info_table = Table(model_info_data, colWidths=[3*cm, 12*cm])
            model_info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            
            elements.append(model_info_table)
            elements.append(Spacer(1, 0.5*cm))
            
            # Modelio parametrai
            elements.append(Paragraph("Modelio parametrai", self.styles['Subtitle']))
            
            if 'parameters' in model_config:
                params = model_config['parameters']
                
                # Pagrindiniai parametrai
                param_data = []
                
                # Antraštės
                param_data.append(["Parametras", "Reikšmė"])
                
                # Bendri parametrai
                if 'epochs' in params:
                    param_data.append(["Epochų skaičius", str(params['epochs'])])
                if 'batch_size' in params:
                    param_data.append(["Batch dydis", str(params['batch_size'])])
                if 'learning_rate' in params:
                    param_data.append(["Mokymosi sparta", str(params['learning_rate'])])
                if 'dropout' in params:
                    param_data.append(["Dropout", str(params['dropout'])])
                if 'layers' in params:
                    param_data.append(["Sluoksnių skaičius", str(params['layers'])])
                if 'neurons' in params:
                    param_data.append(["Neuronų skaičius", str(params['neurons'])])
                
                # Specifiniai parametrai
                if 'specific' in params and params['specific']:
                    for key, value in params['specific'].items():
                        param_data.append([key.capitalize(), str(value)])
                
                # Parametrų lentelė
                param_table = Table(param_data, colWidths=[7*cm, 8*cm])
                param_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
                ]))
                
                elements.append(param_table)
                elements.append(Spacer(1, 0.5*cm))
            
            # Jei nėra metrikų, baigiam generuoti dokumentą
            if not metrics or len(metrics) == 0:
                elements.append(Paragraph("Nėra treniravimo metrikų", self.styles['Normal']))
                doc.build(elements)
                return True
            
            # Treniravimo rezultatai
            elements.append(Paragraph("Treniravimo rezultatai", self.styles['Subtitle']))
            
            # Apibendrinimas
            last_epoch = metrics[-1]
            best_val_acc_epoch = max(metrics, key=lambda x: x.get('val_accuracy', 0))
            best_val_loss_epoch = min(metrics, key=lambda x: x.get('val_loss', float('inf')))
            
            summary_data = [
                ["Metrika", "Geriausia reikšmė", "Epocha", "Galutinė reikšmė"],
                ["Validacijos tikslumas", f"{best_val_acc_epoch.get('val_accuracy', 0)*100:.2f}%", 
                 str(best_val_acc_epoch.get('epoch', 'N/A')), f"{last_epoch.get('val_accuracy', 0)*100:.2f}%"],
                ["Validacijos klaida", f"{best_val_loss_epoch.get('val_loss', 0):.6f}", 
                 str(best_val_loss_epoch.get('epoch', 'N/A')), f"{last_epoch.get('val_loss', 0):.6f}"],
                ["Treniravimo tikslumas", f"{max(metrics, key=lambda x: x.get('accuracy', 0)).get('accuracy', 0)*100:.2f}%", 
                 str(max(metrics, key=lambda x: x.get('accuracy', 0)).get('epoch', 'N/A')), f"{last_epoch.get('accuracy', 0)*100:.2f}%"],
                ["Treniravimo klaida", f"{min(metrics, key=lambda x: x.get('loss', float('inf'))).get('loss', 0):.6f}", 
                 str(min(metrics, key=lambda x: x.get('loss', float('inf'))).get('epoch', 'N/A')), f"{last_epoch.get('loss', 0):.6f}"]
            ]
            
            # Jei paskutinė epocha turi treniravimo laiką
            if 'training_time' in last_epoch:
                summary_data.append(["Bendras treniravimo laikas", "", "", f"{last_epoch.get('training_time', 0):.2f} s"])
            
            # Apibendrinimo lentelė
            summary_table = Table(summary_data, colWidths=[5*cm, 4*cm, 2*cm, 4*cm])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('BACKGROUND', (0, 1), (0, -1), colors.lightgrey),
                ('BACKGROUND', (1, 1), (1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            
            elements.append(summary_table)
            elements.append(Spacer(1, 0.5*cm))
            
            # Grafikai
            elements.append(Paragraph("Treniravimo grafikai", self.styles['Subtitle']))
            
            # Generuojame grafikus
            accuracy_chart = self._generate_accuracy_chart(metrics)
            if accuracy_chart:
                elements.append(Image(accuracy_chart, width=16*cm, height=10*cm))
                elements.append(Spacer(1, 0.3*cm))
            
            loss_chart = self._generate_loss_chart(metrics)
            if loss_chart:
                elements.append(Image(loss_chart, width=16*cm, height=10*cm))
                elements.append(Spacer(1, 0.3*cm))
            
            # Visų metrikų lentelė (pirmos ir paskutinės 5 epochos)
            elements.append(Paragraph("Detalios metrikos", self.styles['Subtitle']))
            
            # Paruošiame metrikų lentelę
            metrics_data = [["Epocha", "Loss", "Accuracy", "Val Loss", "Val Accuracy"]]
            
            # Pirmos 5 epochos
            for i in range(min(5, len(metrics))):
                epoch = metrics[i]
                metrics_data.append([
                    str(epoch.get('epoch', i+1)),
                    f"{epoch.get('loss', 0):.6f}",
                    f"{epoch.get('accuracy', 0)*100:.2f}%",
                    f"{epoch.get('val_loss', 0):.6f}",
                    f"{epoch.get('val_accuracy', 0)*100:.2f}%"
                ])
            
            # Jei yra daugiau nei 10 epochų, pridedame "..."
            if len(metrics) > 10:
                metrics_data.append(["...", "...", "...", "...", "..."])
            
            # Paskutinės 5 epochos
            if len(metrics) > 10:
                for i in range(max(5, len(metrics)-5), len(metrics)):
                    epoch = metrics[i]
                    metrics_data.append([
                        str(epoch.get('epoch', i+1)),
                        f"{epoch.get('loss', 0):.6f}",
                        f"{epoch.get('accuracy', 0)*100:.2f}%",
                        f"{epoch.get('val_loss', 0):.6f}",
                        f"{epoch.get('val_accuracy', 0)*100:.2f}%"
                    ])
            elif len(metrics) > 5:
                # Jei yra 6-10 epochų, pridedame likusias
                for i in range(5, len(metrics)):
                    epoch = metrics[i]
                    metrics_data.append([
                        str(epoch.get('epoch', i+1)),
                        f"{epoch.get('loss', 0):.6f}",
                        f"{epoch.get('accuracy', 0)*100:.2f}%",
                        f"{epoch.get('val_loss', 0):.6f}",
                        f"{epoch.get('val_accuracy', 0)*100:.2f}%"
                    ])
            
            # Metrikų lentelė
            metrics_table = Table(metrics_data, colWidths=[2*cm, 3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                ('BACKGROUND', (0, 1), (0, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 8)
            ]))
            
            elements.append(metrics_table)
            
            # Išvados ir rekomendacijos
            elements.append(PageBreak())
            elements.append(Paragraph("Išvados ir rekomendacijos", self.styles['Subtitle']))
            
            # Analizuojame overfit
            overfit_loss = last_epoch.get('val_loss', 0) > last_epoch.get('loss', 0) * 1.2
            overfit_acc = last_epoch.get('accuracy', 0) > last_epoch.get('val_accuracy', 0) * 1.2
            
            conclusions = []
            
            if overfit_loss or overfit_acc:
                conclusions.append(Paragraph("Modelis rodo permokymą (overfitting) požymių:", self.styles['Normal']))
                conclusions_list = []
                
                if overfit_loss:
                    conclusions_list.append("Validacijos klaida (val_loss) yra žymiai didesnė nei treniravimo klaida (loss).")
                if overfit_acc:
                    conclusions_list.append("Treniravimo tikslumas (accuracy) yra žymiai didesnis nei validacijos tikslumas (val_accuracy).")
                
                for conclusion in conclusions_list:
                    conclusions.append(Paragraph(f"• {conclusion}", self.styles['Normal']))
                
                recommendations = [
                    "Padidinkite dropout reikšmę, kad sumažintumėte permokymą.",
                    "Sumažinkite modelio sudėtingumą (sluoksnių ar neuronų skaičių).",
                    "Pritaikykite L1/L2 regularizaciją.",
                    "Padidinkite treniravimo duomenų kiekį arba naudokite duomenų augmentaciją."
                ]
                
                conclusions.append(Spacer(1, 0.3*cm))
                conclusions.append(Paragraph("Rekomendacijos:", self.styles['Normal']))
                
                for recommendation in recommendations:
                    conclusions.append(Paragraph(f"• {recommendation}", self.styles['Normal']))
            else:
                # Jei nėra permokymų, pateikiame bendras išvadas
                val_acc = last_epoch.get('val_accuracy', 0)
                
                if val_acc >= 0.9:
                    conclusions.append(Paragraph("Modelis pasiekė puikų tikslumą (≥90%). Rekomenduojama:", self.styles['Normal']))
                    recommendations = [
                        "Išbandyti modelį su naujais, nematytais duomenimis.",
                        "Įvertinti modelio veikimą realiomis sąlygomis.",
                        "Eksportuoti modelį į produkcijos aplinką."
                    ]
                elif val_acc >= 0.8:
                    conclusions.append(Paragraph("Modelis pasiekė gerą tikslumą (≥80%). Rekomenduojama:", self.styles['Normal']))
                    recommendations = [
                        "Tęsti treniravimą su didesniu epochų skaičiumi.",
                        "Eksperimentuoti su mokymosi spartos (learning rate) sumažinimu.",
                        "Išbandyti skirtingus optimizatorius (pvz., Adam, RMSprop)."
                    ]
                else:
                    conclusions.append(Paragraph("Modelio tikslumas yra žemas (<80%). Rekomenduojama:", self.styles['Normal']))
                    recommendations = [
                        "Peržiūrėti modelio architektūrą ir padidinti sudėtingumą.",
                        "Išbandyti skirtingus hiperparametrus.",
                        "Padidinti treniravimo duomenų kiekį ar kokybę.",
                        "Išbandyti kitą modelio tipą."
                    ]
                
                for recommendation in recommendations:
                    conclusions.append(Paragraph(f"• {recommendation}", self.styles['Normal']))
            
            for conclusion in conclusions:
                elements.append(conclusion)
            
            # Sukuriame PDF
            doc.build(elements)
            
            return True
            
        except Exception as e:
            logging.error(f"Klaida generuojant PDF ataskaitą: {str(e)}")
            return False
    
    def _generate_accuracy_chart(self, metrics):
        """
        Sugeneruoja tiklumo (accuracy) grafiką
        
        Args:
            metrics (list): Metrikų sąrašas
            
        Returns:
            str: Sugeneruoto grafiko kelias arba None, jei nepavyko sugeneruoti
        """
        try:
            # Tikriname, ar metrikos turi reikiamus laukus
            if not all('accuracy' in m and 'val_accuracy' in m and 'epoch' in m for m in metrics):
                return None
            
            # Paruošiame duomenis
            epochs = [m['epoch'] for m in metrics]
            accuracy = [m['accuracy'] for m in metrics]
            val_accuracy = [m['val_accuracy'] for m in metrics]
            
            # Sukuriame grafiką
            plt.figure(figsize=(10, 6))
            plt.plot(epochs, accuracy, 'b-', label='Treniravimo tikslumas')
            plt.plot(epochs, val_accuracy, 'r-', label='Validacijos tikslumas')
            plt.title('Modelio tikslumas')
            plt.xlabel('Epocha')
            plt.ylabel('Tikslumas')
            plt.legend()
            plt.grid(True)
            
            # Išsaugome grafiką į atminties buferį
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            
            # Išsaugome grafiką į laikiną failą
            temp_file = os.path.join(self.temp_dir, f"accuracy_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            with open(temp_file, 'wb') as f:
                f.write(buf.getvalue())
            
            plt.close()
            
            return temp_file
            
        except Exception as e:
            logging.error(f"Klaida generuojant tiklumo grafiką: {str(e)}")
            return None
    
    def _generate_loss_chart(self, metrics):
        """
        Sugeneruoja klaidos (loss) grafiką
        
        Args:
            metrics (list): Metrikų sąrašas
            
        Returns:
            str: Sugeneruoto grafiko kelias arba None, jei nepavyko sugeneruoti
        """
        try:
            # Tikriname, ar metrikos turi reikiamus laukus
            if not all('loss' in m and 'val_loss' in m and 'epoch' in m for m in metrics):
                return None
            
            # Paruošiame duomenis
            epochs = [m['epoch'] for m in metrics]
            loss = [m['loss'] for m in metrics]
            val_loss = [m['val_loss'] for m in metrics]
            
            # Sukuriame grafiką
            plt.figure(figsize=(10, 6))
            plt.plot(epochs, loss, 'b-', label='Treniravimo klaida')
            plt.plot(epochs, val_loss, 'r-', label='Validacijos klaida')
            plt.title('Modelio klaida')
            plt.xlabel('Epocha')
            plt.ylabel('Klaida')
            plt.legend()
            plt.grid(True)
            
            # Išsaugome grafiką į atminties buferį
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            
            # Išsaugome grafiką į laikiną failą
            temp_file = os.path.join(self.temp_dir, f"loss_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            with open(temp_file, 'wb') as f:
                f.write(buf.getvalue())
            
            plt.close()
            
            return temp_file
            
        except Exception as e:
            logging.error(f"Klaida generuojant klaidos grafiką: {str(e)}")
            return None