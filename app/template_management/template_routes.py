from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database import db
from database.models.template_models import Template  # Įsitikinkite, kad importuojate teisingą modelį

template_management = Blueprint('template_management', __name__, url_prefix='/template_management')

@template_management.route('/')
def index():
    """Šablonų pagrindinis puslapis"""
    return render_template('template_management/index.html')

@template_management.route('/templates')
def list_templates():
    """Šablonų sąrašo puslapis"""
    templates = db.query(Template).all()
    return render_template('template_management/list_templates.html', templates=templates)

@template_management.route('/templates/<template_name>')
def edit_template(template_name):
    """Redaguoti konkretų šabloną"""
    template = db.query(Template).filter_by(name=template_name).first()
    if not template:
        flash(f'Šablonas "{template_name}" nerastas', 'danger')
        return redirect(url_for('template_management.list_templates'))
    
    return render_template('template_management/edit_template.html', template=template)

@template_management.route('/api/templates')
def get_templates_json():
    """API endpoint JSON šablonų sąrašui gauti"""
    templates = db.query(Template).all()
    
    # Konvertuojame šablonus į JSON formatą
    templates_json = []
    for template in templates:
        templates_json.append({
            'id': template.id,
            'name': template.name,
            'type': template.type,
            'description': template.description,
            'created_at': template.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify(templates_json)