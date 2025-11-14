#!/usr/bin/env bash
# Render build script - runs during deployment

echo "Starting build process..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Initialize database
echo "🗄️  Initializing database..."
python init_db.py

echo "✅ Build complete!"
