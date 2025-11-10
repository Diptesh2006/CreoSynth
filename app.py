from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from langchain_openai import ChatOpenAI
from crewai import Agent, Task, Crew, Process
import uuid
from datetime import datetime
import traceback

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Store projects in memory (in production, use a database)
projects = {}

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    return jsonify({
        "success": True,
        "projects": list(projects.values())
    })

@app.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project"""
    try:
        data = request.json
        topic = data.get('topic', '').strip()
        guidelines = data.get('guidelines', '').strip()
        project_name = data.get('project_name', topic[:50] if topic else 'Untitled Project')
        
        if not topic:
            return jsonify({
                "success": False,
                "error": "Topic is required"
            }), 400
        
        if not guidelines:
            return jsonify({
                "success": False,
                "error": "Brand guidelines are required"
            }), 400
        
        # Check for API key
        api_key = data.get('api_key', '').strip()
        if not api_key:
            return jsonify({
                "success": False,
                "error": "OpenAI API key is required"
            }), 400
        
        # Create project
        project_id = str(uuid.uuid4())
        project = {
            "id": project_id,
            "project_name": project_name,
            "topic": topic,
            "guidelines": guidelines,
            "status": "pending",
            "writer_output": "",
            "reviewer_feedback": "",
            "final_output": "",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        projects[project_id] = project
        
        # Start processing (in production, use a task queue like Celery)
        # For now, we'll process synchronously and the frontend will poll
        import threading
        
        def process_in_background():
            try:
                projects[project_id].update({
                    "status": "processing",
                    "updated_at": datetime.now().isoformat()
                })
                
                result = process_crewai_project(project_id, topic, guidelines, api_key)
                projects[project_id].update({
                    "status": "completed",
                    "writer_output": result.get("writer_output", ""),
                    "reviewer_feedback": result.get("reviewer_feedback", ""),
                    "final_output": result.get("final_output", ""),
                    "updated_at": datetime.now().isoformat()
                })
            except Exception as e:
                projects[project_id].update({
                    "status": "error",
                    "error_message": str(e),
                    "updated_at": datetime.now().isoformat()
                })
        
        # Start processing in background thread
        thread = threading.Thread(target=process_in_background)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "project": projects[project_id]
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get a specific project"""
    if project_id not in projects:
        return jsonify({
            "success": False,
            "error": "Project not found"
        }), 404
    
    return jsonify({
        "success": True,
        "project": projects[project_id]
    })

@app.route('/api/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    """Update a project"""
    if project_id not in projects:
        return jsonify({
            "success": False,
            "error": "Project not found"
        }), 404
    
    data = request.json
    projects[project_id].update(data)
    projects[project_id]["updated_at"] = datetime.now().isoformat()
    
    return jsonify({
        "success": True,
        "project": projects[project_id]
    })

def process_crewai_project(project_id, topic, guidelines, api_key):
    """Process a project using CrewAI"""
    try:
        # Set API key
        os.environ["OPENAI_API_KEY"] = api_key
        
        # Setup the OpenAI LLM
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=4000
        )
        
        # Define Agents
        creative_writer = Agent(
            role='Creative Content Writer',
            goal='To write an engaging, informative, and human-like blog post on a given topic.',
            backstory=(
                "You are an expert content creator who specializes in "
                "technology and culture. You know how to break down complex "
                "topics into simple, engaging narratives that captivate an audience."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False,
        )
        
        brand_reviewer = Agent(
            role='Brand Compliance Reviewer',
            goal='To review a given piece of content and ensure it strictly adheres to brand guidelines.',
            backstory=(
                "You are the guardian of the brand's voice. Your job is to read "
                "content and check it for tone, style, and accuracy against the "
                "company's brand profile. You are meticulous and have a keen eye for detail."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False,
        )
        
        # Define Tasks
        write_task = Task(
            description=(
                f"Write a 300-word blog post about the topic: '{topic}'. "
                "The post must be engaging and easy to understand."
            ),
            expected_output='A formatted blog post (text) of around 300 words.',
            agent=creative_writer,
        )
        
        review_task = Task(
            description=(
                f"Review the blog post written by the Creative Writer. "
                f"Check it against the following Brand Guidelines: '{guidelines}'. "
                "Provide a detailed review with either 'APPROVED' or 'REJECTED' status and clear feedback."
            ),
            expected_output="A comprehensive review with 'APPROVED' or 'REJECTED' status and clear revision notes.",
            agent=brand_reviewer,
            context=[write_task],
        )
        
        # Create and Run the Crew
        my_crew = Crew(
            agents=[creative_writer, brand_reviewer],
            tasks=[write_task, review_task],
            process=Process.sequential,
            verbose=False
        )
        
        task_inputs = {
            'topic': topic,
            'guidelines': guidelines
        }
        
        result = my_crew.kickoff(inputs=task_inputs)
        
        # Extract outputs from tasks
        writer_output = ""
        reviewer_feedback = ""
        final_output = str(result)
        
        # Try to extract task outputs
        if hasattr(result, 'tasks_output'):
            for task_output in result.tasks_output:
                if 'Creative Content Writer' in str(task_output) or 'Writer' in str(task_output):
                    writer_output = str(task_output)
                elif 'Brand Compliance Reviewer' in str(task_output) or 'Reviewer' in str(task_output):
                    reviewer_feedback = str(task_output)
        
        # If we can't extract separately, use the final output
        if not writer_output and not reviewer_feedback:
            # Split the output intelligently
            parts = final_output.split("Review")
            if len(parts) > 1:
                writer_output = parts[0].strip()
                reviewer_feedback = "Review" + parts[1].strip()
            else:
                writer_output = final_output
                reviewer_feedback = "Review completed. See final output."
        
        return {
            "writer_output": writer_output,
            "reviewer_feedback": reviewer_feedback,
            "final_output": final_output
        }
        
    except Exception as e:
        error_msg = f"Error processing project: {str(e)}\n{traceback.format_exc()}"
        raise Exception(error_msg)

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')

