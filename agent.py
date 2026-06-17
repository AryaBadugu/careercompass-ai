"""
CareerCompass AI — 6-Step Reasoning Agent
(Stable OpenAI Direct Integration Build)
"""
import os
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables
load_dotenv()

class CareerCompassAgent:
    """
    6-step reasoning agent for career guidance.
    Directly leverages the stable AzureOpenAI client to avoid SDK authentication bugs.
    """
    
    def __init__(self):
        print("🚀 Initializing CareerCompass Agent...")
        
        # Pull required environment endpoints cleanly
        # Construct the base endpoint url from your project endpoint if needed
        endpoint = os.getenv("PROJECT_ENDPOINT").split("/api/projects/")[0]
        
        # Connect directly using the standard, stable client architecture
        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=os.getenv("PROJECT_KEY"),
            api_version="2024-05-01-preview",
            timeout=55.0,          # Keep under Render's 60s hard limit
            max_retries=1
        )
        print("✅ Direct Cloud Pipeline Established Successfully!")
    
    def analyze_profile(self, user_input: str) -> dict:
        """
        Run the full 6-step analysis for a user profile.
        Returns all steps and the final plan.
        """
        print(f"\n📊 Analyzing profile: {user_input[:50]}...")
        steps_log = []
        
        print("🤔 Agent is reasoning through the 6 architectural steps...")
        
        # Generate the structured analysis straight via chat completions
        response = self.client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=[
                {
                    "role": "system",
                    "content": """You are CareerCompass AI, a career guidance agent. 
When a user describes their profile, you MUST follow these 6 steps IN ORDER.
After EACH step, print "STEP X COMPLETE:" followed by your findings.
Be CONCISE in each step — use bullet points, not paragraphs.

STEP 1 - PROFILE ANALYSIS:
Extract the exact details from the user's input.
IMPORTANT: Format the output EXACTLY like this (use comma-separated technical keywords only, no conversational text):
Skills=[Python, React, Machine Learning]
Goals=[AI/ML Engineer, Full Stack Developer]
Education=2nd year Engineering student, CS
Experience=Built Health Guardian AI, Neuro-Cursor

If no specific skills are found, use Skills=[Not specified]
Print: "STEP 1 COMPLETE:" followed by these 4 lines.

STEP 2 - CAREER SEARCH:
Simulate searching a career database to locate 5 matching career paths based on their engineering background and skills.
Print: "STEP 2 COMPLETE: Found careers=[career1, career2, ...]"

STEP 3 - GAP ANALYSIS:
Compare user's current skills to the requirements of each found career.
Identify what skills they're missing for each path. Keep it to 2-3 bullet points per career.
Print: "STEP 3 COMPLETE: Gaps identified for each path"

STEP 4 - OPPORTUNITY RANKING:
Score each career path from 1-10 based on:
- Skill match (how many skills they already have)
- Growth potential
- Effort to enter
Print: "STEP 4 COMPLETE: Ranked [career1: 8/10, career2: 7/10, ...]"

STEP 5 - ROADMAP CREATION:
For the TOP career, create a structured 90-day learning plan.
IMPORTANT: You MUST use exactly these headers for the frontend to parse them:
Phase 1: 0-30 Days
- [action 1]
- [action 2]
Phase 2: 31-60 Days
- [action 1]
- [action 2]
Phase 3: 61-90 Days
- [action 1]
- [action 2]
Keep each phase to 3-4 bullet points max.

Print: "STEP 5 COMPLETE:" followed by the roadmap.

STEP 6 - FINAL PLAN:
Synthesize everything into a detailed, premium action plan.
Format using Markdown:
- Use clear, bold headings for phases (e.g., **Phase 1: Foundation**, **Phase 2: Project Building**).
- Provide 3 highly relevant, premium project ideas that would stand out on a resume.
- Include a specific list of free resources, certifications, or tools from top-tier organizations (like LinkedIn Learning, Microsoft, Unstop, GitHub).
- Make it highly actionable, specific, and directly tailored to the user's background and goals.
- DO NOT use generic phrases like "As an AI..." or "Here is your plan." Start immediately with the structured plan.
Print: "STEP 6 COMPLETE:" followed immediately by the formatted plan.

ALWAYS follow all 6 steps. Never skip steps. Always be encouraging."""
                },
                {"role": "user", "content": user_input}
            ],
            temperature=0.7,
            max_tokens=3000
        )
        
        full_response = response.choices[0].message.content
        
        # Map step markers to parse structural validation blocks out cleanly
        step_markers = [
            "STEP 1 COMPLETE",
            "STEP 2 COMPLETE", 
            "STEP 3 COMPLETE",
            "STEP 4 COMPLETE",
            "STEP 5 COMPLETE",
            "STEP 6 COMPLETE"
        ]
        
        for i, marker in enumerate(step_markers):
            if marker in full_response:
                start = full_response.find(marker)
                end = full_response.find("STEP", start + 1) if i < 5 else len(full_response)
                step_content = full_response[start:end].strip()
                steps_log.append({
                    "step": i + 1,
                    "name": get_step_name(i + 1),
                    "output": step_content,
                    "status": "complete"
                })
        
        return {
            "steps": steps_log,
            "full_response": full_response,
            "steps_completed": len(steps_log)
        }

    def analyze_profile_with_feedback(self, user_input: str) -> dict:
        """
        Run 6-step analysis WITH feedback loop.
        If user says "no," agent regenerates the ranking.
        """
        result = self.analyze_profile(user_input)

        # After initial analysis, ask for feedback
        return result  # This will be handled in the frontend

    def regenerate_ranking(self, original_profile: str, user_feedback: str) -> dict:
        """
        Agent regenerates ranking based on feedback.
        Shows adaptive AI reasoning.
        """
        feedback_prompt = f"""
        The user gave this feedback on your initial career analysis:
        "{user_feedback}"

        Original profile:
        "{original_profile}"

        Based on this feedback:
        1. Re-analyze which career paths the user might prefer
        2. Re-rank them with different criteria
        3. Generate an alternative roadmap

        Return the updated ranking and roadmap.
        """

        response = self.client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=[
                {
                    "role": "system",
                    "content": "You are CareerCompass AI. Regenerate the ranking and roadmap based on user feedback. Return a clear, structured update with the revised ranking and roadmap."
                },
                {
                    "role": "user",
                    "content": feedback_prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )

        regenerated_response = response.choices[0].message.content

        return {
            "feedback": user_feedback,
            "regenerated_response": regenerated_response,
            "feedback_applied": True
        }

    def compare_two_careers(self, career1: str, career2: str) -> dict:
        """
        Compare two career paths in detail.
        """
        comparison_prompt = f"""
        Compare these two career paths in detail:
        Career 1: {career1}
        Career 2: {career2}

        You MUST output your response as a STRICT, VALID JSON object with exactly this schema. Do NOT include markdown formatting (like ```json) or any conversational text.
        {{
          "career1": {{
            "name": "{career1}",
            "skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"],
            "time_to_enter": "Estimated time",
            "growth_potential": "Growth/salary potential",
            "job_market": "Demand and availability",
            "work_life_balance": "Typical balance",
            "best_fit_for": "Personality/Profile fit"
          }},
          "career2": {{
            "name": "{career2}",
            "skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"],
            "time_to_enter": "Estimated time",
            "growth_potential": "Growth/salary potential",
            "job_market": "Demand and availability",
            "work_life_balance": "Typical balance",
            "best_fit_for": "Personality/Profile fit"
          }},
          "recommendation": "Final clear verdict and recommendation."
        }}
        """

        response = self.client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=[
                {
                    "role": "system",
                    "content": "You are CareerCompass AI. Output ONLY valid JSON containing the comparison of the two careers."
                },
                {
                    "role": "user",
                    "content": comparison_prompt
                }
            ],
            temperature=0.7,
            max_tokens=1500
        )

        comparison_response = response.choices[0].message.content.strip()
        
        # Clean up any potential markdown wrapper
        if comparison_response.startswith('```json'):
            comparison_response = comparison_response[7:]
        if comparison_response.startswith('```'):
            comparison_response = comparison_response[3:]
        if comparison_response.endswith('```'):
            comparison_response = comparison_response[:-3]
            
        import json
        try:
            parsed_comparison = json.loads(comparison_response.strip())
        except json.JSONDecodeError:
            # Fallback in case of parse error
            parsed_comparison = {"error": "Failed to generate structured comparison. Please try again."}

        return {"comparison": parsed_comparison}
    
    def cleanup(self):
        """No orphan resources to clear on direct completion endpoints"""
        print("🗑️ Context teardown completed smoothly")

        

def get_step_name(step_num: int) -> str:
    names = {
        1: "Profile Analysis",
        2: "Career Path Search",
        3: "Skills Gap Analysis",
        4: "Opportunity Ranking",
        5: "Roadmap Creation",
        6: "Final Action Plan"
    }
    return names.get(step_num, f"Step {step_num}")


# Execute pipeline validation test directly
if __name__ == "__main__":
    try:
        agent = CareerCompassAgent()
        
        result = agent.analyze_profile(
            "I am Arya, a 2nd year Engineering student interested in CS and Machine Learning. "
            "I've built a multi-disease risk prediction system called Health Guardian AI, "
            "and an eye-controlled mouse interface called Neuro-Cursor developed for both "
            "paralyzed users and the defense and medical sectors. "
            "I want to become an AI/ML engineer."
        )
        
        print("\n" + "="*50)
        print("STEPS COMPLETED successfully:", result["steps_completed"])
        print("="*50)
        for step in result["steps"]:
            print(f"\n✅ Step {step['step']}: {step['name']}")
            print(step["output"][:350] + "...\n")
        
    finally:
        if 'agent' in locals():
            agent.cleanup()