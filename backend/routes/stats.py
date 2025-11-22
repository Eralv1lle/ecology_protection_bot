from flask import Blueprint, jsonify
from database import Report, User
from peewee import fn

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/api/stats', methods=['GET'])
def get_stats():
    total_reports = Report.select().count()
    total_users = User.select().count()
    
    reports_by_status = {}
    for status in ['new', 'reviewing', 'in_progress', 'resolved', 'rejected']:
        count = Report.select().where(Report.status == status).count()
        reports_by_status[status] = count
    
    reports_by_type = {}
    types_query = Report.select(Report.waste_type, fn.COUNT(Report.id).alias('count')).group_by(Report.waste_type)
    for report in types_query:
        reports_by_type[report.waste_type] = report.count
    
    reports_by_danger = {}
    danger_query = Report.select(Report.danger_level, fn.COUNT(Report.id).alias('count')).group_by(Report.danger_level)
    for report in danger_query:
        reports_by_danger[report.danger_level] = report.count
    
    top_users = []
    for user in User.select().order_by(User.rating.desc()).limit(10):
        top_users.append({
            'telegram_id': user.telegram_id,
            'username': user.username,
            'reports_count': user.reports_count,
            'rating': user.rating
        })
    
    return jsonify({
        'total_reports': total_reports,
        'total_users': total_users,
        'reports_by_status': reports_by_status,
        'reports_by_type': reports_by_type,
        'reports_by_danger': reports_by_danger,
        'top_users': top_users
    })

@stats_bp.route('/api/user/<int:telegram_id>/stats', methods=['GET'])
def get_user_stats(telegram_id):
    try:
        user = User.get(User.telegram_id == telegram_id)
        
        reports_by_status = {}
        for status in ['new', 'reviewing', 'in_progress', 'resolved', 'rejected']:
            count = Report.select().where(
                (Report.user == user) & (Report.status == status)
            ).count()
            reports_by_status[status] = count
        
        rank_query = User.select(fn.COUNT(User.id).alias('rank')).where(User.rating > user.rating)
        rank = rank_query.scalar() + 1
        
        return jsonify({
            'telegram_id': user.telegram_id,
            'username': user.username,
            'reports_count': user.reports_count,
            'rating': user.rating,
            'rank': rank,
            'reports_by_status': reports_by_status
        })
    except:
        return jsonify({'error': 'User not found'}), 404
