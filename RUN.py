#!/usr/bin/env python3
"""
Simple Streamlit Launcher
Runs Streamlit locally with options for public sharing
"""
import subprocess
import sys
import os
import webbrowser
import time
from pathlib import Path

# Config
APP_FILE = "app.py"
PORT = "8501"

def find_app_file():
    """Find the Streamlit app file"""
    possible_files = ["app.py", "App.py", "main.py", "streamlit_app.py"]
    
    for file in possible_files:
        if os.path.exists(file):
            return file
    return None

def install_streamlit():
    """Install Streamlit if not available"""
    try:
        import streamlit
        print("✅ Streamlit already installed")
        return True
    except ImportError:
        print("📦 Installing Streamlit...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
            print("✅ Streamlit installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install Streamlit")
            return False

def main():
    print("🐉 Dragon Boat Portal Launcher")
    print("=" * 40)
    
    # Find app file
    app_file = find_app_file()
    if not app_file:
        print(f"❌ App file not found! Looking for: {', '.join(['app.py', 'App.py', 'main.py'])}")
        return
    
    print(f"📁 Found app file: {app_file}")
    
    # Install Streamlit if needed
    if not install_streamlit():
        return
    
    # Show options
    print("\n🚀 Choose how to run your app:")
    print("1. Local only (http://localhost:8501)")
    print("2. Local + network access (accessible on your network)")
    print("3. Instructions for Streamlit Cloud (free public hosting)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        # Local only
        print(f"\n🚀 Starting Streamlit locally...")
        print(f"📱 App will open at: http://localhost:{PORT}")
        
        cmd = [
            sys.executable, "-m", "streamlit", "run", app_file,
            "--server.port", PORT
        ]
        
        subprocess.run(cmd)
    
    elif choice == "2":
        # Network accessible
        print(f"\n🌐 Starting Streamlit with network access...")
        print(f"📱 Local access: http://localhost:{PORT}")
        print(f"🔗 Network access: http://[YOUR_IP]:{PORT}")
        
        # Get local IP
        try:
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            print(f"🔗 Try: http://{local_ip}:{PORT}")
        except:
            pass
        
        cmd = [
            sys.executable, "-m", "streamlit", "run", app_file,
            "--server.port", PORT,
            "--server.address", "0.0.0.0"
        ]
        
        subprocess.run(cmd)
    
    elif choice == "3":
        # Streamlit Cloud instructions
        print("\n☁️ Streamlit Cloud Setup (FREE Public Hosting):")
        print("=" * 50)
        print("1. Create a GitHub account if you don't have one")
        print("2. Create a new repository and upload your files:")
        print(f"   - {app_file}")
        print("   - requirements.txt (create if missing)")
        print("3. Go to https://share.streamlit.io/")
        print("4. Connect your GitHub account")
        print("5. Deploy your repository")
        print("\n📝 Need a requirements.txt? Here's a basic one:")
        print("-" * 30)
        print("streamlit>=1.28.0")
        print("pandas>=1.5.0")
        print("-" * 30)
        
        create_req = input("\n📝 Create requirements.txt automatically? (y/N): ")
        if create_req.lower() == 'y':
            with open("requirements.txt", "w") as f:
                f.write("streamlit>=1.28.0\npandas>=1.5.0\n")
            print("✅ Created requirements.txt")
        
        # Still run locally
        run_local = input("🚀 Run locally while you set up cloud? (y/N): ")
        if run_local.lower() == 'y':
            cmd = [sys.executable, "-m", "streamlit", "run", app_file, "--server.port", PORT]
            subprocess.run(cmd)
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        input("Press Enter to exit...")