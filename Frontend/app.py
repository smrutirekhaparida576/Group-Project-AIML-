import streamlit as st
from PIL import Image
from io import BytesIO
import base64
import os
import sys
import time
from urllib.parse import quote

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from health_score import calculate_health_score
from model.predict import predict_food, predict_serving_size
from nutrition import get_available_food_names, get_nutrition_data
from recommendation import generate_recommendations

MIN_FOOD_CONFIDENCE = float(os.getenv("MIN_FOOD_CONFIDENCE", "40"))
MAX_ANALYSIS_IMAGE_SIZE = int(os.getenv("MAX_ANALYSIS_IMAGE_SIZE", "640"))

FAVICON_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="bg" x1="8" x2="56" y1="8" y2="56" gradientUnits="userSpaceOnUse">
      <stop stop-color="#8CC0EB"/>
      <stop offset="1" stop-color="#BFDDF0"/>
    </linearGradient>
  </defs>
  <rect width="64" height="64" rx="18" fill="url(#bg)"/>
  <path d="M16 33h32v3c0 8.3-6.7 15-15 15h-2c-8.3 0-15-6.7-15-15v-3Z" fill="#FFF9D2"/>
  <path d="M20 29c1-8 6.2-14 12-14s11 6 12 14H20Z" fill="#FFEBCC"/>
  <path d="M21 37h22" stroke="#5d9fd7" stroke-width="4" stroke-linecap="round"/>
  <circle cx="25" cy="25" r="3" fill="#8CC0EB"/>
  <circle cx="33" cy="22" r="3" fill="#8CC0EB"/>
  <circle cx="41" cy="25" r="3" fill="#8CC0EB"/>
