from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from marshmallow import Schema, fields, ValidationError, validate
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///students.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Models
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    age = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Schemas
class StudentSchema(Schema):
    id = fields.Int(dump_only=True)
    first_name = fields.Str(required=True, validate=validate.Length(min=1))
    last_name = fields.Str(allow_none=True)
    email = fields.Email(required=True)
    age = fields.Int(required=False, allow_none=True)
    created_at = fields.DateTime(dump_only=True)

student_schema = StudentSchema()
students_schema = StudentSchema(many=True)

# Routes
@app.route('/api/v1/students/', methods=['GET'])
def list_students():
    students = Student.query.all()
    return jsonify(students_schema.dump(students))

@app.route('/api/v1/students/', methods=['POST'])
def create_student():
    json_data = request.get_json() or {}
    try:
        data = student_schema.load(json_data)
    except ValidationError as e:
        return jsonify({'errors': e.messages}), 400
    if Student.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    s = Student(**data)
    db.session.add(s)
    db.session.commit()
    return student_schema.jsonify(s), 201

@app.route('/api/v1/students/<int:id>/', methods=['GET'])
def get_student(id):
    s = Student.query.get_or_404(id)
    return student_schema.jsonify(s)

@app.route('/api/v1/students/<int:id>/', methods=['PUT','PATCH'])
def update_student(id):
    s = Student.query.get_or_404(id)
    json_data = request.get_json() or {}
    try:
        data = student_schema.load(json_data, partial=('PATCH'==request.method))
    except ValidationError as e:
        return jsonify({'errors': e.messages}), 400
    for k, v in data.items():
        setattr(s, k, v)
    db.session.commit()
    return student_schema.jsonify(s)

@app.route('/api/v1/students/<int:id>/', methods=['DELETE'])
def delete_student(id):
    s = Student.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)