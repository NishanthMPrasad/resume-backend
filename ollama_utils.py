# backend/ollama_utils.py
import requests
import json
import re

# This is the confirmed working endpoint from your test
OLLAMA_API_URL = "http://localhost:11434/api/generate" 
MODEL_NAME = "llama3:latest" # Using :latest as shown in your ollama list output

def _query_ollama(prompt, is_json=False):
    """Generic function to query the Ollama API using the generate endpoint."""
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    if is_json:
        payload["format"] = "json"
        
    try:
        # Increased timeout to 300 seconds (5 minutes) for complex tasks
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=300)
        response.raise_for_status()
        
        response_text = response.json().get('response', '')

        if is_json:
            # The model might wrap the JSON in markdown backticks, so we clean it.
            cleaned_json = re.sub(r'^```json\s*|\s*```$', '', response_text.strip(), flags=re.MULTILINE)
            return json.loads(cleaned_json)
        
        return response_text.strip()
        
    except requests.exceptions.RequestException as e:
        print(f"🚨 Error connecting to Ollama API: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"🚨 Error decoding JSON from Ollama response: {e}")
        print(f"Raw response: {response_text}")
        return None

def enhance_with_ollama(section_name: str, text_to_enhance: str) -> list[str]:
    """Sends text to Ollama for enhancement and returns multiple versions."""
    if not text_to_enhance.strip():
        return [text_to_enhance]
    
    is_summary = 'summary' in section_name.lower()

    if is_summary:
        prompt = f"""
        Rewrite and enhance the following resume summary. Make it more professional, impactful, and concise.
        Generate exactly 3 distinct versions.
        Your final output must be a valid JSON object with a single key "versions" that contains an array of the 3 strings.
        
        Example format: {{"versions": ["First version...", "Second version...", "Third version..."]}}
        
        Input Text:
        ---
        {text_to_enhance}
        ---
        """
        response_data = _query_ollama(prompt, is_json=True)
        if response_data and isinstance(response_data, dict):
            versions = response_data.get("versions", [])
            if isinstance(versions, list) and all(isinstance(v, str) for v in versions):
                return versions
        return [text_to_enhance] # Fallback
    else:
        prompt = f"""
        You are a professional resume advisor.
        Please rewrite the following resume section (Section: {section_name}) to be more professional and impactful.
        Focus on clarity, conciseness, and the use of action verbs. Use bullet points where appropriate.
        
        Input Text:
        ---
        {text_to_enhance}
        ---
        Improved Text:
        """
        response_text = _query_ollama(prompt)
        return [response_text] if response_text else [text_to_enhance]


def generate_resume_fields_from_raw_text(resume_text: str) -> dict:
    """Extracts structured resume data from raw text using a local Ollama model."""
    if not resume_text.strip():
        return {}
        
    schema = {
        "personal": {"name": "string", "email": "string", "phone": "string", "location": "string"},
        "summary": "string",
        "experience": [{"jobTitle": "string", "company": "string", "dates": "string", "description": "string"}],
        "education": [{"degree": "string", "institution": "string", "graduationYear": "string", "gpa": "string", "achievements": "string"}],
        "skills": [{"category": "string", "skills_list": "string"}],
        "certifications": [{"name": "string", "issuer": "string", "date": "string"}],
        "publications": [{"title": "string", "authors": "string", "journal": "string", "date": "string", "link": "string"}]
    }
    
    prompt = f"""
    You are an expert resume parser. Extract the information from the following resume text and provide the output in a valid JSON format that adheres to the schema provided below.
    Ensure all fields are filled, even if with an empty string or empty list if no information is found.
    
    Schema:
    {json.dumps(schema, indent=2)}
    
    Resume Text:
    ---
    {resume_text}
    ---
    
    JSON Output:
    """
    
    response_data = _query_ollama(prompt, is_json=True)
    return response_data if isinstance(response_data, dict) else {}

def generate_elevator_pitch(resume_data: dict) -> str:
    """Generates a concise elevator pitch from resume data using Ollama."""
    resume_summary_text = json.dumps(resume_data, indent=2)
    prompt = f"""
    Based on the following resume data, generate a compelling and concise 30-second elevator pitch.
    The pitch should be professional, engaging, and highlight the candidate's key strengths and career goals.
    
    Resume Details (JSON):
    ---
    {resume_summary_text}
    ---
    
    Elevator Pitch:
    """
    return _query_ollama(prompt) or "Could not generate elevator pitch."