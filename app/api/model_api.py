# Pridėkite šiuos maršrutus prie esamo API

@model_api.route('/api/models', methods=['GET'])
def get_models():
    """
    API endpointas modelių sąrašui gauti
    """
    # Sukuriame modelių paslaugos klasės objektą
    model_service = ModelService()
    
    # Gauname filtravimo parametrus iš URL
    filter_type = request.args.get('type', None)
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    limit = request.args.get('limit', None)
    
    try:
        # Gauname visų modelių sąrašą
        models = model_service.get_all_models(
            filter_type=filter_type,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Pritaikome limitą, jei nurodytas
        if limit and limit.isdigit():
            models = models[:int(limit)]
        
        return jsonify({
            'success': True,
            'models': models,
            'count': len(models)
        })
    
    except Exception as e:
        logger.error(f"Klaida gaunant modelių sąrašą: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Klaida: {str(e)}'
        }), 500

@model_api.route('/api/metrics/export/<training_id>', methods=['GET'])
def export_metrics(training_id):
    """
    API endpointas metrikų eksportavimui CSV formatu
    
    Args:
        training_id (str): Treniravimo sesijos ID
    """
    try:
        # Sukuriame modelių paslaugos klasės objektą
        model_service = ModelService()
        
        # Gauname modelio metrikas
        metrics = model_service.load_model_metrics(training_id)
        
        if not metrics:
            return jsonify({
                'success': False,
                'message': 'Metrikos nerastos'
            }), 404
        
        # Konvertuojame metrikas į tinkamą formatą
        metrics_list = []
        for epoch, data in metrics.items():
            if isinstance(data, dict):
                data['epoch'] = int(epoch)
                metrics_list.append(data)
        
        # Rūšiuojame pagal epochą
        metrics_list.sort(key=lambda x: x.get('epoch', 0))
        
        # Kuriame CSV turinį
        import io
        import csv
        
        output = io.StringIO()
        fieldnames = ['epoch', 'loss', 'val_loss', 'accuracy', 'val_accuracy', 'timestamp']
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for metric in metrics_list:
            # Išrenkame tik reikalingus laukus
            row = {field: metric.get(field, '') for field in fieldnames}
            writer.writerow(row)
        
        # Grąžiname CSV
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=metrics_{training_id}.csv'
        response.headers['Content-Type'] = 'text/csv'
        
        return response
    
    except Exception as e:
        logger.error(f"Klaida eksportuojant metrikas: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Klaida: {str(e)}'
        }), 500