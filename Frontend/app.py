import streamlit as st
from PIL import Image
import random
import time
from urllib.parse import quote

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
    page_title="NutriScan - Food Calorie Detector",
    page_icon=FAVICON_DATA_URL,
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "result" not in st.session_state:
    st.session_state.result = None

SAMPLE_RESULTS = [
    {
        "name": "Rainbow Salad Bowl",
        "calories": "420 kcal",
        "protein": "24 g",
        "carbs": "52 g",
        "fat": "14 g",
        "score": "92",
    },
    {
        "name": "Grilled Paneer Plate",
        "calories": "510 kcal",
        "protein": "31 g",
        "carbs": "38 g",
        "fat": "22 g",
        "score": "88",
    },
    {
        "name": "Avocado Toast",
        "calories": "360 kcal",
        "protein": "13 g",
        "carbs": "41 g",
        "fat": "18 g",
        "score": "90",
    },
]

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

.block-container {{ max-width: 100% !important; padding: 0 !important; }}
#MainMenu, footer, header {{ visibility: hidden; }}
.stDeployButton {{ display: none; }}
[data-testid="stHorizontalBlock"] {{
    max-width: 1120px;
    width: calc(100% - 40px);
    margin-left: auto;
    margin-right: auto;
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

.brand {{ display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 1.25rem; color: var(--ink); }}
.logo-mark {{
    display: grid; place-items: center; width: 42px; height: 42px;
    color: #fff; border-radius: 16px;
    background: linear-gradient(135deg, var(--blue), #66a9df);
    box-shadow: 0 12px 26px rgba(72, 145, 210, 0.28);
}}
.nav-link {{ color: var(--muted) !important; font-weight: 800; border-radius: 999px; padding: 10px 14px !important; }}
.nav-link:hover {{ color: var(--ink) !important; background: rgba(255,255,255,.5); }}

.section {{ position: relative; padding: 92px clamp(20px, 5vw, 80px); overflow: hidden; }}
.hero {{ min-height: calc(100vh - 70px); display: flex; align-items: center; }}
.max-wrap {{ max-width: 1180px; margin: 0 auto; width: 100%; }}
.eyebrow {{
    display: inline-flex; align-items: center; gap: 8px; width: fit-content;
    margin-bottom: 18px; padding: 9px 14px; color: #3f82b8;
    border: 1px solid var(--border); border-radius: 999px;
    background: var(--surface); backdrop-filter: blur(14px);
    font-size: .88rem; font-weight: 800;
}}
.hero h1 {{ font-size: clamp(3rem, 7vw, 6.5rem); line-height: 1.04; letter-spacing: 0; font-weight: 800; color: var(--ink); }}
.section-title {{ font-size: clamp(2rem, 4vw, 4rem); line-height: 1.05; letter-spacing: 0; font-weight: 800; color: var(--ink); }}
.lead-copy {{ color: var(--muted); line-height: 1.75; font-size: clamp(1rem, 2vw, 1.22rem); }}

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

.upload-box {{ border: 2px dashed rgba(76,143,199,.52); border-radius: 24px; min-height: 310px; display: grid; place-items: center; text-align: center; background: rgba(255,255,255,.42); transition: transform .25s ease, border .25s ease; }}
.upload-box:hover {{ transform: translateY(-3px); border-color: var(--blue); }}
.upload-icon {{ color: #5da4df; font-size: 4rem; animation: uploadFloat 2.4s ease-in-out infinite; }}
.stFileUploader label {{ color: var(--ink) !important; font-weight: 800; }}
.stFileUploader section {{ border: 2px dashed rgba(76,143,199,.45); background: rgba(255,255,255,.42); border-radius: 18px; }}

.nutrition-card, .feature-card, .testimonial-card, .stat-card {{
    height: 100%; border: 1px solid var(--border); border-radius: 24px;
    background: rgba(255,255,255,.46); padding: 24px; transition: transform .25s ease, box-shadow .25s ease;
}}
.dark-mode .nutrition-card, .dark-mode .testimonial-card, .dark-mode .stat-card {{ background: rgba(255,255,255,.06); }}
.nutrition-card:hover, .feature-card:hover, .testimonial-card:hover {{ transform: translateY(-7px); }}
.nutrition-card i, .feature-card i {{ color: #5da4df; font-size: 1.65rem; }}
.card-label {{ color: var(--muted); font-weight: 800; margin: 14px 0 5px; }}
.card-value {{ font-size: 1.7rem; font-weight: 800; color: var(--ink); }}
.health-badge {{ display: inline-flex; padding: 9px 13px; color: #3278ad; border-radius: 999px; background: rgba(191,221,240,.58); font-size: .9rem; font-weight: 800; }}
.feature-card:nth-child(odd) {{ background: linear-gradient(145deg, rgba(255,249,210,.78), rgba(191,221,240,.62)); }}
.feature-card:nth-child(even) {{ background: linear-gradient(145deg, rgba(255,235,204,.78), rgba(140,192,235,.55)); }}
.dark-mode .feature-card {{ background: var(--surface); }}
.stat-card {{ display: grid; place-items: center; min-height: 150px; text-align: center; }}
.stat-number {{ color: #4f9bd6; font-size: clamp(2.1rem, 4vw, 3.4rem); font-weight: 800; }}
.testimonial-card img {{ width: 64px; height: 64px; object-fit: cover; border-radius: 50%; border: 4px solid rgba(255,255,255,.74); }}
.stars {{ color: #f4b84d; letter-spacing: 0; }}
.footer-zone {{ padding: 70px clamp(20px, 5vw, 80px) 28px; background: rgba(255,255,255,.34); border-top: 1px solid var(--border); }}
.dark-mode .footer-zone {{ background: rgba(6,17,28,.3); }}
.newsletter {{ display: flex; gap: 8px; padding: 8px; border: 1px solid var(--border); border-radius: 999px; background: var(--surface); }}
.newsletter input {{ min-width: 0; flex: 1; border: 0; outline: 0; padding: 0 12px; color: var(--ink); background: transparent; }}
.newsletter button {{ width: 44px; height: 44px; color: #fff; border: 0; border-radius: 50%; background: var(--blue); }}
.social-link {{ width: 42px; height: 42px; display: inline-grid; place-items: center; margin-right: 8px; border-radius: 50%; color: var(--muted); background: var(--surface); text-decoration: none; }}
.fade-in {{ animation: fadeUp .85s ease both; }}

@keyframes fadeUp {{ from {{ opacity: 0; transform: translateY(28px); }} to {{ opacity: 1; transform: translateY(0); }} }}
@keyframes floatBlob {{ 50% {{ transform: translate3d(18px, -22px, 0) scale(1.08); }} }}
@keyframes slowSpin {{ to {{ transform: rotate(360deg); }} }}
@keyframes scan {{ 0%,100% {{ top: 23%; }} 50% {{ top: 77%; }} }}
@keyframes uploadFloat {{ 50% {{ transform: translateY(-10px); }} }}

@media (max-width: 991px) {{ .phone-card {{ min-height: 430px; }} .section {{ padding: 74px 18px; }} }}
@media (max-width: 576px) {{ .hero h1 {{ font-size: clamp(2.7rem, 15vw, 4.4rem); }} .mini-card {{ padding: 11px 13px; font-size: .88rem; }} }}
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
      <span>NutriScan AI</span>
    </a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#nutriNav" aria-controls="nutriNav" aria-expanded="false" aria-label="Toggle navigation">
      <span class="navbar-toggler-icon"></span>
    </button>
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
          <h1>AI Powered Food Calorie Detection</h1>
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
    <h2 class="section-title">Upload a meal image</h2>
    <p class="lead-copy mx-auto" style="max-width:720px;">NutriScan simulates an AI scan and creates a nutrition snapshot in seconds.</p>
  </div>
</section>
""",
    unsafe_allow_html=True,
)

upload_col, result_col = st.columns([0.95, 1.05], gap="large")
with upload_col:
    st.markdown(
        """
<div class="upload-box glass-card mb-3 fade-in">
  <div>
    <i class="fa-solid fa-cloud-arrow-up upload-icon mb-3"></i>
    <h3 class="fw-bold">Drag & drop your food image</h3>
    <p class="lead-copy mb-0">or browse JPG, PNG, or WebP files</p>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    uploaded_file = st.file_uploader("Choose a food image", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")
    analyze_button = st.button("Analyze Image", type="primary", use_container_width=True)

    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Selected food image", use_container_width=True)

    if uploaded_file and analyze_button:
        st.session_state.analysis_done = False
        progress = st.progress(0, text="AI analyzing meal...")
        for value in range(0, 101, 10):
            progress.progress(value, text=f"AI analyzing meal... {value}%")
            time.sleep(0.05)
        st.session_state.result = random.choice(SAMPLE_RESULTS)
        st.session_state.analysis_done = True
        st.rerun()

with result_col:
    result = st.session_state.result or SAMPLE_RESULTS[0]
    ready_class = "fade-in" if st.session_state.analysis_done else ""
    st.markdown(
        f"""
<div class="glass-card p-4 {ready_class}">
<div class="d-flex flex-wrap justify-content-between align-items-center gap-3 mb-4">
  <h3 class="fw-bold m-0">Detected Nutrition</h3>
  <span class="health-badge">Health Score: <strong class="ms-1">{result['score']}</strong></span>
</div>
<div class="row g-3">
  <div class="col-12"><div class="nutrition-card"><i class="fa-solid fa-utensils"></i><div class="card-label">Food Name</div><div class="card-value">{result['name']}</div></div></div>
  <div class="col-sm-6"><div class="nutrition-card"><i class="fa-solid fa-fire-flame-curved"></i><div class="card-label">Estimated Calories</div><div class="card-value">{result['calories']}</div></div></div>
  <div class="col-sm-6"><div class="nutrition-card"><i class="fa-solid fa-dumbbell"></i><div class="card-label">Protein</div><div class="card-value">{result['protein']}</div></div></div>
  <div class="col-sm-6"><div class="nutrition-card"><i class="fa-solid fa-wheat-awn"></i><div class="card-label">Carbs</div><div class="card-value">{result['carbs']}</div></div></div>
  <div class="col-sm-6"><div class="nutrition-card"><i class="fa-solid fa-droplet"></i><div class="card-label">Fat</div><div class="card-value">{result['fat']}</div></div></div>
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
    ("https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=160&q=80", "Aanya Mehra", "The interface feels calm and premium. I can picture using this after every meal."),
    ("https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=160&q=80", "Rohan Shah", "The upload flow is smooth, and the nutrition cards make results easy to scan."),
    ("https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&w=160&q=80", "Kiara Dsouza", "A friendly health-tech design with just enough animation to feel alive."),
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
  <div class="brand mb-3"><span class="logo-mark"><i class="fa-solid fa-bowl-food"></i></span><span>NutriScan</span></div>
  <p class="lead-copy fs-6">AI-inspired calorie detection UI for healthier everyday food decisions.</p>
</div>
<div class="col-lg-3">
  <h3 class="fw-bold fs-5">Quick Links</h3>
  <a class="nav-link px-0" href="#home">Home</a>
  <a class="nav-link px-0" href="#features">Features</a>
  <a class="nav-link px-0" href="#demo">Demo</a>
  <a class="nav-link px-0" href="#about">About</a>
</div>
<div class="col-lg-4">
  <h3 class="fw-bold fs-5">Newsletter</h3>
  <form class="newsletter mb-3"><input type="email" placeholder="Email address"><button type="button"><i class="fa-solid fa-paper-plane"></i></button></form>
  <a class="social-link" href="#"><i class="fa-brands fa-instagram"></i></a>
  <a class="social-link" href="#"><i class="fa-brands fa-linkedin-in"></i></a>
  <a class="social-link" href="#"><i class="fa-brands fa-github"></i></a>
</div>
    </div>
    <p class="lead-copy text-center fs-6 mt-5">© 2026 NutriScan. All rights reserved.</p>
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
    st.title("NutriScan")
    st.caption("Theme")
    dark = st.toggle("Dark mode", value=st.session_state.dark_mode)
    if dark != st.session_state.dark_mode:
        st.session_state.dark_mode = dark
        st.rerun()
# This is a test line for our group project workflow
