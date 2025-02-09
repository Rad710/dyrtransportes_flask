from functools import wraps

from flask import request
from flask import jsonify

from sqlalchemy import select

from jwt import decode
from jwt import ExpiredSignatureError
from jwt import InvalidTokenError

from app_config import app
from app_config import db_session

from models.user import User

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            
            # Decode token
            data = decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            
            # Get user from database
            stmt = select(User).where(User.user_id == data['user_id'])
            current_user = db_session.scalars(stmt).first()
            
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
                
            # Add user to request context
            request.current_user = current_user
            
        except ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        except Exception as e:
            return jsonify({'message': f'Error: {str(e)}'}), 500
            
        return f(*args, **kwargs)
    return decorated
