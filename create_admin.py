import sys
from database import initialize_db, Admin, db

def create_admin(telegram_id, username=None):
    initialize_db()
    
    db.connect()
    
    try:
        admin = Admin.get(Admin.telegram_id == telegram_id)
        print(f"Администратор с ID {telegram_id} уже существует")
    except Admin.DoesNotExist:
        admin = Admin.create(
            telegram_id=telegram_id,
            username=username,
            is_active=True
        )
        print(f"✅ Администратор создан: ID {telegram_id}, username: @{username or 'неизвестно'}")
    
    db.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование: python create_admin.py <telegram_id> [username]")
        sys.exit(1)
    
    telegram_id = int(sys.argv[1])
    username = sys.argv[2] if len(sys.argv) > 2 else None
    
    create_admin(telegram_id, username)
