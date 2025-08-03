import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API with your key
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file.")
    genai.configure(api_key=api_key)
except Exception as e:
    print(f"Error configuring Gemini API: {e}")

def structure_text_with_ai(raw_resume_text: str) -> dict:
    """
    Uses the Gemini model to parse raw resume text into a structured JSON object.

    Args:
        raw_resume_text: A string containing the full text from the resume.

    Returns:
        A dictionary with the structured resume data.
    """
    
    # Define the JSON schema the AI must follow, now correctly specifying projects and certifications
    # Removed hardcoded IDs like "exp1", "cert1" to avoid "duplicate key" warnings.
    # The AI should now generate unique IDs or the frontend will assign crypto.randomUUID().
    json_schema = """
    {
      "personal": {"name": "", "email": "", "phone": "", "location": "", "legalStatus": ""},
      "summary": "",
      "experience": [
        {"id": "string", "jobTitle": "", "company": "", "dates": "", "description": ""}
      ],
      "education": [
        {"id": "string", "degree": "", "institution": "", "graduationYear": "", "gpa": "", "achievements": ""}
      ],
      "skills": [
        {"id": "string", "category": "", "skills_list": ""}
      ],
      "projects": [
        {"id": "string", "title": "", "date": "", "description": ""}
      ],
      "publications": [
        {"id": "string", "title": "", "authors": "", "journal": "", "date": "", "link": ""}
      ],
      "certifications": [
        {"id": "string", "name": "", "issuer": "", "date": ""}
      ]
    }
    """

    # Create the prompt for the AI model
    prompt = f"""
    You are an expert resume parsing assistant. Analyze the following raw text extracted from a resume and convert it into a structured JSON object. 
    The JSON object must follow this exact schema. 
    Do not add any fields that are not in the schema. Do not enclose the JSON in markdown backticks.
    For the 'description' and 'achievements' fields, maintain the original line breaks from the resume text.
    If a section (like 'projects' or 'publications') is not present in the text, provide an empty list for that key.

    **JSON Schema to follow:**
    ```json
    {json_schema}
    ```

    **Raw Resume Text to Parse:**
    ```
    {raw_resume_text}
    ```
    """

    try:
        # Changed model to gemini-2.0-flash for consistency and better performance
        model = genai.GenerativeModel('gemini-2.0-flash') 
        response = model.generate_content(prompt)
        cleaned_json_string = response.text.strip().replace('```json', '').replace('```', '').strip()
        structured_data = json.loads(cleaned_json_string)
        
        return structured_data

    except Exception as e:
        print(f"An error occurred while calling the Gemini API or parsing its response: {e}")
        # Return a default empty structure on error to prevent frontend crashes
        return {
            "personal": {},
            "summary": "",
            "experience": [],
            "education": [],
            "skills": [],
            "projects": [],
            "publications": [],
            "certifications": []
        }

# --- NEW: Elevator Pitch Function for Gemini ---
def generate_elevator_pitch(resume_data: dict) -> str:
    """Generates a concise elevator pitch from resume data using Gemini."""
    
    # Extract relevant info from resume_data
    personal = resume_data.get('personal', {})
    summary = resume_data.get('summary', '')
    experience = resume_data.get('experience', [])
    skills = resume_data.get('skills', [])
    education = resume_data.get('education', [])
    projects = resume_data.get('projects', []) # Added projects

    # Concatenate relevant information for the prompt
    context_parts = []
    if personal.get('name'):
        context_parts.append(f"Name: {personal['name']}")
    if personal.get('jobTitle'): 
        context_parts.append(f"Current Role: {personal['jobTitle']}")
    if summary:
        context_parts.append(f"Summary: {summary}")
    
    if experience:
        exp_strings = []
        for exp in experience:
            exp_strings.append(f"- {exp.get('jobTitle', '')} at {exp.get('company', '')} ({exp.get('dates', '')}). Description: {exp.get('description', '')}")
        context_parts.append("Experience:\n" + "\n".join(exp_strings))
    
    if skills:
        skill_strings = []
        for skill_cat in skills:
            if skill_cat.get('category') and skill_cat.get('skills_list'):
                skill_strings.append(f"- {skill_cat['category']}: {skill_cat['skills_list']}")
            elif skill_cat.get('skills_list'):
                skill_strings.append(f"- {skill_cat['skills_list']}")
        context_parts.append("Skills:\n" + ", ".join(skill_strings))

    if projects: # Added projects to context for pitch generation
        proj_strings = []
        for proj in projects:
            proj_strings.append(f"- {proj.get('title', '')} ({proj.get('date', '')}). Description: {proj.get('description', '')}")
        context_parts.append("Projects:\n" + "\n".join(proj_strings))

    if education:
        edu_strings = []
        for edu in education:
            edu_strings.append(f"- {edu.get('degree', '')} from {edu.get('institution', '')} ({edu.get('graduationYear', '')})")
        context_parts.append("Education:\n" + "\n".join(edu_strings))

    full_context = "\n\n".join(context_parts)
    
    prompt = f"""
    Based on the following resume data, generate a compelling and concise 30-second elevator pitch.
    The pitch should be professional, engaging, and highlight the candidate's key strengths, experiences, and career goals.
    Focus on what makes the candidate unique and valuable.
    Keep it under 100 words.

    Resume Details:
    ---
    {full_context}
    ---

    Elevator Pitch:
    """
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash') # Ensure you have this model downloaded for Gemini
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error calling Gemini for elevator pitch: {e}")
        return "Could not generate elevator pitch at this time."

def enhance_section_with_ai(section_name, text_to_enhance):
    """
    Enhances a given text section using a generative AI model.

    Args:
        section_name (str): The name of the section (e.g., "Summary", "Experience Description").
        text_to_enhance (str): The original text content to be enhanced.

    Returns:
        list: A list of enhanced versions of the text.
    """
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"""
        Rewrite the following {section_name} to be more impactful, professional, and concise.
        Provide 3 different versions. Ensure the output is clean text, without any markdown formatting like bullet points or bolding, unless it's inherent to the content (e.g., a list of skills).
        Return each version on a new line.

        Original {section_name}:
        {text_to_enhance}

        Enhanced Versions:
        """
        response = model.generate_content(prompt)
        # Split the response into lines, assuming each line is a new version
        return [version.strip() for version in response.text.split('\n') if version.strip()]
    except Exception as e:
        print(f"Error enhancing section with AI: {e}")
        return [text_to_enhance] # Return original on error
