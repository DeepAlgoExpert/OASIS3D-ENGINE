from flask import Flask, request, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
import subprocess
import re
import json
import base64
from flask_cors import CORS

app = Flask(__name__)


CORS(app, resources={r"/try-on": {"origins": "https://oasis3d.netlify.app"}},
          allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Origin", "Access-Control-Allow-Headers", "Access-Control-Allow-Methods"])

CORS(app, resources={r"/measure": {"origins": "https://oasis3d.netlify.app"}},
          allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Origin", "Access-Control-Allow-Headers", "Access-Control-Allow-Methods"])

CORS(app, resources={r"/": {"origins": "https://oasis3d.netlify.app"}},
          allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Origin", "Access-Control-Allow-Headers", "Access-Control-Allow-Methods"])
CORS(app, resources={r"/*": {"origins": "https://oasis3d.netlify.app"}})

# Define the directory where uploaded files are stored

# Define the model upload folder
MEASURE_MODEL_UPLOAD_FOLDER = 'Measurement/3d_body/inputs'
app.config['MEASURE_MODEL_UPLOAD_FOLDER'] = MEASURE_MODEL_UPLOAD_FOLDER

# Ensure the model upload folder exists
if not os.path.exists(MEASURE_MODEL_UPLOAD_FOLDER):
    os.makedirs(MEASURE_MODEL_UPLOAD_FOLDER)


MEASURE_RESULT_FOLDER = 'Measurement/3d_body/results'
app.config['MEASURE_RESULT_FOLDER'] = MEASURE_RESULT_FOLDER

if not os.path.exists(MEASURE_RESULT_FOLDER):
    os.makedirs(MEASURE_RESULT_FOLDER)

# Define the model upload folder
MODEL_UPLOAD_FOLDER = 'images/model'
app.config['MODEL_UPLOAD_FOLDER'] = MODEL_UPLOAD_FOLDER

# Ensure the model upload folder exists
if not os.path.exists(MODEL_UPLOAD_FOLDER):
    os.makedirs(MODEL_UPLOAD_FOLDER)


# Define the model upload folder
GARMENT_UPLOAD_FOLDER = 'images/garment'
app.config['GARMENT_UPLOAD_FOLDER'] = GARMENT_UPLOAD_FOLDER

# Ensure the model upload folder exists
if not os.path.exists(GARMENT_UPLOAD_FOLDER):
    os.makedirs(GARMENT_UPLOAD_FOLDER)

RESULT_FOLDER = 'output'
app.config['RESULT_FOLDER'] = RESULT_FOLDER

# Ensure the model upload folder exists
if not os.path.exists(RESULT_FOLDER):
    os.makedirs(RESULT_FOLDER)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'jpg', 'png'}

# Function to check if a filename has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def delete_files_in_directory(directory_path):
   try:
     files = os.listdir(directory_path)
     for file in files:
       file_path = os.path.join(directory_path, file)
       if os.path.isfile(file_path):
         os.remove(file_path)
     print("All files deleted successfully.")
   except OSError:
     print("Error occurred while deleting files.")

@app.route("/")
def hello_world():
    return "This is body measure and vto test website!"

# Endpoint to serve vto result image
@app.route('/try-on/<path:filename>', methods=['GET'])
def get_vto(filename):
    print(filename)
    return send_from_directory(RESULT_FOLDER, filename)

# Endpoint to serve measure obj
@app.route('/measure/<path:filename>', methods=['GET'])
def get_obj(filename):
    print(filename)
    return send_from_directory(MEASURE_RESULT_FOLDER, filename)

# Endpoint for measurements
@app.route('/measure', methods=['POST'])
def measurement():
    if 'model' not in request.files:
        return jsonify({'error': 'Please provide model image.'})

    model = request.files['model']
    height = request.form['height']
    if model.filename == '':
        return jsonify({'error': 'Please provide valid model file'})

    model_image_path = 'Measurement/3d_body/inputs'
    output_smplx_path = 'Measurement/3d_body/results'
    output_smpl_path = 'Measurement/output'
    delete_files_in_directory(model_image_path)
    delete_files_in_directory(output_smplx_path)
    delete_files_in_directory(output_smpl_path)
    
    if model and allowed_file(model.filename):
        model_filename = secure_filename(model.filename)

        
        model.save(os.path.join(app.config['MEASURE_MODEL_UPLOAD_FOLDER'], model_filename))

        # Run the child script and capture its output
        try:
            result = subprocess.run('cd Measurement && python start.py ' + '--height ' + height, shell=True, capture_output=True, text=True)
            # Check if the command ran successfully
            if result.returncode == 0:
                measurements = result.stdout
                print(measurements)
            else:
                print('Error running the child script:')
                print(result.stderr)
        except Exception as e:
            print('Error:', e)

        # Regular expression pattern to find JSON-formatted text
        pattern = r'{.*}'

        # Search for the pattern in the text
        match = re.search(pattern, measurements)

        if match:
            # Extract the matched JSON-formatted text
            measurements_json = match.group(0)
            
            # Print the extracted JSON-formatted text
            print("Extracted JSON-formatted measurements:")
            print(measurements_json)
        else:
            print("No JSON-formatted measurements found in the text.")

        filename, extension = os.path.splitext(model_filename)
        obj = filename + '.obj'
        obj_url = "https://3.83.96.213/measure/" + obj
        return jsonify({'message': '3D body reconstruction achived successfully', 'obj_url': obj_url, 'measurements': json.loads(measurements_json)})
    else:
        return jsonify({'error': 'File type not allowed. Please provide JPG file'})

# Endpoint for virtual try on
@app.route('/try-on', methods=['POST'])
def fullbody_vto():
    if 'model' not in request.files or 'garment' not in request.files:
        return jsonify({'error': 'Please provide two files'})

    model = request.files['model']
    garment = request.files['garment']
    category = request.args.get('category')

    if category == '0':
        model_type = "hd"
    else:
        model_type = "dc"

    if model.filename == '' or garment.filename == '':
        return jsonify({'error': 'Please provide two valid files'})

    if model and allowed_file(model.filename) and garment and allowed_file(garment.filename):
        model_filename = secure_filename(model.filename)
        garment_filename = secure_filename(garment.filename)
        result_filename = 'out_' + model_type + '_0.png'
        
        model.save(os.path.join(app.config['MODEL_UPLOAD_FOLDER'], model_filename))
        garment.save(os.path.join(app.config['GARMENT_UPLOAD_FOLDER'], garment_filename))
        activate_cmd = f'eval "$(conda shell.bash hook)" && conda activate server && '
	#subprocess.run(activate_cmd + 'cd ./OutfitFullBody/run && python run_ootd.py --model_path ../../images/model/' + model_filename + ' --cloth_path ../../images/garment/' + garment_filename + ' --scale 2.0 --sample 1 --category ' + category + ' --model_type ' + model_type, shell=True, check=True)
        subprocess.run(activate_cmd + 'cd ./OutfitFullBody/run && python run_ootd_origin.py --model_path ../../images/model/' + model_filename + ' --cloth_path ../../images/garment/' + garment_filename + ' --scale 2.0 --sample 1 --category ' + category + ' --model_type ' + model_type, shell=True, check=True)
  
        result_path = f"output/" + result_filename

	#result_url = "http://3.87.162.97/try-on/" + result_filename

        with open(result_path, 'rb') as file:
            image_bytes = file.read()
            # Convert image to base64
            base64_image = base64.b64encode(image_bytes).decode('utf-8')

        return jsonify({'message': 'virtual dressing achived successfully', 'result_url': "result_url", 'result': base64_image})
    else:
        return jsonify({'error': 'File type not allowed. Please provide two JPG files'})

if __name__ == '__main__':
    app.run(debug=True)
    app.run(host = "0.0.0.0", port=5000)
