import os
import traceback
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from crewai import Agent, Task, Crew, Process

# ********************** WARNING **********************
# This file contains a hardcoded API key. DO NOT commit this file to public repos.
# Replace the line below with a secure secret retrieval mechanism in production.
# ********************** WARNING **********************

# --- Hardcoded API Key (user requested) ---
os.environ["GOOGLE_API_KEY"] = "AIzaSyBs2MrjRDDy9nxeaXKU68jTBvET9OpaFIY"
# also set GEMINI_API_KEY for libraries that expect that
os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]

# --- Model choices (litellm expects provider prefix like 'google/...') ---
# Primary preferred model (may require billing/permissions)
MODEL_ID = "google/gemini-2.0-flash"
# Fallback if primary model not available
FALLBACK_MODEL_ID = "google/gemini-1.5-flash"

# FastAPI + CORS
app = FastAPI(title="Creative Co-Pilot Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
async def root():
    return {
        "message": "Creative Co-Pilot Backend API",
        "status": "running",
        "endpoints": {
            "generate": "/generate (POST)",
            "health": "/health (GET)",
            "docs": "/docs (GET)"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "Creative Co-Pilot Backend"}


# Pydantic model for incoming requests
class CrewInput(BaseModel):
    topic: str
    guidelines: str

def build_crew_and_run(model_id: str, topic: str, guidelines: str):
    """
    Build agents/tasks, run Crew, and return a dictionary 
    containing the blog post, review, and compliance verdict.
    """
    # Define Agents (pass model_id string so CrewAI uses litellm/LiteLLM)
    creative_writer = Agent(
        role='Creative Content Writer',
        goal=f'To write an engaging, informative, human-like blog post on the topic: "{topic}".',
        backstory="You are an expert content creator who crafts compelling narratives.",
        llm=model_id,
        verbose=False,
    )

    brand_reviewer = Agent(
        role='Brand Compliance Reviewer',
        goal='To review the blog post and ensure it strictly adheres to the brand guidelines.',
        backstory="You are the guardian of the brand's voice—meticulous and consistent.",
        llm=model_id,
        verbose=False,
    )

    compliance_agent = Agent(
        role='Legal and Ethics Compliance Officer',
        goal='To perform a final check on the blog post for legal, ethical, and copyright risks.',
        backstory="You are a detail-oriented compliance expert who gives a final go/no-go.",
        llm=model_id,
        verbose=False,
    )

    # Tasks
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
            "Provide a simple 'APPROVED' or 'REJECTED' with feedback for revision."
        ),
        expected_output="A short review, either 'APPROVED' or 'REJECTED' with clear revision notes.",
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

    my_crew = Crew(
        agents=[creative_writer, brand_reviewer, compliance_agent],
        tasks=[write_task, review_task, compliance_task],
        process=Process.sequential,
        verbose=True
    )

    # kickoff with inputs
    task_inputs = {
        "topic": topic,
        "guidelines": guidelines
    }

    # Run the crew and get the final output (from compliance task)
    compliance_verdict = my_crew.kickoff(inputs=task_inputs)
    
    # --- THIS IS THE FIX ---
    # We must explicitly convert all outputs to strings.
    # In modern crewai, task.output is an object, so we access .raw_output
    # We use 'str()' as a safe fallback for all versions.
    
    def get_raw(output):
        """Safely extracts the raw string from a TaskOutput object."""
        if hasattr(output, 'raw_output') and output.raw_output:
            return str(output.raw_output)
        return str(output)

    result = {
        "blog_post": get_raw(write_task.output),
        "review_feedback": get_raw(review_task.output),
        "compliance_verdict": get_raw(compliance_verdict)
    }
    
    return result

@app.post("/generate")
async def generate_content(crew_input: CrewInput):
    # Input validation
    if not crew_input.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required.")
    if not crew_input.guidelines.strip():
        raise HTTPException(status_code=400, detail="Guidelines are required.")

    # Ensure key present
    if not os.environ.get("GOOGLE_API_KEY"):
        raise HTTPException(status_code=500, detail="Google API key not set on server.")

    # Try with primary MODEL_ID, fallback to FALLBACK_MODEL_ID on errors like NotFound/BadRequest.
    try_models = [MODEL_ID, FALLBACK_MODEL_ID]
    last_exc = None

    for model in try_models:
        try:
            # Result is now a dictionary: {blog_post, review_feedback, compliance_verdict}
            result_object = build_crew_and_run(model, crew_input.topic, crew_input.guidelines)
            
            # success
            return {"success": True, "model_used": model, "result": result_object}
        
        except Exception as e:
            # Inspect common error messages for helpful guidance
            tb = traceback.format_exc()
            last_exc = (e, tb)
            err_text = str(e).lower()

            # If quota/resource-exhausted, return clear message
            if "resource exhausted" in err_text or "quota" in err_text or "429" in err_text:
                raise HTTPException(
                    status_code=503,
                    detail=(
                        "Provider quota exhausted or rate-limited. "
                        "Enable billing or try again later. "
                        f"Error: {str(e)}"
                    ),
                )

            # If not found / 404 for model, try fallback model
            if "not found" in err_text or "404" in err_text or "is not found" in err_text:
                # try next model in loop
                continue

            # If litellm provider error, craft suggestion
            if "provider not provided" in err_text or "llm provider not provided" in err_text:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        "LLM Provider not provided — the model string must be prefixed "
                        "with provider (e.g. 'google/gemini-2.0-flash'). "
                        f"Server error: {str(e)}"
                    ),
                )

            # otherwise continue to fallback attempt
            continue

    # If both attempts failed, return last exception
    exc, tb = last_exc if last_exc else (RuntimeError("Unknown error"), "")
    raise HTTPException(status_code=500, detail=f"All model attempts failed. Last error: {str(exc)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting FastAPI server on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port) 


