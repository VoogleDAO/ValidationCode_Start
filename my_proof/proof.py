import json
import logging
import os
from typing import Dict, Any, List
from my_proof.models.proof_response import ProofResponse
from my_proof.checks import *

class Proof:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        logging.info(f"Config: {self.config}")
        self.proof_response = ProofResponse(dlp_id=config['dlp_id'])

    def generate(self) -> ProofResponse:
        print("Starting generate method")
        input_data = ''
        for input_filename in os.listdir(self.config['input_dir']):
            input_file = os.path.join(self.config['input_dir'], input_filename)
            if os.path.splitext(input_file)[1].lower() == '.zip':
                print(f"Reading file: {input_file}")
                with open(input_file, 'r') as f:
                    input_data = json.load(f)

        print(input_data)

        print("Calculating quality score...")
        qualityRes = Quality(input_data)
        print(f"Quality score: {qualityRes}")
        
        if qualityRes < 0.0:
            print("Quality check failed, setting valid=False")
            self.proof_response.valid = False
            self.proof_response.score = 0.0
            return self.proof_response

        print("Setting proof response values...")
        self.proof_response.score = qualityRes
        self.proof_response.ownership = 1.0
        self.proof_response.authenticity = 1.0
        self.proof_response.uniqueness = 1.0

        print(f"Final proof response: {self.proof_response.__dict__}")
        return self.proof_response

def Quality(data_list: List[Dict[str, Any]]) -> float:
    print("Starting Quality check")
    report = LocationHistoryValidator(max_speed_m_s=44.44)
    result = report.validate(data_list)
    print(f"Quality validation result: {result}")
    return result
