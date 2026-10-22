# PRIVAI Enterprise — Fast Deployment Guide (Vercel + Render)

This turnkey guide covers deploying the **PRIVAI Face Anonymization Platform**:
- **Backend (FastAPI + InsightFace + InSwapper + OpenCV)**: Deployed to **Render**
- **Frontend (React 19 + TypeScript + Vite)**: Deployed to **Vercel**

---

## Part 1: Deploy Backend to Render (5 Minutes)

### Option A: 1-Click Render Blueprint (Recommended)
1. Push your repository to GitHub.
2. Log in to [Render Dashboard](https://dashboard.render.com).
3. Click **New +** in the top right and select **Blueprint**.
4. Connect your GitHub repository.
5. Render will automatically detect [`render.yaml`](./render.yaml).
6. Click **Apply**. Render will automatically build the service and start the server.

---

### Option B: Manual Web Service on Render
If you prefer configuring manually through the Render UI:

1. In Render Dashboard, click **New +** $\rightarrow$ **Web Service**.
2. Select **Build and deploy from a Git repository** and connect your repo.
3. Configure the following fields:
   - **Name**: `privai-backend` (or your choice)
   - **Region**: Oregon (US West) or Frankfurt (EU)
   - **Branch**: `main`
   - **Root Directory**: Leave blank (repository root)
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install --upgrade pip && pip install -r backend/requirements.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn backend.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Instance Type**: **Free**
4. Expand **Advanced** $\rightarrow$ **Environment Variables**:
   | Key | Value | Notes |
   |---|---|---|
   | `PYTHON_VERSION` | `3.10.13` | Recommended for stable ONNX and InsightFace |
5. In **Health Check Path**, enter: `/api/health`
6. Click **Create Web Service**.

> **Note on Model Download**: On the first startup, PRIVAI's automated model loader will safely stream `inswapper_128.onnx` from Hugging Face into memory/disk. The backend health endpoint `/api/health` will report `"warming"` and transition to `"online"` within ~60 seconds.

7. Once deployed, copy your Render Web Service URL (e.g., `https://privai-backend.onrender.com`).

---

## Part 2: Deploy Frontend to Vercel (2 Minutes)

1. Log in to [Vercel](https://vercel.com).
2. Click **Add New...** $\rightarrow$ **Project**.
3. Import your GitHub repository.
4. In the **Configure Project** screen:
   - **Framework Preset**: `Vite` (auto-detected)
   - **Root Directory**: Click **Edit** and select `frontend` (or leave as `./` — root [`vercel.json`](./vercel.json) handles both automatically)
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Expand **Environment Variables**:
   | Key | Value | Description |
   |---|---|---|
   | `VITE_API_URL` | `https://privai-backend.onrender.com` | Replace with your exact Render backend URL |
6. Click **Deploy**.

Vercel will build and deploy the React application in ~30 seconds.

---

## Part 3: Verification Checklist

1. **Verify Backend Health**:
   Open `https://your-backend.onrender.com/api/health` in your browser. You should see:
   ```json
   {
     "status": "online",
     "face_detection": true,
     "inswapper": true,
     "synthetic_identities": 10,
     "inference": "CPU"
   }
   ```
2. **Verify Frontend**:
   Open your Vercel deployment URL (e.g., `https://privai.vercel.app`).
   - The top navigation bar should display the green pill: **`● Models Ready`**.
   - Navigate to **Studio**, upload a test photo, select a synthetic identity, and click **Anonymize Face**.
   - Verify the anonymized result appears with identity metrics and side-by-side comparison.

---

## Architecture Reference

```
[ User Browser ]
       |
       +---> [ Vercel Edge CDN ] ----> Vite + React 19 Frontend (SPA)
       |
       +---> [ Render Web Service ] -> FastAPI 2.0.0
                                         ├── InsightFace (buffalo_l)
                                         ├── InSwapper 128 ONNX
                                         ├── Multi-Face Video Tracking
                                         └── Soft Edge Anatomical Blending
```
