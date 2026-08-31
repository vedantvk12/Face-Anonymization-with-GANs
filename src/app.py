import os
import glob
import cv2
import numpy as np
import streamlit as st
import insightface


# ============================================================
# PATHS
# ============================================================

ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

MODEL_PATH = os.path.join(
    ROOT,
    "models",
    "inswapper",
    "inswapper_128.onnx"
)

SOURCE_DIR = os.path.join(
    ROOT,
    "data",
    "source_faces"
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="PRIVAI | Face Anonymization",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CSS
# ============================================================

CSS = """
<style>

.stApp {
    background:
        radial-gradient(
            circle at 10% 10%,
            rgba(70, 90, 180, 0.18),
            transparent 30%
        ),
        radial-gradient(
            circle at 90% 20%,
            rgba(0, 210, 190, 0.10),
            transparent 28%
        ),
        linear-gradient(
            135deg,
            #060811,
            #0b1020,
            #070a12
        );

    color: #f5f7ff;
}

.block-container {
    max-width: 1400px;
    padding-top: 1.5rem;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    background: transparent !important;
}

/* Brand */

.brand {
    display: flex;
    justify-content: space-between;
    align-items: center;

    padding: 16px 20px;
    margin-bottom: 25px;

    border-radius: 18px;

    background: rgba(255,255,255,0.045);

    border: 1px solid rgba(255,255,255,0.10);

    box-shadow:
        0 20px 50px rgba(0,0,0,0.30),
        inset 0 1px rgba(255,255,255,0.08);
}

.brand-title {
    font-size: 19px;
    font-weight: 900;
    letter-spacing: 1px;
}

.brand-subtitle {
    color: #7f8aa6;
    font-size: 11px;
    margin-top: 3px;
}

.online {
    padding: 7px 12px;
    border-radius: 999px;

    color: #71e4bd;
    background: rgba(70,220,170,0.08);

    border: 1px solid rgba(70,220,170,0.20);

    font-size: 11px;
    font-weight: 800;
}

/* Hero */

.hero {
    position: relative;

    min-height: 300px;

    padding: 42px;

    margin-bottom: 25px;

    overflow: hidden;

    border-radius: 28px;

    background:
        linear-gradient(
            135deg,
            rgba(29,39,72,0.90),
            rgba(8,12,23,0.94)
        );

    border: 1px solid rgba(255,255,255,0.09);

    box-shadow:
        0 30px 80px rgba(0,0,0,0.42),
        inset 0 1px rgba(255,255,255,0.08);
}

.hero-kicker {
    color: #8da6ff;

    font-size: 11px;

    font-weight: 800;

    letter-spacing: 2px;

    margin-bottom: 15px;
}

.hero-title {
    font-size: 48px;

    line-height: 1.05;

    font-weight: 900;

    letter-spacing: -2px;

    background:
        linear-gradient(
            110deg,
            #ffffff,
            #b8c8ff,
            #76dfff
        );

    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-text {
    max-width: 650px;

    margin-top: 18px;

    color: #9da8c1;

    font-size: 15px;

    line-height: 1.6;
}

.badges {
    display: flex;
    gap: 10px;

    margin-top: 22px;
}

.badge {
    padding: 8px 12px;

    border-radius: 10px;

    background: rgba(255,255,255,0.045);

    border: 1px solid rgba(255,255,255,0.08);

    color: #ccd5e9;

    font-size: 11px;
}

/* 3D Orb */

.orb {
    position: absolute;

    right: 80px;
    top: 50px;

    width: 190px;
    height: 190px;

    border-radius: 50%;

    background:
        radial-gradient(
            circle at 30% 25%,
            rgba(255,255,255,0.35),
            transparent 8%
        ),
        radial-gradient(
            circle at 38% 35%,
            #3958ad,
            #121a38 52%,
            #050710 76%
        );

    border: 1px solid rgba(140,170,255,0.35);

    box-shadow:
        0 0 40px rgba(70,120,255,0.35),
        0 0 100px rgba(70,120,255,0.12),
        inset -25px -25px 45px rgba(0,0,0,0.45);

    animation: float 5s ease-in-out infinite;
}

.orb:before {
    content: "";

    position: absolute;

    width: 225px;
    height: 75px;

    left: -18px;
    top: 57px;

    border: 1px solid rgba(100,210,255,0.32);

    border-radius: 50%;

    transform: rotate(-25deg);
}

.orb:after {
    content: "";

    position: absolute;

    width: 75px;
    height: 225px;

    left: 57px;
    top: -18px;

    border: 1px solid rgba(100,210,255,0.28);

    border-radius: 50%;

    transform: rotate(25deg);
}

@keyframes float {

    0%, 100% {
        transform: translateY(0) rotateY(0deg);
    }

    50% {
        transform: translateY(-12px) rotateY(12deg);
    }
}

/* Cards */

.card {
    padding: 22px;

    border-radius: 20px;

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,0.055),
            rgba(255,255,255,0.02)
        );

    border: 1px solid rgba(255,255,255,0.08);

    box-shadow:
        0 18px 45px rgba(0,0,0,0.25),
        inset 0 1px rgba(255,255,255,0.06);
}

.card-title {
    font-size: 19px;
    font-weight: 800;
}

.card-subtitle {
    color: #7d88a2;
    font-size: 12px;
    margin-top: 4px;
}

/* Metrics */

.metric {
    padding: 18px;

    border-radius: 16px;

    background: rgba(255,255,255,0.035);

    border: 1px solid rgba(255,255,255,0.07);

    box-shadow:
        inset 0 1px rgba(255,255,255,0.05);
}

.metric-label {
    color: #7e89a3;

    font-size: 10px;

    text-transform: uppercase;

    letter-spacing: 1px;
}

.metric-value {
    margin-top: 7px;

    font-size: 23px;

    font-weight: 900;

    color: #e9efff;
}

/* Buttons */

.stButton > button {
    min-height: 50px !important;

    border-radius: 13px !important;

    border: 1px solid rgba(130,160,255,0.30) !important;

    background:
        linear-gradient(
            135deg,
            #3c55a6,
            #20356f
        ) !important;

    color: white !important;

    font-weight: 800 !important;

    box-shadow:
        0 12px 30px rgba(40,70,180,0.25),
        inset 0 1px rgba(255,255,255,0.15);

    transition: 0.2s ease !important;
}

.stButton > button:hover {
    transform: translateY(-2px);
}

/* Upload */

[data-testid="stFileUploader"] {
    padding: 8px;

    border-radius: 15px;

    background: rgba(255,255,255,0.025);

    border: 1px dashed rgba(140,160,210,0.30);
}

/* Images */

[data-testid="stImage"] {
    border-radius: 16px;
    overflow: hidden;

    box-shadow:
        0 15px 40px rgba(0,0,0,0.28);
}

/* Footer */

.footer {
    text-align: center;

    color: #626c83;

    font-size: 11px;

    padding: 30px 0 5px;
}

</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


# ============================================================
# BRAND BAR
# ============================================================

st.markdown(
    """
<div class="brand">
    <div>
        <div class="brand-title">🔐 PRIVAI</div>
        <div class="brand-subtitle">
            Intelligent Face Anonymization Platform
        </div>
    </div>

    <div class="online">
        ● SYSTEM ONLINE
    </div>
</div>
""",
    unsafe_allow_html=True
)


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
<div class="hero">

    <div class="hero-kicker">
        AI • COMPUTER VISION • PRIVACY
    </div>

    <div class="hero-title">
        Protect Identity.<br>
        Preserve Utility.
    </div>

    <div class="hero-text">
        Transform identifiable faces into synthetic identities
        while preserving the surrounding scene for useful
        downstream applications.
    </div>

    <div class="badges">
        <div class="badge">🛡 Identity Protection</div>
        <div class="badge">👁 Scene Preservation</div>
        <div class="badge">⚡ AI Processing</div>
    </div>

    <div class="orb"></div>

</div>
""",
    unsafe_allow_html=True
)


