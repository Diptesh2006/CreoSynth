# --- 1) Install Required Libraries (adds litellm!) ---
!pip install -q -U crewai crewai-tools litellm langchain-google-genai google-generativeai langchain langchain-core
print("Libraries installed successfully.")

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from crewai import Agent, Task, Crew, Process

# --- 1) Configuration: API key source (env preferred) ---
# Recommended: set GEMINI_API_KEY in the environment.
# Fallback: replace the placeholder below with your key for quick local testing only.
HARDCODED_FALLBACK_KEY = "AIzaSyBs2MrjRDDy9nxeaXKU68jTBvET9OpaFIY"

# Try environment first, else fallback to the hard-coded key
gemini_key = os.environ.get("GEMINI_API_KEY", None)
if not gemini_key:
    gemini_key = HARDCODED_FALLBACK_KEY

# Set both variables used by integrations
os.environ["GEMINI_API_KEY"] = gemini_key
os.environ["GOOGLE_API_KEY"] = gemini_key

# --- 2) Model selection (LiteLLM-style name for CrewAI) ---
# Options: "gemini/gemini-2.0-flash", "gemini/gemini-1.5-flash", "gemini/gemini-1.5-pro"
MODEL_ID = "gemini/gemini-2.0-flash"

# --- 3) (Optional) Quick key/model sanity check via LangChain (doesn't require litellm) ---
llm_ok = False
try:
    print("Initializing Google Gemini LLM for a quick key test...")
    # ChatGoogleGenerativeAI expects model name like "gemini-2.0-flash" (without the "gemini/" prefix)
    test_llm = ChatGoogleGenerativeAI(
        model=MODEL_ID.split("/", 1)[1],  # e.g., "gemini-2.0-flash"
        temperature=0.2,
        max_tokens=64,
    )
    _ = test_llm.invoke("ping")
    llm_ok = True
    print("Key validated successfully.")
except Exception as e:
    print("\n--- LLM INITIALIZATION / KEY TEST FAILED ---")
    print(f"Error details: {e}")
    print("If it's a 404, use a supported model like 'gemini-1.5-flash' or 'gemini-2.0-flash'.")
    print("If it's a 429/quota error, enable billing or try a lower-cost model.")
    # We'll still attempt CrewAI usage; some integrations may succeed even if the quick test fails.

# --- 4) Define Agents using LiteLLM model string (pass model string so CrewAI uses LiteLLM) ---
try:
    print("Defining agents...")
    creative_writer = Agent(
        role='Creative Content Writer',
        goal='Write an engaging, informative, human-like blog post on a given topic.',
        backstory="You are an expert content creator who crafts compelling narratives.",
        llm=MODEL_ID,            # pass the model string; CrewAI will use LiteLLM
        verbose=True,
    )

    brand_reviewer = Agent(
        role='Brand Compliance Reviewer',
        goal='Ensure the content strictly adheres to brand guidelines.',
        backstory="You are the guardian of the brand’s voice—meticulous and consistent.",
        llm=MODEL_ID,
        verbose=True,
    )

    compliance_agent = Agent(
        role='Legal and Ethics Compliance Officer',
        goal='Final legal/ethical/copyright check with a decisive verdict.',
        backstory="Detail-oriented compliance expert who gives the final go/no-go.",
        llm=MODEL_ID,
        verbose=True,
    )

    print("Defining tasks...")
    write_task = Task(
        description=(
            "Write a 300-word blog post about the topic: '{topic}'. "
            "The post must be engaging and easy to understand."
        ),
        expected_output='A formatted blog post (text) of around 300 words.',
        agent=creative_writer,
    )

    review_task = Task(
        description=(
            "Review the blog post written by the Creative Writer. "
            "Check it against the following Brand Guidelines: '{guidelines}'. "
            "Provide 'APPROVED' or 'REJECTED' with concise revision notes."
        ),
        expected_output="A short review: 'APPROVED' or 'REJECTED' with clear notes.",
        agent=brand_reviewer,
        context=[write_task],
    )

    compliance_task = Task(
        description=(
            "Perform a final legal and ethical compliance check on the blog post. "
            "Scan the text for sensitive topics, potential misinformation, "
            "or copyright red flags. Provide a final 'GO' or 'NO-GO' with a brief justification."
        ),
        expected_output="Final verdict: 'GO' or 'NO-GO' with a 1-sentence explanation.",
        agent=compliance_agent,
        context=[write_task, review_task],
    )

    print("Assembling and kicking off the crew...")
    my_crew = Crew(
        agents=[creative_writer, brand_reviewer, compliance_agent],
        tasks=[write_task, review_task, compliance_task],
        process=Process.sequential,
        verbose=True
    )

    task_inputs = {
        'topic': 'The Future of Agentic AI',
        'guidelines': 'Tone must be optimistic, inspiring, and avoid complex technical jargon.'
    }

    result = my_crew.kickoff(inputs=task_inputs)

    print("\n\n--- Hackathon Co-Pilot Run Complete ---")
    print("Crew's final output (from Compliance Agent):")
    print(result)

except Exception as e:
    print("\n--- A CREWAI ERROR OCCURRED ---")
    print(f"Error details: {e}")
    print("\nQuick fixes to try:")
    print("1) Ensure 'litellm' is installed (we installed it above).")
    print("2) Switch MODEL_ID to 'gemini/gemini-1.5-flash' if 404 or access issues persist.")
    print("3) If you get 429 errors, enable billing or reduce request rate/content length.")


