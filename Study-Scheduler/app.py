from flask import Flask
from flask_cors import CORS
from routes.intake import intake_bp
from routes.schedule import schedule_bp
from routes.reminders import reminders_bp
from routes.feedback import feedback_bp
from routes.coach import coach_bp

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173"])

app.register_blueprint(intake_bp)
app.register_blueprint(schedule_bp)
app.register_blueprint(reminders_bp)
app.register_blueprint(feedback_bp)
app.register_blueprint(coach_bp)

if __name__ == "__main__":
    app.run(debug=True, port=5000)