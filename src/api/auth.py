from datetime import datetime
from datetime import timedelta
from datetime import timezone

import re

from flask import request
from flask import jsonify

from sqlalchemy import select

import jwt

from app_config import app
from app_config import db_session

from models.user import User

from utils.security import hash_password
from utils.security import verify_password


@app.route('/api/auth/sign-up', methods=['POST'])
def register():
    try:
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        
        # Check if all required fields are present
        if not name or not email or not password:
            return jsonify({'message': 'Missing required fields'}), 400
            
        # Validate email format
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_pattern, email):
            return jsonify({'message': 'Invalid email format'}), 400
            
        # Validate password strength (example: minimum 8 characters)
        if len(password) < 8:
            return jsonify({'message': 'Password must be at least 8 characters long'}), 400
        
        if len(name) <= 0:
            return jsonify({'message': 'Name must not be empty'}), 400
            
        # Check if user already exists
        stmt = select(User).where(User.email == email)
        existing_user = db_session.scalars(stmt).first()
        
        if existing_user:
            return jsonify({'message': 'Email already registered'}), 409
            
        # Create new user
        new_user = User(
            email=email,
            name=name,
            password_hash=hash_password(password),
            modification_user=email,  # Using email as the modification user for creation
            modification_timestamp=datetime.now(timezone.utc)
        )
        
        # Add and commit to database
        db_session.add(new_user)
        db_session.commit()
        
        # Generate JWT token for automatic login after registration
        token = jwt.encode({
            'user_id': new_user.user_id,
            'email': new_user.email,
            'exp': datetime.now(timezone.utc) + timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({
            'message': 'Registration successful',
            'token': token,
            'user': {
                'user_id': new_user.user_id,
                'email': new_user.email
            }
        }), 201
        
    except Exception as e:
        db_session.rollback()
        return jsonify({'message': f'Registration failed: {str(e)}'}), 500



@app.route('/api/auth/log-in', methods=['POST'])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    
    if not email or not password:
        return jsonify({'message': 'Missing credentials'}), 400
    
    try:
        # Query the user by email
        stmt = select(User).where(User.email == email)
        user = db_session.scalars(stmt).first()
        
        if not user:
            return jsonify({'message': 'User not found'}), 401
        
        # Verify password
        if verify_password(password, user.password_hash):
            # Generate token
            token = jwt.encode({
                'user_id': user.user_id,
                'email': user.email,
                'exp': datetime.now(timezone.utc) + timedelta(hours=24)
            }, app.config['SECRET_KEY'], algorithm="HS256")
            
            return jsonify({
                'token': token,
                'user': {
                    'user_id': user.user_id,
                    'email': user.email
                },
                'message': 'Login successful'
            })
        
        return jsonify({'message': 'Invalid password'}), 401
        
    except Exception as e:
        db_session.rollback()
        return jsonify({'message': f'Login failed: {str(e)}'}), 500