# ============================================================
# MODEL LOADING
# ============================================================

@st.cache_resource
def load_system():

    if not os.path.isfile(MODEL_PATH):
        raise FileNotFoundError(
            "InSwapper model not found:\n"
            + MODEL_PATH
        )

    face_app = insightface.app.FaceAnalysis(
        name="buffalo_l",
        providers=[
            "CPUExecutionProvider"
        ]
    )

    face_app.prepare(
        ctx_id=0,
        det_size=(640, 640)
    )

    swapper = insightface.model_zoo.get_model(
        MODEL_PATH,
        download=False,
        providers=[
            "CPUExecutionProvider"
        ]
    )

    source_files = []

    for extension in (
        "*.jpg",
        "*.jpeg",
        "*.png",
        "*.webp"
    ):

        source_files.extend(
            glob.glob(
                os.path.join(
                    SOURCE_DIR,
                    extension
                )
            )
        )

    source_faces = []
    source_names = []

    for path in sorted(source_files):

        if not os.path.isfile(path):
            continue

        if os.path.getsize(path) == 0:
            continue

        image = cv2.imread(path)

        if image is None:
            continue

        faces = face_app.get(image)

        if not faces:
            continue

        face = max(
            faces,
            key=lambda f:
            (
                f.bbox[2] - f.bbox[0]
            )
            *
            (
                f.bbox[3] - f.bbox[1]
            )
        )

        source_faces.append(face)

        source_names.append(
            os.path.basename(path)
        )

    return (
        face_app,
        swapper,
        source_faces,
        source_names
    )


