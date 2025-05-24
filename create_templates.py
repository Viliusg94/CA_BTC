import os

def create_templates():
    """Create missing template files"""
    
    templates_dir = 'app/templates'
    os.makedirs(templates_dir, exist_ok=True)
    
    # Create minimal models.html
    models_html = '''{% extends "base.html" %}

{% block title %}Models Management{% endblock %}

{% block content %}
<div class="container-fluid">
    <h1 class="mb-4">
        <i class="fas fa-brain text-primary"></i> AI Models Management
    </h1>
    
    <div class="row">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">Available Models</h5>
                </div>
                <div class="card-body">
                    {% if model_files %}
                        <div class="row">
                            {% for model_type, filename in model_files.items() %}
                            <div class="col-md-4 mb-3">
                                <div class="card">
                                    <div class="card-body">
                                        <h6 class="card-title">{{ model_type }}</h6>
                                        <p class="card-text">{{ filename }}</p>
                                        <button class="btn btn-primary btn-sm">View Details</button>
                                    </div>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    {% else %}
                        <p class="text-muted">No model files found. Train some models first.</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''
    
    # Create error.html
    error_html = '''{% extends "base.html" %}

{% block title %}Error{% endblock %}

{% block content %}
<div class="container">
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="card">
                <div class="card-body text-center">
                    <i class="fas fa-exclamation-triangle fa-3x text-warning mb-3"></i>
                    <h4>Oops! Something went wrong</h4>
                    <p class="text-muted">{{ error if error else "An unexpected error occurred." }}</p>
                    <a href="/" class="btn btn-primary">Return Home</a>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''
    
    # Write template files
    with open(os.path.join(templates_dir, 'models.html'), 'w', encoding='utf-8') as f:
        f.write(models_html)
    
    with open(os.path.join(templates_dir, 'error.html'), 'w', encoding='utf-8') as f:
        f.write(error_html)
    
    print("✅ Created template files")
    print("  - app/templates/models.html")
    print("  - app/templates/error.html")

if __name__ == '__main__':
    create_templates()
