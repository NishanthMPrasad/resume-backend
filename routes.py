# backend/routes.py
'''
from flask import request, jsonify, send_file, Blueprint
import io

# Make sure these functions are correctly imported from your other files
from document_generator import generate_docx_from_data, generate_pdf_from_data
from file_parser import parse_resume_file
from gemini_utils import generate_elevator_pitch # Changed to import from gemini_utils

@api_bp.route('/parse-resume', methods=['POST'])
def parse_resume_route():
    print("→ Received /api/parse-resume")               # ← add this
    if 'file' not in request.files:
        print("   ❌ no file part")
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    print("   📄 filename:", file.filename)              # ← and this
    ...


def normalize_pipe_separated_field(field_value):
    """Converts a pipe-separated string or list into a clean list of items."""
    if isinstance(field_value, str):
        return [item.strip() for item in field_value.split('|') if item.strip()]
    elif isinstance(field_value, list):
        return [item.strip() for item in field_value if isinstance(item, str) and item.strip()]
    return []


# Create a Blueprint for API routes
api_bp = Blueprint('api', __name__)

# --- Resume Parsing Endpoint ---
@api_bp.route('/parse-resume', methods=['POST'])
def parse_resume_route():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if file:
        try:
            result = parse_resume_file(file)
            if "error" in result:
                return jsonify(result), 500
            
            return jsonify(result), 200

        except Exception as e:
            print(f"An unexpected error occurred in /api/parse-resume: {e}")
            return jsonify({"error": "An internal server error occurred during parsing."}), 500
    
    return jsonify({"error": "An unknown error occurred"}), 500


# --- Document Generation Endpoints ---
@api_bp.route('/generate-docx', methods=['POST'])
def generate_docx_route():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    resume_data = request.json
    # Normalize Certifications and any other pipe-separated fields
    resume_data['certifications'] = normalize_pipe_separated_field(resume_data.get('certifications', ''))
    resume_data['skills'] = normalize_pipe_separated_field(resume_data.get('skills', ''))
    resume_data['education'] = normalize_pipe_separated_field(resume_data.get('education', ''))
    resume_data['experience'] = normalize_pipe_separated_field(resume_data.get('experience', ''))

    try:
        doc = generate_docx_from_data(resume_data)
        file_stream = io.BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)
        
        personal_info = resume_data.get('personal', {})
        filename = f"{personal_info.get('name', 'resume').replace(' ', '_')}.docx"
        
        return send_file(
            file_stream,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    except Exception as e:
        print(f"Error generating DOCX: {e}")
        return jsonify({"error": "An internal error occurred while generating the DOCX file."}), 500


@api_bp.route('/generate-pdf', methods=['POST'])
def generate_pdf_route():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
        
    resume_data = request.json
    try:
        pdf_bytes = generate_pdf_from_data(resume_data)
        
        personal_info = resume_data.get('personal', {})
        filename = f"{personal_info.get('name', 'resume').replace(' ', '_')}.pdf"

        return send_file(
            io.BytesIO(pdf_bytes),
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return jsonify({"error": "An internal error occurred while generating the PDF file."}), 500

# --- NEW: Elevator Pitch Generation Endpoint ---
@api_bp.route('/generate-elevator-pitch', methods=['POST'])
def generate_elevator_pitch_route():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    resume_data = request.json
    try:
        pitch = generate_elevator_pitch(resume_data) # Now calls the function from gemini_utils
        return jsonify({"elevatorPitch": pitch}), 200
    except Exception as e:
        print(f"Error generating elevator pitch: {e}")
        return jsonify({"error": "An internal error occurred while generating the elevator pitch."}), 500

'''
# backend/routes.py
'''
from flask import Blueprint, request, jsonify, send_file
import io
import traceback
from werkzeug.datastructures import FileStorage

from document_generator import generate_docx_from_data, generate_pdf_from_data
from file_parser import parse_resume_file
from gemini_utils import generate_elevator_pitch

api_bp = Blueprint('api', __name__)


def normalize_pipe_separated_field(field_value):
    """
    Convert a pipe-separated string or list into a clean Python list of strings.
    """
    if isinstance(field_value, str):
        return [item.strip() for item in field_value.split('|') if item.strip()]
    if isinstance(field_value, list):
        return [item.strip() for item in field_value if isinstance(item, str) and item.strip()]
    return []


@api_bp.route('/parse-resume', methods=['POST'])
def parse_resume_route():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    original = request.files['file']
    if original.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # Read the upload into memory once
    raw = original.read()
    last_exc = None

    # Try up to 3 times with a fresh FileStorage each time
    for attempt in range(3):
        try:
            stream = io.BytesIO(raw)
            fake_file = FileStorage(
                stream=stream,
                filename=original.filename,
                content_type=original.content_type or 'application/octet-stream'
            )
            result = parse_resume_file(fake_file)

            if isinstance(result, dict) and "error" in result:
                return jsonify(result), 500

            return jsonify(result), 200

        except Exception:
            last_exc = traceback.format_exc()
            print(f"⚠️ parse-resume attempt {attempt+1} failed:\n{last_exc}")

    print("❌ All parse-resume attempts failed. Last exception:")
    print(last_exc)
    return jsonify({"error": "Internal server error during parsing."}), 500


@api_bp.route('/generate-docx', methods=['POST'])
def generate_docx_route():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    # Normalize any pipe‑separated lists
    data['certifications'] = normalize_pipe_separated_field(data.get('certifications', []))
    data['skills']         = normalize_pipe_separated_field(data.get('skills', []))
    data['education']      = normalize_pipe_separated_field(data.get('education', []))
    data['experience']     = normalize_pipe_separated_field(data.get('experience', []))

    personal = data.get('personal', {})
    if not personal.get('name'):
        return jsonify({"error": "Missing resume data"}), 400

    try:
        doc = generate_docx_from_data(data)
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)

        filename = f"{personal.get('name').replace(' ', '_')}.docx"
        return send_file(
            buf,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    except Exception:
        traceback.print_exc()
        return jsonify({"error": "Internal error while generating DOCX."}), 500


@api_bp.route('/generate-pdf', methods=['POST'])
def generate_pdf_route():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    personal = data.get('personal', {})
    if not personal.get('name'):
        return jsonify({"error": "Missing resume data"}), 400

    try:
        pdf_bytes = generate_pdf_from_data(data)
        buf = io.BytesIO(pdf_bytes)

        filename = f"{personal.get('name').replace(' ', '_')}.pdf"
        return send_file(
            buf,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    except Exception:
        traceback.print_exc()
        return jsonify({"error": "Internal error while generating PDF."}), 500


@api_bp.route('/generate-elevator-pitch', methods=['POST'])
def generate_elevator_pitch_route():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    personal = data.get('personal', {})
    if not personal.get('name'):
        return jsonify({"error": "Missing resume data"}), 400

    try:
        pitch = generate_elevator_pitch(data)
        return jsonify({"elevatorPitch": pitch}), 200
    except Exception:
        traceback.print_exc()
        return jsonify({"error": "Internal error while generating elevator pitch."}), 500
'''
import io
from flask import Blueprint, request, jsonify, send_file
from document_generator import generate_docx_from_data, generate_pdf_from_data
from file_parser import parse_resume_file
from gemini_utils import generate_elevator_pitch

