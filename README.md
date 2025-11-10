# AI Content Creation Studio

A modern web application powered by CrewAI multi-agent system for automated blog post creation and brand compliance review.

## Features

- 🤖 **Multi-Agent System**: Uses CrewAI with two specialized agents:
  - **Creative Writer**: Generates engaging, informative blog posts
  - **Brand Reviewer**: Ensures content adheres to brand guidelines
- 🎨 **Modern UI/UX**: Beautiful, responsive interface with real-time updates
- 🔄 **Real-time Status**: Live project tracking and workflow visualization
- 🔒 **Secure**: API keys are used per-request and not stored

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Backend Server

```bash
python app.py
```

The server will start on `http://localhost:5000`

### 3. Open the Frontend

Open `index.html` in your web browser, or serve it using a simple HTTP server:

```bash
# Using Python
python -m http.server 8000

# Or using Node.js
npx http-server
```

Then navigate to `http://localhost:8000` (or the port you chose).

## Usage

1. **Enter Your OpenAI API Key**: Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. **Fill in the Form**:
   - **Project Name** (optional): Give your project a name
   - **Blog Topic**: What should the blog post be about?
   - **Brand Guidelines**: Specify tone, style, target audience, and brand requirements
3. **Click "Generate Content"**: The agents will work together to create and review your content
4. **View Results**: Watch the workflow progress in real-time and see the final output

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/projects` - Get all projects
- `POST /api/projects` - Create a new project
- `GET /api/projects/<id>` - Get a specific project
- `PUT /api/projects/<id>` - Update a project

## Project Structure

```
.
├── app.py              # Flask backend API
├── models.py           # Original CrewAI agent code (reference)
├── index.html          # Frontend UI
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Notes

- The API key is required for each request but is not stored on the server
- Projects are stored in memory (for production, use a database)
- The system uses GPT-4o-mini for cost-effective, fast processing
- Content generation typically takes 30-60 seconds

## Troubleshooting

**Backend won't start:**
- Make sure port 5000 is not in use
- Check that all dependencies are installed

**Frontend can't connect:**
- Ensure the backend is running on `http://localhost:5000`
- Check browser console for CORS errors

**Content generation fails:**
- Verify your OpenAI API key is valid
- Check that you have sufficient API credits
- Review the error message in the project details

## License

This project is created for hackathon purposes.

