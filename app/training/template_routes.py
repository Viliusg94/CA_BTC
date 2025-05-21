from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import os
import json
import logging
from datetime import datetime
from app.services.model_service import ModelService

# Inicializuojame šablonų valdymo maršrutus
template_management = Blueprint('template_management', __name__, url_prefix='/training/templates')

@template_management.route('/')
def index():
    """
    Parametrų šablonų valdymo puslapis
    """
    # Inicializuojame ModelService
    service = ModelService()
    
    # Gauname visus šablonus
    templates = service.get_model_templates()
    
    # Gauname filtravimo parametrus
    category = request.args.get('category', '')
    model_type = request.args.get('type', '')
    search = request.args.get('search', '')
    
    # Filtruojame šablonus pagal parametrus
    filtered_templates = {}
    for name, template in templates.items():
        # Tikriname, ar šablonas atitinka filtravimo kriterijus
        if category and template.get('category', '') != category:
            continue
        if model_type and template.get('type', '') != model_type:
            continue
        if search and search.lower() not in name.lower() and search.lower() not in template.get('description', '').lower():
            continue
        
        # Pridedame šabloną į filtruotų šablonų žodyną
        filtered_templates[name] = template
    
    # Gauname unikalias šablonų kategorijas
    categories = set()
    for template in templates.values():
        if 'category' in template:
            categories.add(template['category'])
    
    # Grupuojame šablonus pagal kategorijas
    templates_by_category = {}
    for name, template in filtered_templates.items():
        category = template.get('category', 'Kita')
        if category not in templates_by_category:
            templates_by_category[category] = {}
        templates_by_category[category][name] = template
    
    # Grąžiname šablonų valdymo puslapį
    return render_template(
        'training/templates.html',
        templates=filtered_templates,
        templates_by_category=templates_by_category,
        categories=sorted(categories)
    )

