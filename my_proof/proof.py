import json
import logging
import os
from typing import Dict, Any, List, Union
from my_proof.models.proof_response import ProofResponse
from .checks import LocationHistoryValidator
from .android_validator import AndroidLocationHistoryValidator

class Proof:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        logging.info(f"Config: {self.config}")
        self.proof_response = ProofResponse(dlp_id=config['dlp_id'])

    def generate(self) -> ProofResponse:
        print("Starting generate method")
        input_data = None
        for input_filename in os.listdir(self.config['input_dir']):
            input_file = os.path.join(self.config['input_dir'], input_filename)
            if os.path.splitext(input_file)[1].lower() == '.zip':
                print(f"Reading file: {input_file}")
                # Read as regular JSON file despite .zip extension
                with open(input_file, 'r', encoding='utf-8') as f:
                    input_data = json.load(f)

        if input_data is None:
            print("No valid JSON data found")
            self.proof_response.valid = False
            self.proof_response.score = 0.0
            return self.proof_response

        print("Calculating quality score...")
        qualityRes = Quality(input_data)
        print(f"Quality score: {qualityRes}")
        
        # Initialize proof response values
        self.proof_response.score = qualityRes
        self.proof_response.ownership = 1.0
        self.proof_response.authenticity = 1.0
        self.proof_response.uniqueness = 1.0
        self.proof_response.valid = True  # Set valid to True by default
        
        if qualityRes < 0.0:
            print("Quality check failed, setting valid=False")
            self.proof_response.valid = False
            self.proof_response.score = 0.0
            return self.proof_response

        print(f"Final proof response: {self.proof_response.__dict__}")
        return self.proof_response

def Quality(data_list: Union[List[Dict[str, Any]], Dict[str, Any]]) -> float:
    print("Starting Quality check")

    try:
        # Debug prints
        print(f"Type of data_list: {type(data_list)}")
        if isinstance(data_list, dict):
            print(f"Keys in data_list: {list(data_list.keys())}")
        
        # Detect data format
        if isinstance(data_list, dict) and "semanticSegments" in data_list:
            # Android format
            print("Detected Android format data")
            validator = AndroidLocationHistoryValidator(max_speed_m_s=44.44)
            # Extract the list from semanticSegments
            segments = data_list["semanticSegments"]
            result = validator.validate(segments)
        elif isinstance(data_list, list):
            # iOS format
            print("Detected iOS format data")
            validator = LocationHistoryValidator(max_speed_m_s=44.44)
            result = validator.validate(data_list)
        else:
            print("Error: Unrecognized data format")
            print("Data must be either:")
            print("1. A dictionary containing 'semanticSegments' key (Android)")
            print("2. A list of location entries (iOS)")
            return -1
        
        print(f"Quality validation result: {result}")
        return result
    except Exception as e:
        print(f"Error in Quality check: {e}")
        return -1