</svg>
"""

FAVICON_DATA_URL = f"data:image/svg+xml,{quote(FAVICON_SVG)}"

st.set_page_config(
    page_title="CalCount AI - Food Calorie Estimator",
    page_icon= FAVICON_DATA_URL ,
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "result" not in st.session_state:
    st.session_state.result = None
if "uploaded_image_bytes" not in st.session_state:
    st.session_state.uploaded_image_bytes = None
if "uploaded_image_name" not in st.session_state:
    st.session_state.uploaded_image_name = None
if "upload_key" not in st.session_state:
    st.session_state.upload_key = 0
if "serving_grams" not in st.session_state:
    st.session_state.serving_grams = 100


def image_to_data_url(image_path):
    if not os.path.exists(image_path):
        return ""

    extension = os.path.splitext(image_path)[1].lower()
    mime_type = "image/png" if extension == ".png" else "image/jpeg"

    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("ascii")

    return f"data:{mime_type};base64,{encoded_image}"


SAMPLE_RESULTS = [
    {
        "name": "Rainbow Salad Bowl",
        "calories": "420 kcal",
        "protein": "24 g",
        "carbs": "52 g",
        "fat": "14 g",
        "score": "92",
        "category": "Healthy meal",
    },
    {
        "name": "Grilled Paneer Plate",
        "calories": "510 kcal",
        "protein": "31 g",
        "carbs": "38 g",
        "fat": "22 g",
        "score": "88",
        "category": "Balanced meal",
    },
    {
        "name": "Avocado Toast",
        "calories": "360 kcal",
        "protein": "13 g",
        "carbs": "41 g",
        "fat": "18 g",
        "score": "90",
        "category": "Healthy snack",
    },
]

BIRYANI_VARIANTS = [
    "Biryani",
    "Veg Biryani",
    "Chicken Biryani",
    "Mutton Biryani",
    "Egg Biryani",
]


def build_non_food_result(prediction=None):
    prediction = prediction or {}
    confidence_value = float(prediction.get("confidence_value", 0) or 0)
    predicted_food = prediction.get("food", "")
    return {
        "name": "No food detected",
        "predicted_food": predicted_food,
        "confidence": prediction.get("confidence", "--"),
        "confidence_value": confidence_value,
        "top_predictions": prediction.get("top_predictions", []),
        "calories": "--",
        "protein": "--",
        "carbs": "--",
        "fat": "--",
        "sugar": "--",
        "fiber": "--",
        "score": "--",
        "category": "Not a food image",
        "recommendation": "Please upload a clear image of a food item or meal, or choose the correct food name manually.",
        "advice": "Nutrition details are shown automatically only when the model is confident that the image contains food.",
        "suggestion": "If this is food, use the correction option above the result panel.",
        "alternatives": "--",
        "nutrition_source": "Not applicable",
        "nutrition_note": f"No nutrition was generated because food confidence is below {MIN_FOOD_CONFIDENCE:.0f}%.",
        "is_food": False,
    }


def build_result(food_name, prediction, serving_grams=100, serving_prediction=None):
    serving_prediction = serving_prediction or {}
    nutrition_data = get_nutrition_data(food_name)
    multiplier = float(serving_grams) / 100
    for field in ["calories", "protein", "carbs", "fat", "sugar", "fiber"]:
        nutrition_data[field] = round(float(nutrition_data[field]) * multiplier, 2)

    serving_source = serving_prediction.get("serving_source")
    if serving_source:
        nutrition_note = (
            f"Serving size estimated at {serving_grams}g using {serving_source}. "
            "Nutrition loaded from nutrition.csv; base values are per 100g."
        )
    else:
        nutrition_note = f"Nutrition loaded from nutrition.csv. Base values are per 100g; shown for {serving_grams}g."

    health_data = calculate_health_score(nutrition_data)
    recommendation_data = generate_recommendations(nutrition_data, health_data)
    confidence_value = float(prediction.get("confidence_value", 0) or 0)

    if confidence_value and confidence_value < 50:
        nutrition_note = f"Low-confidence prediction. {nutrition_note}"

    return {
        "name": food_name,
        "confidence": prediction.get("confidence", "--"),
        "confidence_value": confidence_value,
        "top_predictions": prediction.get("top_predictions", []),
        "calories": f"{nutrition_data['calories']} kcal",
        "protein": f"{nutrition_data['protein']} g",
        "carbs": f"{nutrition_data['carbs']} g",
        "fat": f"{nutrition_data['fat']} g",
        "sugar": f"{nutrition_data['sugar']} g",
        "fiber": f"{nutrition_data['fiber']} g",
        "score": str(health_data["health_score"]),
        "category": health_data["category"],
        "recommendation": health_data["recommendation"],
        "advice": recommendation_data["advice"],
        "suggestion": recommendation_data["suggestion"],
        "alternatives": ", ".join(recommendation_data["healthy_alternatives"]),
        "nutrition_source": nutrition_data.get("source", "Local nutrition CSV"),
        "nutrition_note": nutrition_note,
        "serving_grams": serving_grams,
        "serving_confidence": serving_prediction.get("serving_confidence", "--"),
        "serving_food": serving_prediction.get("serving_food", food_name),
        "serving_area_percent": serving_prediction.get("serving_area_percent"),
        "serving_source": serving_source,
        "is_food": True,
    }


def analyze_uploaded_food(uploaded_file):
    uploaded_file.seek(0)
    food_image = Image.open(uploaded_file).convert("RGB")
    food_image.thumbnail((MAX_ANALYSIS_IMAGE_SIZE, MAX_ANALYSIS_IMAGE_SIZE), Image.Resampling.LANCZOS)

    try:
        prediction = predict_food(food_image)
    except ValueError as error:
        if "no class prediction" in str(error).lower():
            return build_non_food_result()
        raise

    confidence_value = float(prediction.get("confidence_value", 0) or 0)

    if confidence_value < MIN_FOOD_CONFIDENCE:
        return build_non_food_result(prediction)

    try:
        serving_prediction = predict_serving_size(food_image, prediction["food"])
        serving_grams = serving_prediction["serving_grams"]
    except ValueError:
        serving_prediction = None
        serving_grams = st.session_state.serving_grams

    st.session_state.serving_grams = int(serving_grams)
    return build_result(prediction["food"], prediction, serving_grams, serving_prediction)

mode_class = "dark-mode" if st.session_state.dark_mode else "light-mode"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');
@import url('https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css');
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css');

:root {{
    --cream: #FFF9D2;
    --peach: #FFEBCC;
    --mint: #BFDDF0;
    --blue: #8CC0EB;
    --ink: #253244;
    --muted: #69798d;
    --surface: rgba(255, 255, 255, 0.68);
    --surface-strong: rgba(255, 255, 255, 0.9);
    --border: rgba(255, 255, 255, 0.7);
    --shadow: 0 24px 70px rgba(92, 132, 170, 0.22);
}}

html {{ scroll-behavior: smooth; }}
html, body {{ max-width: 100%; overflow-x: hidden; }}

.stApp {{
    font-family: 'Manrope', sans-serif;
    color: var(--ink);
    background:
        radial-gradient(circle at 14% 8%, rgba(255, 235, 204, 0.96), transparent 34%),
        radial-gradient(circle at 84% 10%, rgba(191, 221, 240, 0.95), transparent 32%),
        linear-gradient(135deg, var(--cream), #fffdf1 45%, var(--mint));
}}

.stApp.dark-mode {{
    --ink: #f6fbff;
    --muted: #bfd0de;
    --surface: rgba(17, 30, 45, 0.66);
    --surface-strong: rgba(20, 34, 50, 0.92);
    --border: rgba(255, 255, 255, 0.14);
    --shadow: 0 24px 70px rgba(3, 11, 20, 0.38);
    background:
        radial-gradient(circle at 16% 10%, rgba(140, 192, 235, 0.24), transparent 34%),
        radial-gradient(circle at 86% 14%, rgba(255, 235, 204, 0.16), transparent 28%),
        linear-gradient(135deg, #0f1c29, #152b3d 45%, #1c4055);
}}

.block-container {{ max-width: 100% !important; padding: 0 !important; overflow-x: hidden; }}
#MainMenu, footer, header {{ visibility: hidden; }}
.stAppHeader, [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] {{
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
}}
.stDeployButton {{ display: none; }}
[data-testid="stHorizontalBlock"] {{
    max-width: 1120px;
    width: calc(100% - 40px);
    margin-left: auto;
    margin-right: auto;
    align-items: stretch;
}}

.navbar-glass {{
    position: sticky;
    top: 0;
    z-index: 999;
    margin: 0 auto;
    padding: 14px clamp(18px, 5vw, 72px);
    background: rgba(255, 255, 255, 0.46);
    backdrop-filter: blur(22px);
    border-bottom: 1px solid var(--border);
    box-shadow: 0 12px 40px rgba(62, 111, 154, 0.12);
}}

.dark-mode .navbar-glass {{ background: rgba(13, 26, 38, 0.68); }}
.navbar-toggler {{
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 9px 11px;
    background: var(--surface-strong);
    box-shadow: 0 10px 24px rgba(92, 132, 170, 0.14);
}}
.navbar-toggler:focus {{ box-shadow: 0 0 0 3px rgba(140, 192, 235, .45); }}
.nav-menu-toggle {{ display: none; }}
.navbar-toggler-icon {{
    background-image: none;
    width: 24px;
    height: 18px;
    position: relative;
}}
.navbar-toggler-icon::before,
.navbar-toggler-icon::after,
.navbar-toggler-icon {{
    border-top: 2px solid var(--ink);
}}
.navbar-toggler-icon::before,
.navbar-toggler-icon::after {{
    content: "";
    position: absolute;
    left: 0;
    width: 24px;
}}
.navbar-toggler-icon::before {{ top: 7px; }}
.navbar-toggler-icon::after {{ top: 16px; }}

.brand {{ display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 1.25rem; color: var(--ink); }}
.logo-mark {{
    display: grid; place-items: center; width: 42px; height: 42px;
    color: #fff; border-radius: 16px;
    background: linear-gradient(135deg, var(--blue), #66a9df);
    box-shadow: 0 12px 26px rgba(72, 145, 210, 0.28);
}}
.nav-link {{ color: var(--muted) !important; font-weight: 800; border-radius: 999px; padding: 10px 14px !important; }}
.nav-link:hover {{ color: var(--ink) !important; background: rgba(255,255,255,.5); }}

.section {{ position: relative; padding: 88px clamp(20px, 5vw, 80px); overflow: hidden; }}
.hero {{ min-height: calc(100vh - 70px); display: flex; align-items: center; }}
.max-wrap {{ max-width: 1180px; margin: 0 auto; width: 100%; }}
.eyebrow {{
    display: inline-flex; align-items: center; gap: 8px; width: fit-content;
    margin-bottom: 18px; padding: 9px 14px; color: #3f82b8;
    border: 1px solid var(--border); border-radius: 999px;
    background: var(--surface); backdrop-filter: blur(14px);
    font-size: .88rem; font-weight: 800;
}}
.hero h1 {{ font-size: clamp(3.25rem, 6vw, 5.85rem); line-height: 1.03; letter-spacing: 0; font-weight: 800; color: var(--ink); overflow-wrap: anywhere; }}
.section-title {{ font-size: clamp(2.15rem, 3.6vw, 3.8rem); line-height: 1.05; letter-spacing: 0; font-weight: 800; color: var(--ink); }}
.lead-copy {{ color: var(--muted); line-height: 1.75; font-size: clamp(1rem, 2vw, 1.22rem); overflow-wrap: anywhere; }}

.btn-soft-primary, .btn-soft-secondary {{
    display: inline-flex; align-items: center; gap: 10px; min-height: 54px;
    padding: 0 22px; border-radius: 999px; font-weight: 800; text-decoration: none;
    transition: transform .25s ease, box-shadow .25s ease;
}}
.btn-soft-primary {{ color: #fff !important; background: linear-gradient(135deg, #7db9e8, #5da4df); box-shadow: 0 18px 34px rgba(86, 158, 219, .32); }}
.btn-soft-secondary {{ color: var(--ink) !important; background: var(--surface-strong); border: 1px solid var(--border); }}
.btn-soft-primary:hover, .btn-soft-secondary:hover {{ transform: translateY(-3px); }}

.blob {{ position: absolute; z-index: 0; width: 260px; height: 260px; border-radius: 50%; filter: blur(5px); opacity: .62; animation: floatBlob 8s ease-in-out infinite; }}
.blob-one {{ top: 15%; left: -7%; background: var(--peach); }}
.blob-two {{ right: -5%; top: 14%; background: var(--blue); animation-delay: -3s; }}
.blob-three {{ right: 28%; bottom: 10%; background: var(--mint); animation-delay: -5s; }}

.glass-card {{ border: 1px solid var(--border); background: var(--surface); box-shadow: var(--shadow); backdrop-filter: blur(22px); border-radius: 28px; }}
.phone-card {{ position: relative; min-height: 540px; display: grid; place-items: center; overflow: hidden; }}
.scan-ring {{ width: min(78%, 430px); aspect-ratio: 1; padding: 14px; border-radius: 50%; background: conic-gradient(from 120deg, var(--blue), var(--cream), var(--peach), var(--mint), var(--blue)); animation: slowSpin 12s linear infinite; }}
.scan-ring img {{ width: 100%; height: 100%; object-fit: cover; border: 12px solid rgba(255,255,255,.72); border-radius: 50%; }}
.scan-line {{ position: absolute; left: 17%; right: 17%; height: 3px; background: linear-gradient(90deg, transparent, #fff, transparent); box-shadow: 0 0 28px rgba(255,255,255,.95); animation: scan 3s ease-in-out infinite; }}
.mini-card {{ position: absolute; display: flex; align-items: center; gap: 10px; padding: 14px 18px; border-radius: 20px; background: rgba(255,255,255,.78); box-shadow: 0 18px 38px rgba(70,122,164,.22); font-weight: 800; color: var(--ink); }}
.dark-mode .mini-card {{ background: rgba(20,34,50,.84); }}
.calories {{ top: 18%; left: 5%; }} .score {{ right: 5%; bottom: 17%; }}

.upload-box {{ border: 2px dashed rgba(76,143,199,.52); border-radius: 24px; min-height: 300px; display: grid; place-items: center; text-align: center; background: rgba(255,255,255,.42); transition: transform .25s ease, border .25s ease; }}
.upload-box:hover {{ transform: translateY(-3px); border-color: var(--blue); }}
.upload-icon {{ color: #5da4df; font-size: 4rem; animation: uploadFloat 2.4s ease-in-out infinite; }}
.stFileUploader label {{ color: var(--ink) !important; font-weight: 800; }}
.stFileUploader section {{
    position: relative;
    min-height: 255px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    border: 2px dashed rgba(76,143,199,.52);
    background: rgba(255,255,255,.42);
    border-radius: 24px;
    padding: 28px 22px;
    transition: transform .25s ease, border .25s ease;
    cursor: pointer;
}}
.stFileUploader, .stFileUploader section {{ width: 100%; }}
.stFileUploader section:hover {{ transform: translateY(-3px); border-color: var(--blue); }}
.stFileUploader [data-testid="stFileUploaderDropzoneInstructions"] {{
    display: block !important;
    color: var(--ink);
    font-weight: 800;
    width: 100%;
    text-align: center;
    margin: 0 auto;
}}
.stFileUploader [data-testid="stFileUploaderDropzoneInstructions"]::before {{
    content: "\\f0ee";
    display: block;
    margin: 0 auto 26px;
    color: #5da4df;
    font: var(--fa-font-solid);
    font-size: 4.55rem;
    line-height: 1;
    animation: uploadFloat 2.4s ease-in-out infinite;
}}
.stFileUploader [data-testid="stFileUploaderDropzoneInstructions"] > *,
.stFileUploader [data-testid="stFileUploaderDropzoneInstructions"] span,
.stFileUploader [data-testid="stFileUploaderDropzoneInstructions"] small {{
    display: none !important;
}}
.stFileUploader [data-testid="stFileUploaderDropzoneInstructions"]::after {{
    content: "Upload a food image\\A JPG, JPEG, PNG, or WebP\\A up to 200 MB";
    display: block;
    color: var(--ink);
    font-size: 1.35rem;
    font-weight: 800;
    line-height: 1.5;
    white-space: pre-line;
    max-width: 290px;
    margin: 0 auto;
}}
.stFileUploader section button {{
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    opacity: 0;
    cursor: pointer;
}}
.stFileUploader [data-testid="stFileUploaderFile"] {{
    background: var(--surface-strong);
    border: 1px solid var(--border);
    color: var(--ink);
}}
.stButton button {{
    min-height: 50px;
    width: 100%;
    border-radius: 999px;
    font-weight: 800;
    border: 0;
    background: linear-gradient(135deg, #7db9e8, #5da4df);
    box-shadow: 0 16px 30px rgba(86, 158, 219, .25);
}}

.nutrition-card, .feature-card, .testimonial-card, .stat-card {{
    height: 100%; border: 1px solid var(--border); border-radius: 22px;
    background: rgba(255,255,255,.52); padding: 22px;
    transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease, background .25s ease;
}}
.dark-mode .nutrition-card, .dark-mode .testimonial-card, .dark-mode .stat-card {{ background: rgba(255,255,255,.06); }}
.nutrition-card:hover, .feature-card:hover, .testimonial-card:hover {{
    transform: translateY(-7px);
    border-color: rgba(93, 164, 223, .58);
    box-shadow: 0 26px 58px rgba(72, 145, 210, .24);
}}
.nutrition-card i, .feature-card i {{ color: #5da4df; font-size: 1.65rem; }}
.feature-card i {{ transition: transform .25s ease, color .25s ease; }}
.feature-card:hover i {{ color: #3278ad; transform: scale(1.12) rotate(-4deg); }}
.card-label {{ color: var(--muted); font-weight: 800; margin: 14px 0 5px; }}
.card-value {{ font-size: 1.7rem; font-weight: 800; color: var(--ink); overflow-wrap: anywhere; }}
.health-badge {{ display: inline-flex; padding: 9px 13px; color: #3278ad; border-radius: 999px; background: rgba(191,221,240,.58); font-size: .9rem; font-weight: 800; }}
.result-panel {{ overflow: hidden; width: 100%; max-width: 980px; margin: 0 auto; }}
.result-grid {{ display: grid; gap: 12px; }}
.summary-grid {{ display: grid; grid-template-columns: 1.35fr 1fr 1fr 1fr; gap: 12px; }}
.metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; }}
.result-panel .nutrition-card {{ min-height: 0; padding: 15px; border-radius: 18px; }}
.result-panel .nutrition-card i {{ font-size: 1.15rem; }}
.result-panel .card-label {{ margin: 8px 0 3px; font-size: .76rem; }}
.result-panel .card-value {{ font-size: clamp(1rem, 2vw, 1.35rem); line-height: 1.15; }}
.advice-card .lead-copy {{ line-height: 1.45; font-size: .92rem !important; }}
.result-notes-wrap {{ grid-column: 1 / -1; width: 100%; margin: 0; display: grid; gap: 4px; }}
.result-note {{ color: var(--muted); line-height: 1.45; font-size: .9rem; margin: 0; }}
.feature-card:nth-child(odd) {{ background: linear-gradient(145deg, rgba(255,249,210,.78), rgba(191,221,240,.62)); }}
.feature-card:nth-child(even) {{ background: linear-gradient(145deg, rgba(255,235,204,.78), rgba(140,192,235,.55)); }}
.dark-mode .feature-card {{ background: var(--surface); }}
.stat-card {{ display: grid; place-items: center; min-height: 150px; text-align: center; }}
.stat-number {{ color: #4f9bd6; font-size: clamp(2.1rem, 4vw, 3.4rem); font-weight: 800; }}
.testimonial-card img {{
    width: 64px; height: 64px; object-fit: cover; border-radius: 50%;
    border: 4px solid rgba(255,255,255,.74);
    transition: transform .25s ease, border-color .25s ease;
}}
.testimonial-card:hover img {{ transform: scale(1.08); border-color: rgba(93, 164, 223, .72); }}
.stars {{ color: #f4b84d; letter-spacing: 0; transition: filter .25s ease; }}
.testimonial-card:hover .stars {{ filter: drop-shadow(0 3px 8px rgba(244, 184, 77, .38)); }}
.footer-zone {{ padding: 70px clamp(20px, 5vw, 80px) 28px; background: rgba(255,255,255,.34); border-top: 1px solid var(--border); }}
.dark-mode .footer-zone {{ background: rgba(6,17,28,.3); }}
.contact-note {{ color: var(--muted); line-height: 1.7; margin-bottom: 18px; }}
.social-link {{ width: 42px; height: 42px; display: inline-grid; place-items: center; margin-right: 8px; border-radius: 50%; color: var(--muted); background: var(--surface); text-decoration: none; }}
.fade-in {{ animation: fadeUp .85s ease both; }}

@keyframes fadeUp {{ from {{ opacity: 0; transform: translateY(28px); }} to {{ opacity: 1; transform: translateY(0); }} }}
@keyframes floatBlob {{ 50% {{ transform: translate3d(18px, -22px, 0) scale(1.08); }} }}
@keyframes slowSpin {{ to {{ transform: rotate(360deg); }} }}
@keyframes scan {{ 0%,100% {{ top: 23%; }} 50% {{ top: 77%; }} }}
@keyframes uploadFloat {{ 50% {{ transform: translateY(-10px); }} }}

@media (min-width: 992px) {{
    .hero .row {{ min-height: 620px; }}
    .navbar-collapse {{ display: flex !important; }}
    .result-panel {{ margin-bottom: 34px; }}
    .stFileUploader section {{ max-width: 430px; margin-left: auto; margin-right: auto; }}
}}

@media (max-width: 900px) {{
    [data-testid="stHorizontalBlock"] {{
        width: calc(100% - 28px);
        gap: 22px !important;
    }}
    [data-testid="column"] {{
        min-width: 100% !important;
        width: 100% !important;
        flex: 1 1 100% !important;
    }}
    .result-panel {{
        max-width: 100%;
    }}
    .summary-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }}
    .metric-grid {{
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }}
}}

@media (max-width: 991px) {{
    [data-testid="stHorizontalBlock"] {{ width: calc(100% - 28px); }}
    .navbar-glass {{ padding: 10px 16px; }}
    .phone-card {{ min-height: 430px; }}
    .section {{ padding: 68px 18px; }}
    .hero {{ min-height: auto; padding-top: 56px; }}
    .hero h1 {{ font-size: clamp(2.6rem, 10vw, 4.6rem); }}
    .navbar-collapse {{ display: none !important; }}
    .nav-menu-toggle:checked ~ .navbar-collapse {{ display: block !important; }}
    .navbar-collapse {{
        margin-top: 12px;
        padding: 10px;
        border: 1px solid var(--border);
        border-radius: 18px;
        background: var(--surface-strong);
    }}
}}

@media (max-width: 720px) {{
    .section {{
        padding: 54px 16px;
    }}
    .hero {{
        padding-top: 38px;
    }}
    .hero h1 {{
        font-size: clamp(2.35rem, 11vw, 3.7rem);
    }}
    .section-title {{
        font-size: clamp(1.9rem, 8vw, 2.8rem);
    }}
    .phone-card {{
        min-height: 340px;
    }}
    .summary-grid,
    .metric-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }}
    .result-panel .nutrition-card {{
        padding: 14px;
    }}
    .advice-card {{
        grid-column: 1 / -1;
    }}
}}

@media (max-width: 576px) {{
    [data-testid="stHorizontalBlock"] {{
        width: calc(100% - 20px);
        gap: 18px !important;
    }}
    [data-testid="column"] {{
        min-width: 100% !important;
        width: 100% !important;
        flex: 1 1 100% !important;
    }}
    .navbar-glass {{ padding: 9px 12px; }}
    .brand {{ font-size: 1rem; gap: 8px; }}
    .logo-mark {{ width: 36px; height: 36px; border-radius: 12px; }}
    .nav-link {{ padding: 9px 10px !important; }}
    .section {{ padding: 42px 12px; }}
    .hero {{ padding-top: 34px; text-align: left; }}
    .hero h1 {{ font-size: clamp(2.35rem, 12vw, 3.35rem); line-height: 1.07; }}
    .section-title {{ font-size: clamp(1.85rem, 9vw, 2.6rem); }}
    .lead-copy {{ font-size: .98rem; line-height: 1.55; }}
    .eyebrow {{ font-size: .78rem; padding: 7px 10px; margin-bottom: 12px; }}
    .btn-soft-primary, .btn-soft-secondary {{
        width: 100%;
        justify-content: center;
        min-height: 48px;
        padding: 0 16px;
    }}
    .phone-card {{ min-height: 300px; border-radius: 20px; margin-top: 8px; }}
    .scan-ring {{ width: min(74%, 260px); padding: 9px; }}
    .scan-ring img {{ border-width: 8px; }}
    .mini-card {{ padding: 9px 11px; font-size: .8rem; border-radius: 14px; }}
    .calories {{ top: 10%; left: 4%; }}
    .score {{ right: 4%; bottom: 10%; }}
    .blob {{ display: none; }}
    .glass-card {{ border-radius: 20px; box-shadow: 0 16px 42px rgba(92, 132, 170, 0.18); }}
    .upload-box {{ min-height: 190px; border-radius: 18px; padding: 18px 12px; }}
    .upload-box h3 {{ font-size: 1.2rem; }}
    .upload-icon {{ font-size: 2.6rem; }}
    .stFileUploader section {{ min-height: 220px; border-radius: 18px; padding: 22px 16px; }}
    .stFileUploader [data-testid="stFileUploaderDropzoneInstructions"]::before {{ margin-bottom: 22px; font-size: 4rem; }}
    .nutrition-card, .feature-card, .testimonial-card, .stat-card {{
        border-radius: 18px;
        padding: 16px;
    }}
    .result-panel {{ padding: 16px !important; }}
    .result-panel .nutrition-card {{ min-height: auto; }}
    .summary-grid {{ grid-template-columns: 1fr; }}
    .metric-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    .nutrition-card:hover, .feature-card:hover, .testimonial-card:hover {{ transform: none; }}
    .nutrition-card i, .feature-card i {{ font-size: 1.25rem; }}
    .card-label {{ margin: 9px 0 4px; font-size: .78rem; }}
    .card-value {{ font-size: clamp(1.08rem, 6vw, 1.38rem); line-height: 1.16; }}
    .health-badge {{ width: 100%; justify-content: center; font-size: .82rem; }}
    .stat-card {{ min-height: 112px; }}
    .testimonial-card {{ flex-direction: column; }}
    .footer-zone {{ padding: 46px 14px 22px; }}
}}

@media (max-width: 390px) {{
    .brand span:last-child {{
        font-size: .92rem;
    }}
    .hero h1 {{
        font-size: clamp(2.05rem, 11vw, 2.75rem);
    }}
    .stFileUploader [data-testid="stFileUploaderDropzoneInstructions"]::after {{
        font-size: 1.12rem;
        max-width: 240px;
    }}
    .metric-grid {{
        grid-template-columns: 1fr;
    }}
    .health-badge {{
        white-space: normal;
        text-align: center;
    }}
}}
</style>
"""

