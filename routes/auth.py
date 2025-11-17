from flask import Blueprint, jsonify, request, session
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# ==========================================================================
# Authentication Endpoints
# ==========================================================================

@auth_bp.route('/register', methods=['POST'])
@login_required
def register() -> object:
	"""Register a new user (admin only)"""
	if not current_user.is_authenticated:
		return jsonify({'error': 'Unauthorized'}), 401
	data = request.json
	username = data.get('username')
	email = data.get('email')
	password = data.get('password')
	if not username or not email or not password:
		return jsonify({'error': 'Missing required fields'}), 400
	if User.query.filter(db.func.lower(User.username) == username.lower()).first():
		return jsonify({'error': 'Username already exists'}), 400
	if User.query.filter(db.func.lower(User.email) == email.lower()).first():
		return jsonify({'error': 'Email already exists'}), 400
	try:
		user = User(username=username, email=email.lower())
		user.set_password(password)
		db.session.add(user)
		db.session.commit()
		return jsonify({'message': 'User created successfully', 'user': user.to_dict()}), 201
	except Exception as e:
		db.session.rollback()
		return jsonify({'error': 'Failed to create user'}), 500

@auth_bp.route('/login', methods=['POST'])
def login() -> object:
	"""Login with username/email and password (case-insensitive)"""
	data = request.json
	identifier = data.get('username') or data.get('email')
	password = data.get('password')
	if not identifier or not password:
		return jsonify({'error': 'Missing credentials'}), 400
	user = User.query.filter((db.func.lower(User.username) == identifier.lower()) | (db.func.lower(User.email) == identifier.lower())).first()
	if not user or not user.check_password(password):
		return jsonify({'error': 'Invalid credentials'}), 401
	if not user.is_active:
		return jsonify({'error': 'Account is disabled'}), 403
	session.permanent = True
	login_user(user, remember=True)
	response = jsonify({'message': 'Login successful', 'user': user.to_dict()})
	response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
	response.headers['Pragma'] = 'no-cache'
	response.headers['Expires'] = '0'
	return response, 200

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout() -> object:
	"""Logout current user"""
	logout_user()
	session.clear()
	response = jsonify({'message': 'Logout successful'})
	response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
	response.headers['Pragma'] = 'no-cache'
	response.headers['Expires'] = '0'
	response.set_cookie('session', '', expires=0, path='/')
	response.set_cookie('remember_token', '', expires=0, path='/')
	return response, 200

@auth_bp.route('/check', methods=['GET'])
def check_auth() -> object:
	"""Check if user is authenticated"""
	if current_user.is_authenticated:
		response = jsonify({'authenticated': True, 'user': current_user.to_dict()})
	else:
		response = jsonify({'authenticated': False})
	response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
	response.headers['Pragma'] = 'no-cache'
	response.headers['Expires'] = '0'
	return response, 200
