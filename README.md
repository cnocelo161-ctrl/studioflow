```
# StudioFlow

AI-powered architecture project processor that converts client intake into structured project plans.

---

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

``` 
## Environment Variables

Create a local .env file in the root directory:

```env
OPENAI_API_KEY=your_openai_api_key
N8N_BASE_URL=https://robertnocelo.app.n8n.cloud
N8N_API_KEY=your_n8n_api_key
```
## Run
```bash
cp input.template.json input.json
python main.py