st.markdown(f'<div class="{mode_class}">', unsafe_allow_html=True)
st.html(CSS)

st.markdown(
    """
<nav class="navbar navbar-expand-lg navbar-glass">
  <div class="container-fluid max-wrap px-0">
    <a class="navbar-brand brand" href="#home">
      <span class="logo-mark"><i class="fa-solid fa-bowl-food"></i></span>
      <span>CalCount AI</span>
    </a>
    <input class="nav-menu-toggle" type="checkbox" id="nutriMenuToggle">
    <label class="navbar-toggler" for="nutriMenuToggle" aria-label="Toggle navigation">
      <span class="navbar-toggler-icon"></span>
    </label>
    <div class="collapse navbar-collapse justify-content-end" id="nutriNav">
      <ul class="navbar-nav align-items-lg-center gap-lg-1">
        <li class="nav-item"><a class="nav-link" href="#home">Home</a></li>
        <li class="nav-item"><a class="nav-link" href="#features">Features</a></li>
        <li class="nav-item"><a class="nav-link" href="#demo">Demo</a></li>
        <li class="nav-item"><a class="nav-link" href="#about">About</a></li>
        <li class="nav-item"><a class="nav-link" href="#contact">Contact</a></li>
      </ul>
    </div>
  </div>
</nav>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<section class="section hero" id="home">
  <div class="blob blob-one"></div>
  <div class="blob blob-two"></div>
  <div class="blob blob-three"></div>
  <div class="max-wrap">
    <div class="row align-items-center g-5">
      <div class="col-lg-6">
        <div class="fade-in">
          <span class="eyebrow"><i class="fa-solid fa-sparkles"></i> Friendly AI nutrition assistant</span>
          <h1>AI Powered Food Calorie Estimation</h1>
          <p class="lead-copy my-4">Upload your food image and instantly discover calories and nutrition details.</p>
          <div class="d-flex flex-wrap gap-3">
            <a class="btn-soft-primary" href="#demo"><i class="fa-solid fa-cloud-arrow-up"></i> Upload Image</a>
            <a class="btn-soft-secondary" href="#features"><i class="fa-solid fa-circle-info"></i> Learn More</a>
          </div>
        </div>
      </div>
      <div class="col-lg-6">
        <div class="glass-card phone-card fade-in">
          <div class="scan-ring">
            <img src="https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=900&q=80" alt="Colorful healthy food bowl">
          </div>
          <div class="scan-line"></div>
          <div class="mini-card calories"><i class="fa-solid fa-fire"></i><span>420 kcal</span></div>
          <div class="mini-card score"><i class="fa-solid fa-heart-pulse"></i><span>Score 92</span></div>
        </div>
      </div>
    </div>
  </div>
</section>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<section class="section" id="demo">
  <div class="max-wrap text-center mb-5 fade-in">
    <span class="eyebrow">Try the demo</span>
    <h2 class="section-title">Upload one food item image</h2>
    <p class="lead-copy mx-auto" style="max-width:720px;">CalCount AI works best with one clear food item at a time and creates a nutrition snapshot in seconds.</p>
  </div>
</section>
""",
    unsafe_allow_html=True,
)

