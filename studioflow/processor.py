
import json
import os
import uuid
from openai import OpenAI
from models import NormalizedIntake

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are a senior architect's project coordinator.
Your job is to take a normalized client intake and generate a structured architecture project output.

You must respond with valid JSON only. No markdown. No explanation. No code fences.

The JSON must match this exact structure:
{
  "project_id": "<uuid>",
  "project_title": "<short descriptive title>",
  "project_brief": "<2-3 sentence summary of the project>",
  "scope_of_work": ["<item>", ...],
  "phases": [
    {
      "phase_number": 1,
      "name": "<phase name>",
      "description": "<what happens in this phase>",
      "estimated_duration_weeks": <integer>,
      "key_deliverables": ["<deliverable>", ...]
    }
  ],
  "key_considerations": ["<consideration>", ...],
  "recommended_next_steps": ["<step>", ...]
}
"""

def generate_project_output(normalized: NormalizedIntake, project_id: str = None) -> dict:
    if project_id is None:
        project_id = str(uuid.uuid4())

    intake_summary = f"""
Client: {normalized.client_name or "Not provided"}
Project Type: {normalized.project_type or "Not specified"}
Location: {normalized.location or "Not specified"}
Description: {normalized.description or "Not provided"}
Budget: {normalized.budget or "Not specified"}
Timeline: {normalized.timeline or "Not specified"}
""".strip()

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Generate a structured project output for this intake:\n\n{intake_summary}\n\nUse this project_id: {project_id}"
                },
            ],
            temperature=0.3,
        )

        raw_text = response.choices[0].message.content.strip()

        return json.loads(raw_text)

    except Exception as e:
        return {
            "status": "error",
            "error": "llm_failure",
            "details": str(e),
        }
