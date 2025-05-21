# Dokumentacijos ir pagalbos sistema - maršrutai vartotojo vadovui, DUK ir mokymams
from flask import Blueprint, render_template, request, redirect, url_for
import os
import json
import markdown
import logging

# Konfigūruojame logerį
logger = logging.getLogger(__name__)

# Sukuriame Blueprint
documentation_routes = Blueprint('docs', __name__, url_prefix='/docs')

# Kelias į dokumentacijos failus
DOCS_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'docs')

@documentation_routes.route('/')
def index():
    """Dokumentacijos pradžios puslapis"""
    return render_template('documentation/index.html', title="Dokumentacija ir pagalba")

@documentation_routes.route('/user-guide')
def user_guide():
    """Vartotojo vadovo puslapis"""
    # Gauname pasirinktą temą (jei yra)
    section = request.args.get('section', 'intro')
    
    # Nustatome galimų skyrių sąrašą
    sections = [
        {'id': 'intro', 'title': 'Įvadas', 'file': 'intro.md'},
        {'id': 'getting-started', 'title': 'Darbo pradžia', 'file': 'getting_started.md'},
        {'id': 'models', 'title': 'Darbas su modeliais', 'file': 'models.md'},
        {'id': 'training', 'title': 'Modelių treniravimas', 'file': 'training.md'},
        {'id': 'evaluation', 'title': 'Modelių validavimas', 'file': 'evaluation.md'},
        {'id': 'predictions', 'title': 'Prognozių sudarymas', 'file': 'predictions.md'},
    ]
    
    # Randame pasirinkto skyriaus informaciją
    current_section = next((s for s in sections if s['id'] == section), sections[0])
    
    try:
        # Bandome nuskaityti markdown failą
        md_file_path = os.path.join(DOCS_FOLDER, 'user_guide', current_section['file'])
        
        if os.path.exists(md_file_path):
            with open(md_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Konvertuojame Markdown į HTML
            html_content = markdown.markdown(content, extensions=['fenced_code'])
        else:
            html_content = f"<p>Deja, skyrius '{current_section['title']}' dar neturi turinio.</p>"
    except Exception as e:
        logger.error(f"Klaida nuskaitant dokumentacijos failą: {e}")
        html_content = f"<div class='alert alert-danger'>Klaida nuskaitant dokumentacijos failą: {str(e)}</div>"
    
    return render_template(
        'documentation/user_guide.html',
        title="Vartotojo vadovas",
        sections=sections,
        current_section=current_section,
        content=html_content
    )

@documentation_routes.route('/faq')
def faq():
    """DUK (Dažniausiai užduodami klausimai) puslapis"""
    try:
        # Bandome nuskaityti JSON failą su DUK
        faq_file_path = os.path.join(DOCS_FOLDER, 'faq.json')
        
        if os.path.exists(faq_file_path):
            with open(faq_file_path, 'r', encoding='utf-8') as f:
                faq_data = json.load(f)
        else:
            faq_data = []
    except Exception as e:
        logger.error(f"Klaida nuskaitant DUK failą: {e}")
        faq_data = []
    
    # Sugrupuojame klausimus pagal kategorijas
    categories = {}
    for item in faq_data:
        category = item.get('category', 'Bendra')
        if category not in categories:
            categories[category] = []
        categories[category].append(item)
    
    return render_template(
        'documentation/faq.html',
        title="Dažniausiai užduodami klausimai (DUK)",
        categories=categories
    )

@documentation_routes.route('/tutorials')
def tutorials():
    """Mokomosios medžiagos puslapis"""
    # Gauname pasirinktą temą (jei yra)
    tutorial = request.args.get('tutorial', 'intro')
    
    # Nustatome galimų temų sąrašą
    tutorials_list = [
        {'id': 'intro', 'title': 'Įvadas į Bitcoin prognozavimą', 'file': 'intro.md', 'difficulty': 'easy'},
        {'id': 'data-preparation', 'title': 'Duomenų paruošimas', 'file': 'data_preparation.md', 'difficulty': 'medium'},
        {'id': 'create-model', 'title': 'Modelio sukūrimas', 'file': 'create_model.md', 'difficulty': 'medium'},
        {'id': 'train-model', 'title': 'Modelio treniravimas', 'file': 'train_model.md', 'difficulty': 'medium'},
        {'id': 'evaluate-model', 'title': 'Modelio validavimas', 'file': 'evaluate_model.md', 'difficulty': 'hard'},
        {'id': 'make-predictions', 'title': 'Prognozių sudarymas', 'file': 'make_predictions.md', 'difficulty': 'hard'},
    ]
    
    # Randame pasirinktos temos informaciją
    current_tutorial = next((t for t in tutorials_list if t['id'] == tutorial), tutorials_list[0])
    
    try:
        # Bandome nuskaityti markdown failą
        md_file_path = os.path.join(DOCS_FOLDER, 'tutorials', current_tutorial['file'])
        
        if os.path.exists(md_file_path):
            with open(md_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Konvertuojame Markdown į HTML
            html_content = markdown.markdown(content, extensions=['fenced_code'])
        else:
            html_content = f"<p>Deja, tema '{current_tutorial['title']}' dar neturi turinio.</p>"
    except Exception as e:
        logger.error(f"Klaida nuskaitant mokomosios medžiagos failą: {e}")
        html_content = f"<div class='alert alert-danger'>Klaida nuskaitant mokomosios medžiagos failą: {str(e)}</div>"
    
    return render_template(
        'documentation/tutorials.html',
        title="Mokomoji medžiaga",
        tutorials=tutorials_list,
        current_tutorial=current_tutorial,
        content=html_content
    )

@documentation_routes.route('/api')
def api_docs():
    """API dokumentacijos puslapis"""
    return render_template('documentation/api.html', title="API dokumentacija")