import os, requests
from dotenv import load_dotenv
load_dotenv()
token = os.getenv("HUGGINGFACE_API_TOKEN")
if not token:
    raise SystemExit("Set HUGGINGFACE_API_TOKEN env var first.")
headers = {"Authorization": f"Bearer {token}"}
r = requests.post(
    "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5",
    headers=headers,
    json={"inputs":"a funny dog dancing in the rain"},
    timeout=120,
)
print(r.status_code)
print(r.headers.get("content-type"))
print(r.text[:1000])
