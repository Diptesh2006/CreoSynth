# Quick Start Guide

## Step 1: Install Python Dependencies

Open your terminal/command prompt in the project directory and run:

```bash
pip install -r requirements.txt
```

**Note**: If you have multiple Python versions, you might need to use `pip3` instead of `pip`.

## Step 2: Start the Backend Server

### Option A: Using the startup script (Windows)
Double-click `start.bat` or run in command prompt:
```bash
start.bat
```

### Option B: Using the startup script (Mac/Linux)
```bash
chmod +x start.sh
./start.sh
```

### Option C: Manual start
```bash
python app.py
```

You should see output like:
```
 * Running on http://0.0.0.0:5000
```

**Keep this terminal window open** - the server needs to keep running!

## Step 3: Open the Frontend

### Option A: Direct file open (Simplest)
1. Navigate to the project folder in File Explorer
2. Double-click `index.html`
3. It will open in your default browser

### Option B: Using Python HTTP server (Recommended)
Open a **new** terminal window (keep the backend running) and run:

```bash
# Python 3
python -m http.server 8000

# Or Python 2
python -m SimpleHTTPServer 8000
```

Then open your browser and go to: `http://localhost:8000`

### Option C: Using Node.js (if you have it)
```bash
npx http-server -p 8000
```

Then open: `http://localhost:8000`

## Step 4: Use the Application

1. **Enter your OpenAI API Key**: 
   - Get it from https://platform.openai.com/api-keys
   - Paste it in the "OpenAI API Key" field

2. **Fill in the form**:
   - **Project Name** (optional): e.g., "Q4 Blog Post"
   - **Blog Topic**: e.g., "The Future of Agentic AI"
   - **Brand Guidelines**: e.g., "Tone must be optimistic, inspiring, and avoid complex technical jargon"

3. **Click "Generate Content"**

4. **Watch the workflow**: The agents will process your request and you'll see real-time updates!

## Troubleshooting

### "Module not found" error
- Make sure you installed dependencies: `pip install -r requirements.txt`
- Try: `pip3 install -r requirements.txt` if you have multiple Python versions

### "Port 5000 already in use"
- Another application is using port 5000
- Close that application or change the port in `app.py` (line 262): `app.run(debug=True, port=5001, ...)`

### Frontend can't connect to backend
- Make sure the backend is running (Step 2)
- Check that you see "Running on http://0.0.0.0:5000" in the backend terminal
- Try opening `http://localhost:5000/api/health` in your browser - it should show `{"status":"healthy"}`

### CORS errors in browser console
- Make sure `flask-cors` is installed: `pip install flask-cors`
- Restart the backend server

### API Key errors
- Make sure your OpenAI API key is valid
- Check you have credits in your OpenAI account
- The key should start with `sk-`

## What's Running?

- **Backend**: Flask server on `http://localhost:5000` (handles API requests)
- **Frontend**: HTML file in your browser (the user interface)

Both need to be running for the app to work!

