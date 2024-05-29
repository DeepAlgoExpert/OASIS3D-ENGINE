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

def save_base64_image(base64_string, filename):
    try:
        # Extract base64 image data
        _, base64_data = base64_string.split(',', 1)
        
        # Decode base64 data
        image_data = base64.b64decode(base64_data)
        
        # Write image data to file
        with open(filename, 'wb') as f:
            f.write(image_data)
        
        print(f"Image saved as {filename}")
        return True
    except Exception as e:
        print(f"Error saving image: {e}")
        return False

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
    model = request.json['model']
    height = request.json['height']

    model_image_path = 'Measurement/3d_body/inputs'
    output_smplx_path = 'Measurement/3d_body/results'
    output_smpl_path = 'Measurement/output'
    delete_files_in_directory(model_image_path)
    delete_files_in_directory(output_smplx_path)
    delete_files_in_directory(output_smpl_path)
    
    if model:
        model_filename = "model.jpg"
        model_path= os.path.join(app.config['MEASURE_MODEL_UPLOAD_FOLDER'], model_filename)
        save_base64_image(model, model_path)

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
        obj_url = "https://54.175.70.202/measure/" + obj
        return jsonify({'message': '3D body reconstruction achived successfully', 'obj_url': obj_url, 'measurements': json.loads(measurements_json)})
    else:
        return jsonify({'error': 'File type not allowed. Please provide JPG file'})

# Endpoint for virtual try on
@app.route('/try-on', methods=['POST'])
def fullbody_vto():
    #if 'model' not in request.files or 'garment' not in request.files:
        #return jsonify({'error': 'Please provide two files'})
    print('starting...')
    model = request.json['model']
    model_type = request.json['modelType']
    garment = request.json['garment']
    garment_type = request.json['garmentType']

    print('garment_type:', garment_type)

    if garment_type=="Upper-body":
        category = '0'
    elif garment_type=="Lower-body":
        category = '1'
    else:
        category = '2'

    if model and garment:

        model_filename = "model.jpg"
        model_path= os.path.join(app.config['MODEL_UPLOAD_FOLDER'], model_filename)
        save_base64_image(model, model_path)

        garment_filename = "garment.jpg"
        garment_path= os.path.join(app.config['GARMENT_UPLOAD_FOLDER'], garment_filename)
        save_base64_image(garment, garment_path)

        activate_cmd = f'eval "$(conda shell.bash hook)" && conda activate server && '

        if garment_type=="Upper-body":
            result_filename = 'out_hd_0.png'
            subprocess.run(activate_cmd + 'cd ./OutfitFullBody/run && python run_ootd_origin.py --model_path ../../images/model/' + model_filename + 
            ' --cloth_path ../../images/garment/' + garment_filename + ' --scale 2.0 --sample 1', shell=True, check=True)
        else:
            result_filename = 'out_dc_0.png'
            subprocess.run(activate_cmd + 'cd ./OutfitFullBody/run && python run_ootd_origin.py --model_path ../../images/model/' + model_filename + 
            ' --cloth_path ../../images/garment/' + garment_filename + ' --scale 2.0 --sample 1 --category ' + category + 
            ' --model_type dc', shell=True, check=True) 

        result_path = f"output/" + result_filename

	#result_url = "http://3.87.162.97/try-on/" + result_filename

        with open(result_path, 'rb') as file:
            image_bytes = file.read()
            # Convert image to base64
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
        return base64_image
            
        return jsonify({'message': 'virtual dressing achived successfully', 'result_url': "result_url", 'result': base64_image})
    else:
        return jsonify({'error': 'File type not allowed. Please provide two JPG files'})

if __name__ == '__main__':
    app.run(debug=True)
    app.run(host = "0.0.0.0", port=5000)
