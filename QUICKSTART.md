
# WemaBank Chatbot - Quick Reference

## Setup Steps (In Order)

1. Install dependencies:
   pip install -r requirements.txt
   playwright install chromium

2. Run crawler:
   python enhanced_crawler.py
   (Creates: wema_enhanced.json)

3. Create vector index:
   python create_faiss_index.py
   (Creates: wema_index/ folder)

4. Start web server:
   python app.py
   (Access: http://localhost:5000)

## File Checklist

Required for web chatbot:
☐ templates/index.html
☐ app.py
☐ wema_enhanced.json (or similar data file)
☐ wema_index/ (folder with index.faiss and index.pkl)

## Common Commands

# Check if everything is ready
python check_index.py

# Test a single query (without web interface)
python query.py

# Run CLI chatbot (alternative to web)
python chatbot.py

## Port Access (Codespaces)

1. Click "PORTS" tab in VS Code
2. Find port 5000
3. Click globe icon to open in browser
