# Trading Path Builder

A full-stack web application for generating personalized trading plans based on user quiz responses. The system uses AI (OpenAI) to create customized trading strategies and guides users through a three-stage learning path.

## 🚀 Features

- **Interactive Quiz**: Multi-question trading readiness assessment with keyboard shortcuts
- **AI-Powered Generation**: Personalized trading plans generated using OpenAI GPT models
- **Three-Stage Learning Path**: Progressive content delivery (Foundation → Execution → Advanced)
- **Smart Caching**: Fingerprint-based caching system to avoid redundant API calls
- **Instant Unlock**: Single-click unlock for premium content (no payment processing)
- **Email Authentication**: Secure sign-up and sign-in with email verification
- **Responsive Design**: Modern, mobile-friendly UI with dark theme
- **Analytics Tracking**: Built-in event tracking for user interactions

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10+** (for backend)
- **Node.js 18+** with npm (for frontend)
- **OpenAI API Key** (required for AI content generation)
- **PostgreSQL** (optional, SQLite is used by default for development)

## 🛠️ Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd trading_path_builder
```

### 2. Backend Setup

#### Step 1: Create Virtual Environment

```bash
cd backend
python -m venv .venv
```

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
.venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

#### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

#### Step 3: Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Environment
ENV=development

# Database (SQLite for development, PostgreSQL for production)
DATABASE_URL=sqlite:///./dev.db

# OpenAI API Configuration (REQUIRED)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_OUTPUT_TOKENS=2000

# Authentication
JWT_SECRET=your-secure-jwt-secret-change-in-production
EMAIL_SERVICE_API_KEY=your-sendgrid-api-key-optional

# Email Configuration (Optional - works in mock mode if not set)
GMAIL_ADDRESS=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password

# URLs
FRONTEND_URL=http://localhost:3000
BACKEND_HOST=http://127.0.0.1:8000
ALLOWED_ORIGINS=

# Payment (Display only - no actual payment processing)
PRICE_USD=5.0

# Feature Flags
PAYWALL_ENABLED=true
FREE_STAGE_ID=1
TEMPLATE_VERSION=1.0
ALLOW_ANON_PLAN=true
```

