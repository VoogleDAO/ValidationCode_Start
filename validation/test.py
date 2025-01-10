import requests
import json

def validate_endpoint():
    BASE_URL = "http://127.0.0.1:5000"
    VALIDATE_ENDPOINT = f"{BASE_URL}/validate"

    sample_data_list = [
        {
            "prompt": "What is the capital of France?",
            "uniqueID": 213,
            "responses": [
                {"response": "The capital of France is Paris.", "model": "GPT-3.5"},
                {"response": "Paris is the capital city of France.", "model": "GPT-4"}
            ],
            "chosen": 1,
            "time_taken": 11.001
        },
        {
            "prompt": "Who wrote 'Romeo and Juliet'?",
            "uniqueID": 214,
            "responses": [
                {"response": "William Shakespeare wrote 'Romeo and Juliet'.", "model": "GPT-3.5"},
                {"response": "Shakespeare is the author of 'Romeo and Juliet'.", "model": "BERT"}
            ],
            "chosen": 0,
            "time_taken": 11.001
        },
        {
            "prompt": "What's the largest planet in our solar system?",
            "uniqueID": 215,
            "responses": [
                {"response": "Jupiter is the largest planet in our solar system.", "model": "GPT-4"},
                {"response": "The largest planet in our solar system is Jupiter.", "model": "GPT-3.5"}
            ],
            "chosen": 0,
            "time_taken": 11.001
        },
        {
            "prompt": "What is the capital of France?",
            "uniqueID": 213,
            "responses": [
                {"response": "The capital of France is Paris.", "model": "GPT-3.5"},
                {"response": "Paris is the capital city of France.", "model": "GPT-4"}
            ],
            "chosen": 1,
            "time_taken": 11.001
        },
        {
            "prompt": "What's the largest planet in our solar system?",
            "uniqueID": 216,
            "responses": [
                {"response": "Jupiter is the largest planet in our solar system.", "model": "GPT-4"},
                {"response": "The largest planet in our solar system is Jupiter.", "model": "GPT-3.5"}
            ],
            "chosen": 1,
            "time_taken": 11.001
        },
        {
            "prompt": "What is the capital of France?",
            "uniqueID": 218,
            "responses": [
                {"response": "The capital of France is Paris.", "model": "GPT-3.5"},
                {"response": "Paris is the capital city of France.", "model": "GPT-4"}
            ],
            "chosen": 1,
            "time_taken": 11.001
            },
        ]


    response = requests.post(VALIDATE_ENDPOINT, json=sample_data_list)
    
    if response.status_code == 200:
        response_data = response.json()
        print("Validation successful. Response data:")
        print(json.dumps(response_data, indent=2))
        return True
    else:
        print(f"Validation failed. Status code: {response.status_code}")
        print("Response content:", response.text)
        return False

if __name__ == "__main__":
    validate_endpoint()