upload_col, result_col = st.columns([0.8, 1.2], gap="large")
with upload_col:
    uploaded_file = None
    st.info("Please upload one clear food item at a time for accurate calorie estimation.")

    if st.session_state.uploaded_image_bytes is None:
        uploaded_widget = st.file_uploader(
            "Upload one food item image",
            type=["jpg", "jpeg", "png", "webp"],
            label_visibility="collapsed",
            key=f"food_upload_{st.session_state.upload_key}",
        )

        if uploaded_widget:
            st.session_state.uploaded_image_bytes = uploaded_widget.getvalue()
            st.session_state.uploaded_image_name = uploaded_widget.name
            st.rerun()

    else:
        uploaded_file = BytesIO(st.session_state.uploaded_image_bytes)
        uploaded_file.name = st.session_state.uploaded_image_name or "uploaded_food_image"
        image = Image.open(BytesIO(st.session_state.uploaded_image_bytes))
        st.image(image, caption="Selected food image", use_container_width=True)

        if st.button("Choose Different Image", use_container_width=True):
            st.session_state.uploaded_image_bytes = None
            st.session_state.uploaded_image_name = None
            st.session_state.result = None
            st.session_state.analysis_done = False
            st.session_state.upload_key += 1
            st.rerun()

    analyze_button = st.button("Analyze Image", type="primary", use_container_width=True)

    if analyze_button and not uploaded_file:
        st.warning("No image uploaded. Please choose a food image before analyzing.")

    if uploaded_file and analyze_button:
        st.session_state.analysis_done = False
        progress = st.progress(0, text="AI analyzing meal...")
        progress.progress(20, text="AI analyzing meal...")
        try:
            st.session_state.result = analyze_uploaded_food(uploaded_file)
            progress.progress(100, text="Analysis complete")
            st.session_state.analysis_done = True
            st.rerun()
        except ValueError as error:
            st.error(str(error))

