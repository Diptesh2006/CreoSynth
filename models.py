# --- 1. Install Required Libraries ---
# We install crewai and the official OpenAI library for langchain
!pip install crewai langchain-openai
print("Libraries installed successfully.")

# --- 2. Import Libraries ---
import os
from getpass import getpass
# V V V THIS IS THE NEW IMPORT V V V
from langchain_openai import ChatOpenAI
from crewai import Agent, Task, Crew, Process

# --- 3. Get API Key ---
# Ask for the OpenAI API Key
openai_api_key = getpass("Please enter your OpenAI API Key: ")
os.environ["OPENAI_API_KEY"] = openai_api_key

# --- 4. Main Code Block ---
try:
    # --- 4a. Setup the OpenAI LLM ---
    print("Initializing OpenAI LLM (gpt-4o-mini)...")
    
    # We will use 'gpt-4o-mini' as it's a fast, capable, and cost-effective model
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=4000
    )
    
    print("OpenAI LLM initialized successfully.")

    # --- 4b. Define Your Agents ---
    print("Defining agents...")
    
    creative_writer = Agent(
        role='Creative Content Writer',
        goal='To write an engaging, informative, and human-like blog post on a given topic.',
        backstory=(
            "You are an expert content creator who specializes in "
            "technology and culture. You know how to break down complex "
            "topics into simple, engaging narratives that captivate an audience."
        ),
        llm=llm,  # <-- This agent now uses the OpenAI LLM
        verbose=True,
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
        llm=llm,  # <-- This agent also uses the OpenAI LLM
        verbose=True,
        allow_delegation=False,
    )

    # --- 4c. Define the Tasks ---
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
            "Provide a simple 'APPROVED' or 'REJECTED' with feedback for revision."
        ),
        expected_output="A short review, either 'APPROVED' or 'REJECTED' with clear revision notes.",
        agent=brand_reviewer,
        context=[write_task],
    )

    # --- 4d. Create and Run the Crew ---
    print("Assembling and kicking off the crew...")
    
    my_crew = Crew(
        agents=[creative_writer, brand_reviewer],
        tasks=[write_task, review_task],
        process=Process.sequential,
        verbose=True
    )

    task_inputs = {
        'topic': 'The Future of Agentic AI',
        'guidelines': 'Tone must be optimistic, inspiring, and avoid complex technical jargon.'
    }

    result = my_crew.kickoff(inputs=task_inputs)

    # --- 4e. Show the Result ---
    print("\n\n--- Hackathon Co-Pilot Run Complete ---")
    print("Crew's final output:")
    print(result)

except Exception as e:
    # --- 4f. Catch All Errors ---
    print(f"\n--- AN ERROR OCCURRED ---")
    print(f"Error details: {e}")
    print("\nThis usually means your OpenAI API Key is invalid or has insufficient credits.")
    print("Please restart and try again.")