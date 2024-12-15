from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import io
import tempfile
import os
import gc
from pydub import AudioSegment
import importlib

app = Flask(__name__)
CORS(app)

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
MAX_DURATION = 300  # 5 minutes in seconds

@app.route('/process', methods=['POST'])
def process_audio():
    try:
        # Check if a file is uploaded
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        if not file.filename.endswith('.mp3'):
            return jsonify({"error": "File must be MP3 format"}), 400

        # Check file size
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        if size > MAX_FILE_SIZE:
            return jsonify({"error": "File too large (max 20MB)"}), 400

        # Get the selected frequency type
        selected_frequency = request.form.get('frequency')
        if not selected_frequency:
            return jsonify({"error": "Frequency type not selected"}), 400

        # Save file temporarily and process it
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=True) as temp_mp3:
            file.save(temp_mp3.name)
            audio = AudioSegment.from_mp3(temp_mp3.name)

            # Check duration
            if len(audio) > MAX_DURATION * 1000:  # pydub uses milliseconds
                return jsonify({"error": "Audio too long (max 5 minutes)"}), 400

            # Dynamically load the conversion module
            frequency_map = {
                'Delta (0.5–4 Hz)': 'delta',
                'Theta (4–8 Hz)': 'theta',
                'Alpha (8–14 Hz)': 'alpha',
                'Beta (14–30 Hz)': 'beta',
                'Gamma (30–100 Hz)': 'gamma'
            }

            module_name = frequency_map.get(selected_frequency)
            if not module_name:
                return jsonify({"error": "Invalid frequency type"}), 400

            try:
                conversion_module = importlib.import_module(f'conversions.{module_name}')
                processed_audio = conversion_module.convert(audio)
            except ImportError:
                return jsonify({"error": f"Conversion module for {selected_frequency} not found"}), 500

        # Save processed WAV
        processed_output = io.BytesIO()
        processed_audio.export(processed_output, format="wav")
        processed_output.seek(0)

        gc.collect()  # Force garbage collection

        return Response(
            processed_output.read(),
            mimetype='audio/wav',
            headers={
                "Content-Disposition": f'attachment; filename="{module_name}_output.wav"'
            }
        )

    except Exception as e:
        gc.collect()
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
