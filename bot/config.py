import logging
import google.generativeai as genai

# =============================================
TELEGRAM_TOKEN = "8607632393:AAHHjpT_qv66HerNzQHarFT51TGIoqVr_wU"
GEMINI_API_KEY = "AIzaSyD1qDLyDIFDSeibWPsSAOWnh_y3XH9-bbo"
RESULTS_FILE   = "candidates.json"
# =============================================

MODELS = ["gemini-1.5-flash-8b", "gemini-1.5-flash", "gemini-1.0-pro"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

genai.configure(api_key=GEMINI_API_KEY)
