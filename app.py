from flask import Flask, request, jsonify, render_template, send_from_directory
import os
from datetime import datetime
import openai
import wave
import contextlib
import json
from dotenv import load_dotenv
import logging
import sys
import socket

# Load .env file if it exists (for local development)
load_dotenv()

app = Flask(__name__)

# Configure app settings from environment variables
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'recordings')
app.config['COST_PER_MINUTE'] = float(os.getenv('COST_PER_MINUTE', '0.006'))
app.config['TITLE'] = os.getenv('TITLE', 'Voice Input')

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
app.logger.setLevel(getattr(logging, log_level, logging.INFO))

# Add hostname to logs for container identification
app.logger.info(f"Starting application on host: {socket.gethostname()}")

# Ensure the uploads directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Create or load the cost tracking file
COST_FILE = os.path.join(app.config['UPLOAD_FOLDER'], 'costs.json')
def load_costs():
    if os.path.exists(COST_FILE):
        with open(COST_FILE, 'r') as f:
            return json.load(f)
    return {'total_cost': 0.0, 'recordings': {}}

def save_costs(costs):
    with open(COST_FILE, 'w') as f:
        json.dump(costs, f)

def calculate_cost(duration_seconds):
    return (duration_seconds / 60.0) * app.config['COST_PER_MINUTE']

# Log configuration for debugging
app.logger.info(f"App configuration:")
app.logger.info(f"  UPLOAD_FOLDER: {app.config['UPLOAD_FOLDER']}")
app.logger.info(f"  COST_PER_MINUTE: {app.config['COST_PER_MINUTE']}")
app.logger.info(f"  TITLE: {app.config['TITLE']}")

# Configure OpenAI and app settings
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    app.logger.warning("OpenAI API key not found in environment variables or .env file")
    if not os.getenv('ALLOW_MISSING_API_KEY', '').lower() == 'true':
        app.logger.error("Application startup failed: Missing OpenAI API key")
        sys.exit(1)
openai.api_key = api_key

# Get confirmation setting from environment (default to True if not set)
CONFIRM_DELETE = os.getenv('CONFIRM_DELETE', 'true').lower() == 'true'

@app.route('/')
def index():
    costs = load_costs()
    return render_template('index.html', 
                           total_cost=costs['total_cost'], 
                           confirm_delete=CONFIRM_DELETE,
                           title=app.config['TITLE'])

@app.route('/upload', methods=['POST'])
def upload_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Generate unique filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'recording_{timestamp}.webm'
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Save the file
    audio_file.save(filepath)
    
    try:
        # Transcribe the audio using OpenAI's API
        with open(filepath, 'rb') as audio:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio
            )
        
        # Get audio duration and calculate cost
        duration = float(request.form.get('duration', 0))  # Duration in seconds
        cost = calculate_cost(duration)
        
        # Update costs tracking
        costs = load_costs()
        costs['recordings'][filename] = {
            'duration': duration,
            'cost': cost,
            'timestamp': timestamp
        }
        costs['total_cost'] = sum(rec['cost'] for rec in costs['recordings'].values())
        save_costs(costs)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'transcript': transcript.text,
            'duration': duration,
            'cost': cost,
            'total_cost': costs['total_cost']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_recording(filename):
    try:
        app.logger.debug(f'Delete request received for file: {filename}')
        # Ensure the filename only contains safe characters and has .webm extension
        if not filename.endswith('.webm') or '/' in filename or '\\' in filename:
            app.logger.error(f'Invalid filename format: {filename}')
            return jsonify({'error': 'Invalid filename'}), 400

        # Get the absolute path and verify it's within the uploads directory
        filepath = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        uploads_dir = os.path.abspath(app.config['UPLOAD_FOLDER'])
        
        app.logger.debug(f'File path: {filepath}')
        app.logger.debug(f'Uploads dir: {uploads_dir}')
        
        if not filepath.startswith(uploads_dir):
            app.logger.error(f'Path traversal attempt detected: {filepath}')
            return jsonify({'error': 'Invalid filename'}), 400
        
        if os.path.exists(filepath):
            app.logger.debug(f'File exists, attempting to delete: {filepath}')
            # Remove the file
            os.remove(filepath)
            app.logger.debug('File deleted successfully')
            
            # Update costs tracking
            costs = load_costs()
            if filename in costs['recordings']:
                del costs['recordings'][filename]
                costs['total_cost'] = sum(rec['cost'] for rec in costs['recordings'].values())
                save_costs(costs)
                app.logger.debug('Costs updated successfully')
            
            return jsonify({
                'success': True,
                'total_cost': costs['total_cost']
            })
        else:
            app.logger.error(f'File not found: {filepath}')
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        app.logger.error(f'Error during delete: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/recordings/<path:filename>')
def serve_recording(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.getenv('PORT', 5001))
    
    # Get debug setting from environment
    debug = os.getenv('FLASK_DEBUG', '').lower() == 'true'
    
    # In container environments, we need to listen on 0.0.0.0
    host = os.getenv('HOST', '0.0.0.0')
    
    app.logger.info(f"Starting server on {host}:{port} (debug={debug})")
    app.run(debug=debug, host=host, port=port)
