from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from validation import validate
from aws_interaction import upload_json_to_s3
from datetime import datetime

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello_world():
    return render_template('index.html', message="Hello, World!")

@app.route('/status')
def api_status():
    return jsonify({"status": "API is running"})

@app.route('/validate', methods=['POST'])
def validate_route():
    data = request.json
    if validate(data):
        now = datetime.now()
        timestamp = now.timestamp()
        #file_url = upload_json_to_s3('vanatensorpoisondata', f'{timestamp}.json', data)
        #return jsonify({ 
        #     "file_url": file_url,
        #    "status": "success"
        #})
        
    else:
        return jsonify({"status": "error"})

if __name__ == '__main__':
    app.run(debug=True)