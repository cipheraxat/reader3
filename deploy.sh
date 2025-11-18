#!/bin/bash

# Quick deployment script for reader3
# This script helps you deploy to your chosen platform

set -e

echo "🚀 Reader3 Cloud Deployment Helper"
echo "=================================="
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "📦 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit - Reader3 EPUB Reader"
fi

echo "Choose your deployment platform:"
echo ""
echo "1) Render.com (Recommended - Easiest)"
echo "2) Railway.app"
echo "3) Fly.io"
echo "4) Heroku"
echo "5) Manual - Just show me the steps"
echo ""
read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "📘 Render.com Deployment"
        echo "======================="
        echo ""
        echo "Steps:"
        echo "1. Create a GitHub repository (if you haven't already)"
        echo "2. Push this code to GitHub:"
        echo ""
        echo "   git remote add origin https://github.com/YOUR_USERNAME/reader3.git"
        echo "   git push -u origin master"
        echo ""
        echo "3. Go to https://render.com and sign up/login"
        echo "4. Click 'New +' → 'Web Service'"
        echo "5. Connect your GitHub repository"
        echo "6. Render will auto-detect render.yaml"
        echo "7. Click 'Create Web Service'"
        echo ""
        echo "✅ Your app will be live at: https://reader3-XXXX.onrender.com"
        echo ""
        read -p "Press Enter to open Render.com..." 
        xdg-open https://render.com 2>/dev/null || open https://render.com 2>/dev/null || echo "Visit: https://render.com"
        ;;
        
    2)
        echo ""
        echo "🚂 Railway.app Deployment"
        echo "========================"
        echo ""
        echo "Steps:"
        echo "1. Push code to GitHub (if not done)"
        echo "2. Go to https://railway.app"
        echo "3. Login with GitHub"
        echo "4. Click 'New Project' → 'Deploy from GitHub repo'"
        echo "5. Select your repository"
        echo "6. Click 'Deploy'"
        echo "7. Generate domain in Settings"
        echo ""
        echo "✅ Your app will be live at: https://reader3-production-XXXX.up.railway.app"
        echo ""
        read -p "Press Enter to open Railway.app..." 
        xdg-open https://railway.app 2>/dev/null || open https://railway.app 2>/dev/null || echo "Visit: https://railway.app"
        ;;
        
    3)
        echo ""
        echo "✈️  Fly.io Deployment"
        echo "===================="
        echo ""
        if ! command -v fly &> /dev/null; then
            echo "Installing Fly CLI..."
            curl -L https://fly.io/install.sh | sh
            export PATH="$HOME/.fly/bin:$PATH"
        fi
        echo "Deploying to Fly.io..."
        fly auth login
        fly launch --name reader3-$(whoami) --region ord --no-deploy
        
        # Update fly.toml if needed
        echo "Deploying..."
        fly deploy
        
        echo ""
        echo "✅ Your app is live!"
        fly open
        ;;
        
    4)
        echo ""
        echo "🟣 Heroku Deployment"
        echo "==================="
        echo ""
        if ! command -v heroku &> /dev/null; then
            echo "Please install Heroku CLI first:"
            echo "curl https://cli-assets.heroku.com/install.sh | sh"
            exit 1
        fi
        
        echo "Logging in to Heroku..."
        heroku login
        
        echo "Creating app..."
        APP_NAME="reader3-$(whoami)-$(date +%s)"
        heroku create $APP_NAME
        
        echo "Deploying..."
        git push heroku master
        
        echo ""
        echo "✅ Your app is live!"
        heroku open
        ;;
        
    5)
        echo ""
        echo "📋 Manual Deployment Steps"
        echo "=========================="
        echo ""
        echo "All configuration files are ready:"
        echo "  ✓ render.yaml - for Render.com"
        echo "  ✓ Railway.toml - for Railway.app"
        echo "  ✓ Dockerfile - for containerized deployment"
        echo "  ✓ Procfile - for Heroku"
        echo "  ✓ requirements.txt - Python dependencies"
        echo ""
        echo "See DEPLOYMENT.md for detailed instructions"
        echo ""
        cat DEPLOYMENT.md
        ;;
        
    *)
        echo "Invalid choice. Please run again and select 1-5."
        exit 1
        ;;
esac

echo ""
echo "📚 Don't forget to add your EPUB books!"
echo "   Run: uv run reader3.py your-book.epub"
echo ""
echo "🎉 Happy reading!"
