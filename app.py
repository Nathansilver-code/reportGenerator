
from flask import Flask, url_for
from extensions import db, login_manager
from config import Config
from flask_migrate import Migrate




def create_app():
    """Application factory: creates and configures the Flask app."""
    app = Flask(__name__)
    app.config.from_object(Config)

    
    db.init_app(app)
    login_manager.init_app(app)
    migrate = Migrate(app, db)
    
    login_manager.login_view = "auth.login"          
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    
    from routes.auth import auth_bp
    from routes.marks import marks_bp
    from routes.reports import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(marks_bp)
    app.register_blueprint(reports_bp)

    
    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)          



