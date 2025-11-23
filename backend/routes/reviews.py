from flask import Blueprint, jsonify, request
from database import Review, User, db

reviews_bp = Blueprint('reviews', __name__)


@reviews_bp.route('/api/reviews', methods=['GET'])
def get_reviews():
    db.connect(reuse_if_open=True)
    reviews = Review.select().where(Review.is_approved == True).order_by(Review.created_at.desc())

    reviews_list = []
    for review in reviews:
        reviews_list.append({
            'id': review.id,
            'user_id': review.user.telegram_id,
            'username': review.user.username,
            'first_name': review.user.first_name,
            'text': review.text,
            'rating': review.rating,
            'created_at': review.created_at.isoformat()
        })

    db.close()
    return jsonify(reviews_list)


@reviews_bp.route('/api/reviews', methods=['POST'])
def create_review():
    data = request.json

    db.connect(reuse_if_open=True)
    try:
        user = User.get(User.telegram_id == data['user_id'])
    except:
        user = User.create(
            telegram_id=data['user_id'],
            username=data.get('username'),
            first_name=data.get('first_name')
        )

    review = Review.create(
        user=user,
        text=data['text'],
        rating=data.get('rating', 5)
    )

    db.close()
    return jsonify({'id': review.id, 'status': 'created'}), 201


@reviews_bp.route('/api/reviews/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    db.connect(reuse_if_open=True)
    review = Review.get_by_id(review_id)
    review.delete_instance()
    db.close()
    return jsonify({'status': 'deleted'})