from flask import Blueprint, request, jsonify
from database import db, Report, User, ReportHistory
from datetime import datetime

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/api/reports', methods=['GET'])
def get_reports():
    status = request.args.get('status')
    waste_type = request.args.get('waste_type')
    danger_level = request.args.get('danger_level')
    
    query = Report.select()
    
    if status:
        query = query.where(Report.status == status)
    if waste_type:
        query = query.where(Report.waste_type == waste_type)
    if danger_level:
        query = query.where(Report.danger_level == danger_level)
    
    reports = []
    for report in query.order_by(Report.created_at.desc()):
        reports.append({
            'id': report.id,
            'user_id': report.user.telegram_id,
            'username': report.user.username,
            'photo_path': report.photo_path,
            'latitude': report.latitude,
            'longitude': report.longitude,
            'address': report.address,
            'description': report.description,
            'waste_type': report.waste_type,
            'danger_level': report.danger_level,
            'status': report.status,
            'created_at': report.created_at.isoformat(),
            'updated_at': report.updated_at.isoformat()
        })
    
    return jsonify(reports)

@reports_bp.route('/api/reports/<int:report_id>', methods=['GET'])
def get_report(report_id):
    try:
        report = Report.get_by_id(report_id)
        
        history = []
        for h in report.history.order_by(ReportHistory.created_at.desc()):
            history.append({
                'old_status': h.old_status,
                'new_status': h.new_status,
                'changed_by': h.changed_by,
                'comment': h.comment,
                'created_at': h.created_at.isoformat()
            })
        
        return jsonify({
            'id': report.id,
            'user_id': report.user.telegram_id,
            'username': report.user.username,
            'photo_path': report.photo_path,
            'latitude': report.latitude,
            'longitude': report.longitude,
            'address': report.address,
            'description': report.description,
            'waste_type': report.waste_type,
            'danger_level': report.danger_level,
            'status': report.status,
            'created_at': report.created_at.isoformat(),
            'updated_at': report.updated_at.isoformat(),
            'history': history
        })
    except:
        return jsonify({'error': 'Report not found'}), 404

@reports_bp.route('/api/reports', methods=['POST'])
def create_report():
    data = request.json
    
    try:
        user = User.get(User.telegram_id == data['user_id'])
    except:
        user = User.create(
            telegram_id=data['user_id'],
            username=data.get('username'),
            first_name=data.get('first_name')
        )
    
    report = Report.create(
        user=user,
        photo_path=data['photo_path'],
        latitude=data['latitude'],
        longitude=data['longitude'],
        address=data.get('address'),
        description=data['description'],
        waste_type=data['waste_type'],
        danger_level=data['danger_level']
    )
    
    user.reports_count += 1
    user.rating += 10
    user.save()
    
    return jsonify({
        'id': report.id,
        'status': 'created'
    }), 201

@reports_bp.route('/api/reports/<int:report_id>', methods=['PUT'])
def update_report(report_id):
    data = request.json
    
    try:
        report = Report.get_by_id(report_id)
        old_status = report.status
        
        report.status = data['status']
        report.updated_at = datetime.now()
        report.save()
        
        ReportHistory.create(
            report=report,
            old_status=old_status,
            new_status=data['status'],
            changed_by=data['changed_by'],
            comment=data.get('comment')
        )
        
        return jsonify({'status': 'updated'})
    except:
        return jsonify({'error': 'Report not found'}), 404

@reports_bp.route('/api/reports/<int:report_id>', methods=['DELETE'])
def delete_report(report_id):
    try:
        report = Report.get_by_id(report_id)
        report.delete_instance()
        return jsonify({'status': 'deleted'})
    except:
        return jsonify({'error': 'Report not found'}), 404
