<<<<<<< HEAD
from app import create_app, db

app = create_app()
with app.app_context():
    db.drop_all()
    db.create_all()
    print("Database reset successfully!")
=======
from app import create_app, db

app = create_app()
with app.app_context():
    db.drop_all()
    db.create_all()
    print("Database reset successfully!")
>>>>>>> 552e9e81cb63452b0e8f79c5c9e347d7571dd5f1
