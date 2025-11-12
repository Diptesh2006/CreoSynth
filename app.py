from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from crewai import Agent, Task, Crew, Process
import uuid
from datetime import datetime
import traceback
import threading

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Store projects in memory (in production, use a database)
projects = {}

# Choose the LiteLLM-style model string that CrewAI will use.
# Options you can use: "gemini/gemini-2.0-flash", "gemini/gemini-1.5-flash", "gemini/gemini-1.5-pro"
# If you hit 404 model-not-found, try a different supported model string.
MODEL_ID = os.environ.get("MODEL_ID", "gemini/gemini-2.0-flash")


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
        data = request.json or {}
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
                "error": "Gemini / OpenAI API key is required"
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

    data = request.json or {}
    projects[project_id].update(data)
    projects[project_id]["updated_at"] = datetime.now().isoformat()

    return jsonify({
        "success": True,
        "project": projects[project_id]
    })


def process_crewai_project(project_id, topic, guidelines, api_key):
    """
    Process a project using CrewAI with LiteLLM-style Gemini model string.

    Important:
    - This function sets both GEMINI_API_KEY and GOOGLE_API_KEY environment variables
      (some integrations expect one or the other).
    - It passes a model string (MODEL_ID) to Agent(..., llm=MODEL_ID) so CrewAI uses LiteLLM.
    """
    try:
        # Set API keys for downstream libraries that expect either name
        os.environ["GEMINI_API_KEY"] = api_key
        os.environ["GOOGLE_API_KEY"] = api_key

        # If you want to override the model per-request, you can add that here.
        model_to_use = MODEL_ID

        # Define Agents using the model string (LiteLLM-style)
        creative_writer = Agent(
            role='Creative Content Writer',
            goal='To write an engaging, informative, and human-like blog post on a given topic.',
            backstory=(
                "You are an expert content creator who specializes in "
                "technology and culture. You know how to break down complex "
                "topics into simple, engaging narratives that captivate an audience."
            ),
            llm=model_to_use,   # pass model string so CrewAI uses LiteLLM
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
            llm=model_to_use,
            verbose=False,
            allow_delegation=False,
        )

        compliance_agent = Agent(
            role='Legal and Ethics Compliance Officer',
            goal='Perform a final legal/ethical/copyright check with a decisive verdict.',
            backstory=(
                "You are a detail-oriented compliance expert. Scan text for legal, ethical, "
                "and copyright risks and give a final GO / NO-GO."
            ),
            llm=model_to_use,
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

        compliance_task = Task(
            description=(
                "Perform a final legal and ethical compliance check on the blog post. "
                "Scan the text for any sensitive topics, potential misinformation, "
                "or copyright red flags. Provide a final 'GO' or 'NO-GO' with a brief justification."
            ),
            expected_output="A final 'GO' or 'NO-GO' verdict with a 1-sentence explanation.",
            agent=compliance_agent,
            context=[write_task, review_task],
        )

        # Create and Run the Crew
        my_crew = Crew(
            agents=[creative_writer, brand_reviewer, compliance_agent],
            tasks=[write_task, review_task, compliance_task],
            process=Process.sequential,
            verbose=False
        )

        task_inputs = {
            'topic': topic,
            'guidelines': guidelines
        }

        # Kick off CrewAI run (synchronous call here; CrewAI will orchestrate agents)
        result = my_crew.kickoff(inputs=task_inputs)

        writer_output = ""
        reviewer_feedback = ""
        final_output = str(result)

        # Attempt to parse task outputs if available
        try:
            if hasattr(result, 'tasks_output'):
                for task_output in result.tasks_output:
                    text = str(task_output)
                    # naive checks — adjust as needed to match CrewAI runtime shape
                    if 'Creative Content Writer' in text or 'Writer' in text:
                        writer_output = text
                    elif 'Brand Compliance Reviewer' in text or 'Reviewer' in text:
                        reviewer_feedback = text
                    elif 'Legal and Ethics' in text or 'Compliance' in text:
                        # Could be final verdict from compliance agent
                        final_output = text
        except Exception:
            # fall back to simple splitting if structure is unknown
            pass

        # If we couldn't extract separately, try a best-effort split of the final output
        if not writer_output and not reviewer_feedback:
            parts = final_output.split("Review", 1)
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
        # Re-raise so the caller/thread can capture and persist error status
        raise Exception(error_msg)


if __name__ == '__main__':
    # For local testing only. In production use a proper WSGI server.
    app.run(debug=True, port=5000, host='0.0.0.0')