with result_col:
    result = st.session_state.result or SAMPLE_RESULTS[0]
    ready_class = "fade-in" if st.session_state.analysis_done else ""

    if st.session_state.analysis_done and st.session_state.result:
        food_options = get_available_food_names()
        current_name = st.session_state.result.get("name", "")
        predicted_food = st.session_state.result.get("predicted_food", "")
        select_label = "Correct food name if the model is unsure"

        if current_name and current_name not in food_options:
            food_options.insert(0, current_name)
        if predicted_food and predicted_food not in food_options:
            food_options.insert(0, predicted_food)

        placeholder = "Select correct food name"
        if not st.session_state.result.get("is_food", True):
            if placeholder not in food_options:
                food_options.insert(0, placeholder)
            current_name = placeholder

        if current_name in BIRYANI_VARIANTS or predicted_food == "Biryani":
            variant_options = [food for food in BIRYANI_VARIANTS if food in food_options]
            food_options = variant_options + [
                food for food in food_options if food not in variant_options
            ]
            select_label = "Confirm biryani type"

        selected_food = st.selectbox(
            select_label,
            food_options,
            index=food_options.index(current_name) if current_name in food_options else 0,
        )

        if selected_food != current_name and selected_food != placeholder:
            corrected_prediction = {
                "confidence": "Manual",
                "confidence_value": 100,
                "top_predictions": st.session_state.result.get("top_predictions", []),
            }
            st.session_state.result = build_result(
                selected_food,
                corrected_prediction,
                st.session_state.serving_grams,
            )
            st.rerun()

        if st.session_state.result.get("is_food", True):
            selected_grams = st.slider(
                "Serving size (grams)",
                min_value=50,
                max_value=600,
                value=int(st.session_state.result.get("serving_grams", st.session_state.serving_grams)),
                step=5,
            )

            if selected_grams != st.session_state.serving_grams:
                st.session_state.serving_grams = selected_grams
                slider_prediction = {
                    "confidence": st.session_state.result.get("confidence", "--"),
                    "confidence_value": st.session_state.result.get("confidence_value", 0),
                    "top_predictions": st.session_state.result.get("top_predictions", []),
                }
                st.session_state.result = build_result(
                    current_name,
                    slider_prediction,
                    selected_grams,
                )
                st.rerun()

        result = st.session_state.result

    food_name = result.get("name", "Upload an image")
    calories = result.get("calories", "--")
    protein = result.get("protein", "--")
    carbs = result.get("carbs", "--")
    fat = result.get("fat", "--")
    sugar = result.get("sugar", "--")
    fiber = result.get("fiber", "--")
    score = result.get("score", "--")
    category = result.get("category", "Ready")
    confidence = result.get("confidence", "--")
    serving_size = f"{result.get('serving_grams', st.session_state.serving_grams)} g" if result.get("is_food", True) else "--"
    recommendation = result.get("recommendation", "Upload a food image to generate a backend result.")
    advice = result.get("advice", "Healthy advice will appear after analysis.")
    suggestion = result.get("suggestion", "")
    alternatives = result.get("alternatives", "")
    nutrition_note = result.get("nutrition_note", "Waiting for image analysis.")
    top_predictions = result.get("top_predictions", [])
    top_prediction_text = ""
    if top_predictions:
        top_prediction_text = "Top guesses: " + ", ".join(
            f"{item.get('food', 'Unknown')} ({item.get('confidence', '--')})"
            for item in top_predictions[:3]
        )

    st.markdown(
        f"""
<div class="glass-card result-panel p-4 {ready_class}">
<div class="d-flex flex-wrap justify-content-between align-items-center gap-3 mb-3">
  <h3 class="fw-bold m-0">Detected Nutrition</h3>
  <span class="health-badge">Health Score: <strong class="ms-1">{score}</strong></span>
</div>
<div class="result-grid">
  <div class="summary-grid">
    <div class="nutrition-card"><i class="fa-solid fa-utensils"></i><div class="card-label">Food Name</div><div class="card-value">{food_name}</div></div>
    <div class="nutrition-card"><i class="fa-solid fa-circle-check"></i><div class="card-label">Confidence</div><div class="card-value">{confidence}</div></div>
    <div class="nutrition-card"><i class="fa-solid fa-scale-balanced"></i><div class="card-label">Serving Size</div><div class="card-value">{serving_size}</div></div>
    <div class="nutrition-card"><i class="fa-solid fa-heart-pulse"></i><div class="card-label">Category</div><div class="card-value">{category}</div></div>
  </div>
  <div class="metric-grid">
    <div class="nutrition-card"><i class="fa-solid fa-fire-flame-curved"></i><div class="card-label">Calories</div><div class="card-value">{calories}</div></div>
    <div class="nutrition-card"><i class="fa-solid fa-dumbbell"></i><div class="card-label">Protein</div><div class="card-value">{protein}</div></div>
    <div class="nutrition-card"><i class="fa-solid fa-wheat-awn"></i><div class="card-label">Carbs</div><div class="card-value">{carbs}</div></div>
    <div class="nutrition-card"><i class="fa-solid fa-droplet"></i><div class="card-label">Fat</div><div class="card-value">{fat}</div></div>
    <div class="nutrition-card"><i class="fa-solid fa-cube"></i><div class="card-label">Sugar</div><div class="card-value">{sugar}</div></div>
    <div class="nutrition-card"><i class="fa-solid fa-seedling"></i><div class="card-label">Fiber</div><div class="card-value">{fiber}</div></div>
  </div>
  <div class="nutrition-card advice-card"><i class="fa-solid fa-lightbulb"></i><div class="card-label">Recommendation</div><p class="lead-copy mb-0">{recommendation}</p></div>
  <div class="nutrition-card advice-card"><i class="fa-solid fa-heart-circle-check"></i><div class="card-label">Healthy Advice</div><p class="lead-copy mb-0">{advice}</p></div>
  <div class="nutrition-card advice-card"><i class="fa-solid fa-leaf"></i><div class="card-label">Suggestion</div><p class="lead-copy mb-0">{suggestion}</p></div>
  <div class="nutrition-card advice-card"><i class="fa-solid fa-apple-whole"></i><div class="card-label">Healthy Alternatives</div><p class="lead-copy mb-0">{alternatives}</p></div>
  <div class="result-notes-wrap">
    <p class="result-note">{nutrition_note}</p>
    <p class="result-note">{top_prediction_text}</p>
  </div>
</div>
</div>
""",
        unsafe_allow_html=True,
    )