# ============================================================
# LOAD
# ============================================================

with st.spinner("Initializing AI privacy engine..."):

    try:

        (
            face_app,
            swapper,
            source_faces,
            source_names
        ) = load_system()

    except Exception as error:

        st.error("System initialization failed.")
        st.code(str(error))
        st.stop()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown(
    "## ⚙️ CONTROL CENTER"
)

method = st.sidebar.radio(
    "ANONYMIZATION METHOD",
    [
        "Generative",
        "Blur"
    ]
)

st.sidebar.markdown("---")

st.sidebar.markdown(
    "### 🧬 Synthetic Identities"
)

if source_names:

    st.sidebar.success(
        f"{len(source_names)} identities loaded"
    )

    for name in source_names:
        st.sidebar.write(
            "✓ " + name
        )

else:

    st.sidebar.error(
        "No synthetic identities found."
    )

st.sidebar.markdown("---")

st.sidebar.markdown(
    "### 🧠 AI ENGINE"
)

st.sidebar.write(
    "Face Detection  🟢"
)

st.sidebar.write(
    "InSwapper       🟢"
)

st.sidebar.write(
    "OpenCV          🟢"
)

st.sidebar.write(
    "CPU Inference   🟡"
)


# ============================================================
# WORKSPACE HEADER
# ============================================================

st.markdown(
    """
<div class="card">

<div class="card-title">
🧬 Anonymization Workspace
</div>

<div class="card-subtitle">
Upload an image containing one or more faces.
</div>

</div>
""",
    unsafe_allow_html=True
)

st.write("")


# ============================================================
# UPLOAD
# ============================================================

uploaded_file = st.file_uploader(
    "📤 Upload Image",
    type=[
        "jpg",
        "jpeg",
        "png",
        "webp"
    ]
)


# ============================================================
# IMAGE PROCESSING
# ============================================================

