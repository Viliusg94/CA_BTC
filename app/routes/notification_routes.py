# Pranešimų centro maršrutai - atsakingi už pranešimų rodymo ir valdymo puslapius
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
import logging

from app.services.notification_service import NotificationService
from app.models.notification import NotificationType, NotificationStatus

# Konfigūruojame logerį
logger = logging.getLogger(__name__)

# Sukuriame Blueprint
notification_routes = Blueprint('notifications', __name__, url_prefix='/notifications')

# Inicializuojame pranešimų servisą
notification_service = NotificationService()

@notification_routes.route('/')
def notification_center():
    """Rodo pranešimų centro puslapį"""
    try:
        # Gauname visus pranešimus (arba filtruojame pagal tipą)
        notification_type = request.args.get('type')
        
        if notification_type:
            try:
                type_enum = NotificationType(notification_type)
                notifications = [n for n in notification_service.get_all_notifications() if n.type == type_enum]
            except ValueError:
                notifications = notification_service.get_all_notifications()
        else:
            notifications = notification_service.get_all_notifications()
        
        # Rūšiuojame pagal laiką (naujausi viršuje)
        notifications.sort(key=lambda x: x.created_at, reverse=True)
        
        # Pažymime visus pranešimus kaip perskaitytus
        notification_service.mark_all_as_read()
        
        return render_template(
            'notifications/notification_center.html',
            notifications=notifications,
            unread_count=0,
            title="Pranešimų centras"
        )
    except Exception as e:
        logger.error(f"Klaida atidarant pranešimų centrą: {e}")
        flash(f"Klaida atidarant pranešimų centrą: {str(e)}", "danger")
        return redirect(url_for('index'))

@notification_routes.route('/<notification_id>/mark-read', methods=['POST'])
def mark_notification_read(notification_id):
    """Pažymi pranešimą kaip perskaitytą"""
    try:
        notification = notification_service.mark_as_read(notification_id)
        
        if notification:
            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Pranešimas nerastas'}), 404
    
    except Exception as e:
        logger.error(f"Klaida žymint pranešimą kaip perskaitytą: {e}")
        return jsonify({'error': str(e)}), 500

@notification_routes.route('/mark-all-read', methods=['POST'])
def mark_all_read():
    """Pažymi visus pranešimus kaip perskaitytus"""
    try:
        count = notification_service.mark_all_as_read()
        return jsonify({'success': True, 'count': count}), 200
    
    except Exception as e:
        logger.error(f"Klaida žymint visus pranešimus kaip perskaitytus: {e}")
        return jsonify({'error': str(e)}), 500

@notification_routes.route('/<notification_id>/delete', methods=['POST'])
def delete_notification(notification_id):
    """Ištrina pranešimą"""
    try:
        success = notification_service.delete_notification(notification_id)
        
        if success:
            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Pranešimas nerastas'}), 404
    
    except Exception as e:
        logger.error(f"Klaida trinant pranešimą: {e}")
        return jsonify({'error': str(e)}), 500

@notification_routes.route('/delete-all', methods=['POST'])
def delete_all_notifications():
    """Ištrina visus pranešimus"""
    try:
        # Gauname visus pranešimus
        notifications = notification_service.get_all_notifications()
        
        # Ištriname kiekvieną
        for notification in notifications:
            notification_service.delete_notification(notification.id)
        
        return jsonify({'success': True, 'count': len(notifications)}), 200
    
    except Exception as e:
        logger.error(f"Klaida trinant visus pranešimus: {e}")
        return jsonify({'error': str(e)}), 500

# API maršrutai

@notification_routes.route('/api/unread-count')
def api_unread_count():
    """Grąžina neperskaitytų pranešimų skaičių"""
    try:
        count = notification_service.get_unread_count()
        return jsonify({'count': count})
    
    except Exception as e:
        logger.error(f"Klaida gaunant neperskaitytų pranešimų skaičių: {e}")
        return jsonify({'error': str(e)}), 500

@notification_routes.route('/api/recent')
def api_recent_notifications():
    """Grąžina naujausius pranešimus"""
    try:
        # Gauname visus pranešimus
        notifications = notification_service.get_all_notifications()
        
        # Rūšiuojame pagal laiką (naujausi viršuje)
        notifications.sort(key=lambda x: x.created_at, reverse=True)
        
        # Grąžiname tik pirmus 5
        recent = [notification.to_dict() for notification in notifications[:5]]
        
        return jsonify(recent)
    
    except Exception as e:
        logger.error(f"Klaida gaunant naujausius pranešimus: {e}")
        return jsonify({'error': str(e)}), 500

@notification_routes.route('/api/process/<target_id>')
def api_process_status(target_id):
    """Grąžina proceso progresą"""
    try:
        # Ieškome proceso pranešimo
        for notification in notification_service.get_all_notifications():
            if notification.target_id == target_id and notification.type == NotificationType.PROCESS:
                return jsonify({
                    'id': notification.id,
                    'target_id': notification.target_id,
                    'progress': notification.progress,
                    'message': notification.message,
                    'created_at': notification.created_at.isoformat()
                })
        
        return jsonify({'error': 'Proceso informacija nerasta'}), 404
    
    except Exception as e:
        logger.error(f"Klaida gaunant proceso būseną: {e}")
        return jsonify({'error': str(e)}), 500