features = [
    ("fa-brain", "AI Detection", "Recognizes meals from images with a clean, guided scanning experience."),
    ("fa-bolt", "Instant Results", "Displays calorie estimates quickly with friendly visual feedback."),
    ("fa-chart-pie", "Nutrition Analysis", "Breaks food into calories, protein, carbs, fat, and wellness score."),
    ("fa-leaf", "Healthy Suggestions", "Encourages smarter choices with a soft healthcare startup feel."),
]
stats = [("10K+", "Foods Scanned"), ("95%", "Accuracy"), ("5K+", "Happy Users"), ("24/7", "Availability")]
testimonials = [
    (image_to_data_url(os.path.join(PROJECT_ROOT, "Frontend", "assets", "testimonials", "smruti_parida.jpeg")), "Smruti Parida", "The interface feels calm and premium. I can picture using this after every meal."),
    (image_to_data_url(os.path.join(PROJECT_ROOT, "Frontend", "assets", "testimonials", "pragati_dalai.jpeg")), "Pragati Dalai", "The upload flow is smooth, and the nutrition cards make results easy to scan."),
    (image_to_data_url(os.path.join(PROJECT_ROOT, "Frontend", "assets", "testimonials", "siddhi_swain.jpeg")), "Siddhi Swain", "A friendly health-tech design with just enough animation to feel alive."),
]

