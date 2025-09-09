import os
from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
ENV_FILE = os.path.join(ROOT_DIR, ".env")

load_dotenv(dotenv_path=ENV_FILE)

# Settings global
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_ENGINE = os.getenv('AZURE_OPENAI_ENGINE')