if uploaded_file is not None:

    raw = uploaded_file.getvalue()

    array = np.frombuffer(
        raw,
        dtype=np.uint8
    )

    image = cv2.imdecode(
        array,
        cv2.IMREAD_COLOR
    )

    if image is None:

        st.error(
            "Unable to read uploaded image."
        )

        st.stop()

    original_rgb = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    st.markdown(
        "### 👁 Original Image"
    )

    st.image(
        original_rgb,
        use_container_width=True
    )

    st.write("")

    # --------------------------------------------------------
    # BUTTON
    # --------------------------------------------------------

    if st.button(
        "🔐  ANONYMIZE IMAGE",
        type="primary",
        use_container_width=True
    ):

        with st.spinner(
            "Detecting faces and applying anonymization..."
        ):

            # =================================================
            # DETECT
            # =================================================

            faces = face_app.get(
                image
            )

            face_count = len(
                faces
            )

            if face_count == 0:

                st.warning(
                    "No face detected in the image."
                )

                st.stop()

            # =================================================
            # GENERATIVE
            # =================================================

            if method == "Generative":

                if not source_faces:

                    st.error(
                        "No valid synthetic identities available."
                    )

                    st.stop()

                result = image.copy()

                faces = sorted(
                    faces,
                    key=lambda face:
                    face.bbox[0]
                )

                for index, target_face in enumerate(
                    faces
                ):

                    source_face = source_faces[
                        index % len(source_faces)
                    ]

                    result = swapper.get(
                        result,
                        target_face,
                        source_face,
                        paste_back=True
                    )

            # =================================================
            # BLUR
            # =================================================

            else:

                result = image.copy()

                for face in faces:

                    x1, y1, x2, y2 = (
                        face.bbox.astype(int)
                    )

                    width = x2 - x1
                    height = y2 - y1

                    px = int(
                        width * 0.20
                    )

                    py = int(
                        height * 0.30
                    )

                    x1 = max(
                        0,
                        x1 - px
                    )

                    y1 = max(
                        0,
                        y1 - py
                    )

                    x2 = min(
                        result.shape[1],
                        x2 + px
                    )

                    y2 = min(
                        result.shape[0],
                        y2 + py
                    )

                    crop = result[
                        y1:y2,
                        x1:x2
                    ]

                    if crop.size == 0:
                        continue

                    h, w = crop.shape[:2]

                    kernel = max(
                        31,
                        (min(h, w) // 2) * 2 + 1
                    )

                    kernel = min(
                        kernel,
                        101
                    )

                    blurred = cv2.GaussianBlur(
                        crop,
                        (kernel, kernel),
                        0
                    )

                    result[
                        y1:y2,
                        x1:x2
                    ] = blurred

        # ====================================================
        # RESULT
        # ====================================================

        result_rgb = cv2.cvtColor(
            result,
            cv2.COLOR_BGR2RGB
        )

        st.markdown("---")

        st.markdown(
            "## 🎯 Transformation Result"
        )

        left, right = st.columns(
            2,
            gap="large"
        )

        with left:

            st.markdown(
                "#### Original"
            )

            st.image(
                original_rgb,
                use_container_width=True
            )

        with right:

            st.markdown(
                f"#### {method} Anonymized"
            )

            st.image(
                result_rgb,
                use_container_width=True
            )

        # ====================================================
        # METRICS
        # ====================================================

        st.markdown(
            "### 📊 Processing Summary"
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            st.markdown(
                f"""
<div class="metric">
<div class="metric-label">
Faces Detected
</div>
<div class="metric-value">
{face_count}
</div>
</div>
""",
                unsafe_allow_html=True
            )

        with c2:

            st.markdown(
                f"""
<div class="metric">
<div class="metric-label">
Method
</div>
<div class="metric-value">
{method}
</div>
</div>
""",
                unsafe_allow_html=True
            )

        with c3:

            st.markdown(
                """
<div class="metric">
<div class="metric-label">
Identity
</div>
<div class="metric-value">
ALTERED
</div>
</div>
""",
                unsafe_allow_html=True
            )

        with c4:

            st.markdown(
                """
<div class="metric">
<div class="metric-label">
Scene
</div>
<div class="metric-value">
PRESERVED
</div>
</div>
""",
                unsafe_allow_html=True
            )

        # ====================================================
        # PRIVACY MESSAGE
        # ====================================================

        if method == "Generative":

            st.success(
                "🛡️ Generative anonymization completed. "
                "The detected facial identity has been replaced "
                "with a synthetic identity."
            )

        else:

            st.info(
                "🛡️ Blur baseline completed. "
                "Facial details have been obscured."
            )

        # ====================================================
        # DOWNLOAD
        # ====================================================

        success, encoded = cv2.imencode(
            ".jpg",
            result
        )

        if success:

            st.download_button(
                "⬇️ Download Anonymized Image",
                data=encoded.tobytes(),
                file_name=(
                    method.lower()
                    + "_anonymized.jpg"
                ),
                mime="image/jpeg",
                use_container_width=True
            )


# ============================================================
# TECHNICAL DETAILS
# ============================================================

st.markdown("---")

with st.expander(
    "🧠 Technical Architecture"
):

    st.markdown(
        """
**Processing Pipeline**

`Input Image`
→ `Face Detection`
→ `Face Region`
→ `Generative Replacement / Blur`
→ `Anonymized Image`

**Generative Method**

InsightFace detects the facial region and InSwapper
replaces the detected face using a synthetic identity.

**Privacy Evaluation**

Identity similarity can be measured using face-recognition
embeddings. Lower similarity indicates greater identity
alteration.

**Important**

This is an experimental privacy-preservation system.
Generative anonymization does not provide a mathematical
guarantee of anonymity.
"""
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
<div class="footer">
PRIVAI • AI Face Anonymization System<br>
Experimental Privacy-Preserving Computer Vision Platform
</div>
""",
    unsafe_allow_html=True
)