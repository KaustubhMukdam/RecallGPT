import requests
import json

class LLMInterface:
    def __init__(self, model_name="qwen2.5-coder:1.5b"):
        self.api_url = 'http://localhost:11434/api/generate'
        self.model_name = model_name

    def generate(self, prompt):
        payload = {'model': self.model_name, 'prompt': prompt}
        response = requests.post(self.api_url, json=payload, stream=True)
        full_response = ""
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8'))
                    chunk = data.get('response', '')
                    full_response += chunk
                except Exception as e:
                    print(f"Error decoding chunk: {e}")
        return full_response
