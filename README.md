# Trading Path Builder

This repo contains a FastAPI backend and a React frontend for guiding users through a trading readiness quiz and generating an AI-based summary.

## Prerequisites

- Python 3.10+ (for the backend)
- Node.js 18+ with npm (for the frontend build)
- OpenAI API Key (required)

## Backend Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `backend/.env` file with:

```env
OPENAI_API_KEY=your-openai-api-key-here
ENV=development
DATABASE_URL=sqlite:///./dev.db
```

Start the backend server:

```powershell
uvicorn main:app --reload
```

The API listens on `http://127.0.0.1:8000`.

## Email Setup (Optional)

Email functionality is optional. If not configured, the app will work in mock mode (OTP codes will be printed to console).

To enable email OTP functionality with Gmail:

1. **Enable 2-Step Verification** on your Google Account:
   - Go to https://myaccount.google.com/security
   - Enable **2-Step Verification**

2. **Generate App Password**:
   - Go to https://myaccount.google.com/security
   - Click **App passwords**
   - Select **Mail** and **Other (Custom name)**
   - Enter "Trading Path Builder"
   - Click **Generate** and copy the 16-character password

3. **Add to `backend/.env`**:
   ```env
   GMAIL_ADDRESS=your-email@gmail.com
   GMAIL_APP_PASSWORD=your-16-char-app-password
   ```

**Note:** Remove spaces from the App Password when adding to `.env`.

## Frontend Setup

```powershell
cd frontend
npm install
```

## Run the Development Server

```powershell
npm start
```

This serves the app at `http://localhost:3000`.

## Create a Production Build

```powershell
npm run build
```

The optimized bundle lives in `frontend\build`. To preview locally:

```powershell
npx serve -s build
```

Then open the URL that `serve` prints (typically `http://localhost:5000`).

## Deploying the Frontend

Upload the contents of `frontend\build` to your hosting provider (Netlify, Vercel, S3, etc.). If you deploy under a subpath, set the `homepage` field in `frontend/package.json` before running `npm run build`.
