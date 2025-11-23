let currentReviewIndex = 0;
let reviews = [];

async function loadReviews() {
    try {
        const response = await fetch('/api/reviews');
        reviews = await response.json();
        displayReviews();
    } catch (error) {
        console.error('Ошибка загрузки отзывов:', error);
    }
}

function displayReviews() {
    const container = document.getElementById('reviewsContainer');

    if (reviews.length === 0) {
        container.innerHTML = '<div class="review-card active"><p style="text-align: center; color: #999;">Пока нет отзывов</p></div>';
        return;
    }

    container.innerHTML = reviews.map((review, index) => `
        <div class="review-card ${index === 0 ? 'active' : ''}">
            <div class="review-header">
                <div class="review-avatar">${(review.first_name || review.username || 'U')[0].toUpperCase()}</div>
                <div class="review-info">
                    <h4>@${review.username || 'Пользователь'}</h4>
                    <div class="review-date">${new Date(review.created_at).toLocaleDateString('ru-RU')}</div>
                </div>
            </div>
            <div class="review-text">${review.text}</div>
        </div>
    `).join('');

    updateCounter();
}

function showReview(index) {
    const cards = document.querySelectorAll('.review-card');
    cards.forEach((card, i) => {
        card.classList.toggle('active', i === index);
    });
    updateCounter();
}

function nextReview() {
    currentReviewIndex = (currentReviewIndex + 1) % reviews.length;
    showReview(currentReviewIndex);
}

function prevReview() {
    currentReviewIndex = (currentReviewIndex - 1 + reviews.length) % reviews.length;
    showReview(currentReviewIndex);
}

function updateCounter() {
    const counter = document.getElementById('reviewsCounter');
    if (reviews.length > 0) {
        counter.textContent = `${currentReviewIndex + 1} / ${reviews.length}`;
    }
}

document.getElementById('reviewNext')?.addEventListener('click', nextReview);
document.getElementById('reviewPrev')?.addEventListener('click', prevReview);

loadReviews();