**⚠️ Important:** Replace `your-openai-api-key-here` with your actual OpenAI API key. You can obtain one from [platform.openai.com](https://platform.openai.com/api-keys).

#### Step 4: Initialize Database

The database will be automatically created on first run. For SQLite, no additional setup is needed.

#### Step 5: Start the Backend Server

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`

You can access the API documentation at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### 3. Frontend Setup

#### Step 1: Install Dependencies

Open a new terminal window:

```bash
cd frontend
npm install
```

#### Step 2: Configure Environment (Optional)

If your backend is running on a different URL, create a `.env.local` file:

```env
REACT_APP_API_URL=http://127.0.0.1:8000
```

#### Step 3: Start Development Server

```bash
npm start
```

The application will open at `http://localhost:3000`

## 🏗️ Project Structure

```
trading_path_builder/
├── backend/
│   ├── core/              # Core configuration and utilities
│   ├── database/          # Database models and schema
│   ├── routers/           # API route handlers
│   ├── services/          # Business logic services
│   ├── utils/             # Utility functions
│   ├── models/            # Pydantic models
│   ├── main.py            # FastAPI application entry point
│   └── requirements.txt   # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── api/           # API client functions
│   │   ├── pages/         # Page components
│   │   └── utils/         # Utility functions
│   ├── public/            # Static assets
│   └── package.json       # Node.js dependencies
│
└── README.md              # This file
```

## 🔑 API Key Configuration

### Getting Your OpenAI API Key

1. Visit [platform.openai.com](https://platform.openai.com)
2. Sign in or create an account
3. Navigate to **API Keys** section
4. Click **Create new secret key**
5. Copy the key (starts with `sk-` or `sk-or-v1-`)

### OpenAI Router Keys

If you're using an OpenAI Router key (starts with `sk-or-v1-`), you may need to set an additional environment variable:

```env
OPENAI_ROUTER_URL=https://your-router-url.com/v1
```

### Updating the API Key

1. Open `backend/.env`
2. Update the `OPENAI_API_KEY` value
3. Restart the backend server

**Note:** The application includes fingerprint caching, so identical quiz answers won't trigger new API calls, saving costs.

## 📦 Building for Production

### Frontend Production Build

```bash
cd frontend
npm run build
```

This creates an optimized production build in the `frontend/build/` directory.

To preview the production build locally:

```bash
npx serve -s build
```

### Deploying Frontend

Upload the contents of `frontend/build/` to your hosting provider:

- **Netlify**: Drag and drop the `build` folder
- **Vercel**: Connect your repository and set build command to `npm run build`
- **AWS S3**: Upload `build/` contents to an S3 bucket with static website hosting
- **Other**: Any static hosting service that supports React apps

### Backend Production Deployment

1. **Set Production Environment Variables:**

```env
ENV=production
DATABASE_URL=postgresql://user:password@host:port/dbname
JWT_SECRET=your-very-secure-secret-key-here-min-32-chars
OPENAI_API_KEY=your-production-key
FRONTEND_URL=https://your-frontend-domain.com
BACKEND_HOST=https://your-backend-domain.com
```

2. **Use a Production WSGI Server:**

```bash
pip install gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

3. **Set up Reverse Proxy (Nginx recommended)**
4. **Configure SSL/HTTPS**
5. **Set up Database Backups**

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Rate Limiting**: Protection against brute force attacks
- **Input Validation**: All inputs validated using Pydantic
- **CORS Protection**: Configurable allowed origins
- **SQL Injection Prevention**: Using SQLAlchemy ORM
- **Secure Headers**: Security headers configured in middleware

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest tests/
```

### Run Specific Tests

```bash
# Test fingerprint caching
pytest tests/test_fingerprint_caching.py

# Test authentication
pytest tests/test_auth.py

# Test plan generation
pytest tests/test_plan_generation.py
```

## 📊 Features in Detail

### Fingerprint Caching

The system uses a deterministic fingerprinting algorithm to cache generated plans. When identical quiz answers are submitted:

- **Cache Hit**: Returns cached plan instantly (no API call)
- **Cache Miss**: Generates new plan and caches it for future use

This significantly reduces API costs and improves response times.

### Instant Unlock System

The application uses an "instant unlock" model where:

- Stage 1 is always free
- Stages 2 and 3 are locked initially (blurred in UI)
- Users can unlock all stages with a single click (no payment processing)
- The "$5 Buy Full Plan" button is for display only

### Three-Stage Content

1. **Stage 1: Trading Foundation** - Always unlocked, provides overview
2. **Stage 2: Personalized Execution Framework** - Locked until unlock
3. **Stage 3: Advanced Frameworks & Playbooks** - Locked until unlock

## 🐛 Troubleshooting

### Backend Issues

**Problem: `401 Unauthorized` from OpenAI API**
- **Solution**: Verify your `OPENAI_API_KEY` is correct and not expired
- Check for line breaks or extra spaces in the `.env` file
- Ensure the key is on a single line

**Problem: Database connection errors**
- **Solution**: Verify `DATABASE_URL` is correct
- For PostgreSQL, ensure the database exists and credentials are correct
- Check database server is running

**Problem: `ValidationError: Extra inputs are not permitted`**
- **Solution**: This is normal - the system ignores extra `.env` variables
- No action needed if the server starts successfully

### Frontend Issues

**Problem: API calls failing**
- **Solution**: Verify backend is running on `http://127.0.0.1:8000`
- Check `REACT_APP_API_URL` in `.env.local` if using custom backend URL
- Check browser console for CORS errors

**Problem: Summary not generating**
- **Solution**: Verify OpenAI API key is valid and has credits
- Check backend logs for error messages
- Ensure backend is running and accessible

### General Issues

**Problem: Cache not working**
- **Solution**: Verify database is accessible and writable
- Check that `answers_fingerprint` column exists in the `plans` table
- Clear database and restart if needed

## 📝 API Documentation

Once the backend is running, visit:

- **Swagger UI**: `http://127.0.0.1:8000/docs` - Interactive API documentation
- **ReDoc**: `http://127.0.0.1:8000/redoc` - Alternative API documentation

### Key Endpoints

- `POST /quiz/` - Submit quiz answers
- `POST /plan/` - Generate full plan (all 3 stages)
- `POST /plan/summary` - Generate Stage 1 summary only
- `GET /plan/{plan_id}` - Retrieve plan by ID
- `POST /auth/code` - Request authentication code
- `POST /auth/verify` - Verify authentication code
- `POST /checkout/session` - Instant unlock (no payment)

## 🎯 Next Steps After Setup

1. **Add Your OpenAI API Key** - Essential for content generation
2. **Test the Complete Flow** - Take the quiz and verify summary generation
3. **Test Unlock Functionality** - Verify Stages 2 & 3 unlock correctly
4. **Configure Email Service** (Optional) - For production email delivery
5. **Set Up Production Environment** - Configure production database and URLs
6. **Deploy to Production** - Follow production deployment guide

## 📧 Support

For issues or questions:

1. Check the troubleshooting section above
2. Review backend logs in `backend/logs/` directory
3. Check browser console for frontend errors
4. Verify all environment variables are set correctly

## 📄 License

[Specify your license here]

## 🙏 Acknowledgments

- OpenAI for GPT API
- FastAPI for backend framework
- React for frontend framework

---

**Version:** 2.1  
**Last Updated:** 2024

**Note:** This application requires a valid OpenAI API key to function. Make sure to add your API key to the `.env` file before running the application.