@template_management.route('/create', methods=['GET', 'POST'])
def create_template():
    """
    Naujo šablono sukūrimo puslapis
    """
    if request.method == 'POST':
        try:
            # Gauname duomenis iš formos
            template_name = request.form.get('template_name', '').strip()
            template_type = request.form.get('template_type', '').strip()
            template_category = request.form.get('template_category', '').strip()
            template_description = request.form.get('template_description', '').strip()
            
            # Tikriname, ar pavadinimas nenurodytas
            if not template_name:
                flash('Būtina įvesti šablono pavadinimą.', 'danger')
                return redirect(url_for('template_management.create_template'))
            
            # Gauname parametrų reikšmes
            parameters = {
                'epochs': int(request.form.get('epochs', 50)),
                'batch_size': int(request.form.get('batch_size', 32)),
                'learning_rate': float(request.form.get('learning_rate', 0.001)),
                'dropout': float(request.form.get('dropout', 0.2)),
                'layers': int(request.form.get('layers', 2)),
                'neurons': int(request.form.get('neurons', 64))
            }
            
            # Pridedame modelio tipo specifinius parametrus
            if 'specific_params' in request.form:
                parameters['specific'] = json.loads(request.form.get('specific_params', '{}'))
            
            # Sukuriame šablono duomenis
            template_data = {
                'type': template_type,
                'category': template_category,
                'description': template_description,
                'parameters': parameters,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Išsaugome šabloną
            service = ModelService()
            success = service.save_model_template(template_name, template_data)
            
            if success:
                flash(f'Šablonas "{template_name}" sėkmingai sukurtas.', 'success')
                return redirect(url_for('template_management.index'))
            else:
                flash('Klaida išsaugant šabloną.', 'danger')
                
        except Exception as e:
            logging.error(f"Klaida kuriant šabloną: {str(e)}")
            flash(f'Klaida kuriant šabloną: {str(e)}', 'danger')
            
    # Grąžiname šablono kūrimo formą
    return render_template('training/create_template.html')

@template_management.route('/edit/<template_name>', methods=['GET', 'POST'])
def edit_template(template_name):
    """
    Šablono redagavimo puslapis
    """
    # Inicializuojame ModelService
    service = ModelService()
    
    # Gauname šabloną
    templates = service.get_model_templates()
    if template_name not in templates:
        flash(f'Šablonas "{template_name}" nerastas.', 'danger')
        return redirect(url_for('template_management.index'))
    
    template = templates[template_name]
    
    if request.method == 'POST':
        try:
            # Gauname duomenis iš formos
            new_template_name = request.form.get('template_name', '').strip()
            template_type = request.form.get('template_type', '').strip()
            template_category = request.form.get('template_category', '').strip()
            template_description = request.form.get('template_description', '').strip()
            
            # Tikriname, ar pavadinimas nenurodytas
            if not new_template_name:
                flash('Būtina įvesti šablono pavadinimą.', 'danger')
                return redirect(url_for('template_management.edit_template', template_name=template_name))
            
            # Gauname parametrų reikšmes
            parameters = {
                'epochs': int(request.form.get('epochs', 50)),
                'batch_size': int(request.form.get('batch_size', 32)),
                'learning_rate': float(request.form.get('learning_rate', 0.001)),
                'dropout': float(request.form.get('dropout', 0.2)),
                'layers': int(request.form.get('layers', 2)),
                'neurons': int(request.form.get('neurons', 64))
            }
            
            # Pridedame modelio tipo specifinius parametrus
            if 'specific_params' in request.form:
                parameters['specific'] = json.loads(request.form.get('specific_params', '{}'))
            
            # Sukuriame šablono duomenis
            template_data = {
                'type': template_type,
                'category': template_category,
                'description': template_description,
                'parameters': parameters,
                'created_at': template.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Jei pavadinimas pasikeitė, ištriname seną šabloną ir sukuriame naują
            if new_template_name != template_name:
                service.delete_model_template(template_name)
                success = service.save_model_template(new_template_name, template_data)
            else:
                # Išsaugome šabloną
                success = service.save_model_template(template_name, template_data)
            
            if success:
                flash(f'Šablonas "{new_template_name}" sėkmingai atnaujintas.', 'success')
                return redirect(url_for('template_management.index'))
            else:
                flash('Klaida išsaugant šabloną.', 'danger')
                
        except Exception as e:
            logging.error(f"Klaida redaguojant šabloną: {str(e)}")
            flash(f'Klaida redaguojant šabloną: {str(e)}', 'danger')
    
    # Grąžiname šablono redagavimo formą
    return render_template(
        'training/edit_template.html',
        template_name=template_name,
        template=template
    )

@template_management.route('/delete/<template_name>', methods=['POST'])
def delete_template(template_name):
    """
    Šablono ištrynimas
    """
    # Inicializuojame ModelService
    service = ModelService()
    
    # Ištriname šabloną
    success = service.delete_model_template(template_name)
    
    if success:
        flash(f'Šablonas "{template_name}" sėkmingai ištrintas.', 'success')
    else:
        flash(f'Klaida trinant šabloną "{template_name}".', 'danger')
    
    return redirect(url_for('template_management.index'))

@template_management.route('/api/list', methods=['GET'])
def api_list_templates():
    """
    API endpointas šablonų sąrašo gavimui
    """
    # Inicializuojame ModelService
    service = ModelService()
    
    # Gauname visus šablonus
    templates = service.get_model_templates()
    
    # Grąžiname šablonus JSON formatu
    return jsonify(templates)

@template_management.route('/api/get/<template_name>', methods=['GET'])
def api_get_template(template_name):
    """
    API endpointas šablono gavimui
    """
    # Inicializuojame ModelService
    service = ModelService()
    
    # Gauname visus šablonus
    templates = service.get_model_templates()
    
    # Tikriname, ar šablonas egzistuoja
    if template_name not in templates:
        return jsonify({'error': f'Šablonas "{template_name}" nerastas.'}), 404
    
    # Grąžiname šabloną JSON formatu
    return jsonify(templates[template_name])

@template_management.route('/api/save', methods=['POST'])
def api_save_template():
    """
    API endpointas šablono išsaugojimui
    """
    try:
        # Gauname duomenis iš užklausos
        data = request.json
        
        if not data or 'name' not in data or 'parameters' not in data:
            return jsonify({'success': False, 'message': 'Trūksta privalomų laukų (name, parameters)'}), 400
        
        # Išskiriame šablono pavadinimą ir duomenis
        template_name = data['name']
        template_data = {
            'type': data.get('type', 'lstm'),
            'category': data.get('category', 'Bendra'),
            'description': data.get('description', ''),
            'parameters': data['parameters'],
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Išsaugome šabloną
        service = ModelService()
        success = service.save_model_template(template_name, template_data)
        
        if success:
            return jsonify({'success': True, 'message': f'Šablonas "{template_name}" sėkmingai išsaugotas.'})
        else:
            return jsonify({'success': False, 'message': 'Klaida išsaugant šabloną.'}), 500
        
    except Exception as e:
        logging.error(f"Klaida išsaugant šabloną per API: {str(e)}")
        return jsonify({'success': False, 'message': f'Klaida: {str(e)}'}), 500

@template_management.route('/api/delete/<template_name>', methods=['DELETE'])
def api_delete_template(template_name):
    """
    API endpointas šablono ištrynimui
    """
    try:
        # Ištriname šabloną
        service = ModelService()
        success = service.delete_model_template(template_name)
        
        if success:
            return jsonify({'success': True, 'message': f'Šablonas "{template_name}" sėkmingai ištrintas.'})
        else:
            return jsonify({'success': False, 'message': f'Šablonas "{template_name}" nerastas.'}), 404
        
    except Exception as e:
        logging.error(f"Klaida trinant šabloną per API: {str(e)}")
        return jsonify({'success': False, 'message': f'Klaida: {str(e)}'}), 500

@template_management.route('/models')
def models():
    """
    Modelių valdymo puslapis
    """
    return render_template('training/models.html')