feature_cards = "".join(
    f"""<div class="col-md-6 col-xl-3">
  <div class="feature-card fade-in">
    <i class="fa-solid {icon}"></i>
    <h3 class="fw-bold mt-4">{title}</h3>
    <p class="lead-copy fs-6">{text}</p>
  </div>
</div>"""
    for icon, title, text in features
)
stat_cards = "".join(
    f"""<div class="col-sm-6 col-lg-3">
  <div class="stat-card fade-in">
    <div class="stat-number">{number}</div>
    <div class="fw-bold" style="color:var(--muted);">{label}</div>
  </div>
</div>"""
    for number, label in stats
)
testimonial_cards = "".join(
    f"""<div class="col-lg-4">
  <div class="testimonial-card d-flex gap-3 fade-in">
    <img src="{avatar}" alt="Avatar of {name}">
    <div>
      <h3 class="fw-bold fs-5">{name}</h3>
      <div class="stars">★★★★★</div>
      <p class="lead-copy fs-6">"{review}"</p>
    </div>
  </div>
</div>"""
    for avatar, name, review in testimonials
)

st.markdown(
    f"""
<section class="section" id="features">
  <div class="max-wrap text-center mb-5 fade-in">
    <span class="eyebrow">Smart features</span>
    <h2 class="section-title">Designed for daily nutrition clarity</h2>
  </div>
  <div class="max-wrap">
    <div class="row g-4">{feature_cards}</div>
  </div>
</section>

<section class="section" id="about">
  <div class="max-wrap glass-card p-4">
    <div class="row g-3">{stat_cards}</div>
  </div>
</section>

<section class="section">
  <div class="max-wrap text-center mb-5 fade-in">
    <span class="eyebrow">Loved by users</span>
    <h2 class="section-title">Health tracking feels effortless</h2>
  </div>
  <div class="max-wrap">
    <div class="row g-4">{testimonial_cards}</div>
  </div>
</section>

<section class="footer-zone" id="contact">
  <div class="max-wrap">
    <div class="row g-4">
<div class="col-lg-5">
  <div class="brand mb-3"><span class="logo-mark"><i class="fa-solid fa-bowl-food"></i></span><span>CalCount AI</span></div>
  <p class="lead-copy fs-6">AI-inspired calorie estimation UI for healthier everyday food decisions.</p>
</div>
<div class="col-lg-3">
  <h3 class="fw-bold fs-5">Quick Links</h3>
  <a class="nav-link px-0" href="#home">Home</a>
  <a class="nav-link px-0" href="#features">Features</a>
  <a class="nav-link px-0" href="#demo">Demo</a>
  <a class="nav-link px-0" href="#about">About</a>
</div>
<div class="col-lg-4">
  <h3 class="fw-bold fs-5">Feedback</h3>
  <p class="contact-note">Have suggestions to improve CalCount AI? Share your feedback with the project team.</p>
  <a class="social-link" href="#"><i class="fa-brands fa-instagram"></i></a>
  <a class="social-link" href="#"><i class="fa-brands fa-linkedin-in"></i></a>
  <a class="social-link" href="#"><i class="fa-brands fa-github"></i></a>
</div>
    </div>
    <p class="lead-copy text-center fs-6 mt-5">© 2026 CalCount AI. All rights reserved.</p>
  </div>
</section>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
""",
    unsafe_allow_html=True,
)

st.markdown('</div>', unsafe_allow_html=True)

with st.sidebar:
    st.title("CalCount AI")
    st.caption("Theme")
    dark = st.toggle("Dark mode", value=st.session_state.dark_mode)
    if dark != st.session_state.dark_mode:
        st.session_state.dark_mode = dark
        st.rerun()