api_bp = Blueprint("api", __name__)

@api_bp.route("/parse-resume", methods=["POST"])
def parse_resume_route():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    f = request.files["file"]
    if f.filename == "":
        return jsonify({"error": "No file selected"}), 400
    try:
        result = parse_resume_file(f)
        return jsonify(result), 200
    except Exception as e:
        print("Parse error:", e)
        return jsonify({"error": str(e)}), 500

@api_bp.route("/generate-docx", methods=["POST"])
def generate_docx_route():
    data = request.get_json(force=True) or {}
    try:
        doc = generate_docx_from_data(data)
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        name = (data.get("personal",{}).get("name","resume") or "resume").replace(" ","_")
        return send_file(
            buf,
            as_attachment=True,
            download_name=f"{name}.docx",
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        print("DOCX gen error:", e)
        return jsonify({"error": str(e)}), 500

@api_bp.route("/generate-pdf", methods=["POST"])
def generate_pdf_route():
    data = request.get_json(force=True) or {}
    try:
        pdf_bytes = generate_pdf_from_data(data)
        buf = io.BytesIO(pdf_bytes)
        buf.seek(0)
        name = (data.get("personal",{}).get("name","resume") or "resume").replace(" ","_")
        return send_file(
            buf,
            as_attachment=True,
            download_name=f"{name}.pdf",
            mimetype="application/pdf"
        )
    except Exception as e:
        print("PDF gen error:", e)
        return jsonify({"error": str(e)}), 500

@api_bp.route("/generate-elevator-pitch", methods=["POST"])
def generate_pitch_route():
    data = request.get_json(force=True) or {}
    try:
        pitch = generate_elevator_pitch(data)
        return jsonify({"elevatorPitch": pitch}), 200
    except Exception as e:
        print("Pitch error:", e)
        return jsonify({"error": str(e)}), 500

