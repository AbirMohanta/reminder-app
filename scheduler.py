from app import app, scheduler
from flask_sqlalchemy import SQLAlchemy

if __name__ == '__main__':
    with app.app_context():
        scheduler.start()
        try:
            scheduler.run()
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown() 