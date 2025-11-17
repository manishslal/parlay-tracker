import pytest
from app import app

def test_app_exists():
    assert app is not None

def test_app_config():
    assert app.config['SECRET_KEY']
