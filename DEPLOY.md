# Deploying Study Buddy to Vercel

## Prerequisites
1. A [Vercel account](https://vercel.com/signup)
2. A [Neon](https://neon.tech) or [Supabase](https://supabase.com) PostgreSQL database (both have free tiers)
3. Your code pushed to GitHub

## Step 1: Create a PostgreSQL Database

### Option A: Neon (Recommended)
1. Go to [neon.tech](https://neon.tech) and sign up
2. Create a new project
3. Copy the connection string (looks like `postgresql://user:pass@host/dbname`)

### Option B: Supabase
1. Go to [supabase.com](https://supabase.com) and sign up
2. Create a new project
3. Go to Settings → Database → Connection string → URI
4. Copy the connection string

## Step 2: Deploy to Vercel

### Via Vercel Dashboard (Easiest)
1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repository
3. Set the **Root Directory** to `studyB`
4. Add Environment Variables:
   - `DATABASE_URL` = your PostgreSQL connection string
   - `SECRET_KEY` = a random secure string (generate one: `python -c "import secrets; print(secrets.token_hex(32))"`)
   - `GROQ_API_KEY` = your Groq API key
   - `MAIL_USERNAME` = your Gmail address (optional)
   - `MAIL_PASSWORD` = your Gmail app password (optional)
5. Click Deploy

### Via CLI
```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy from studyB folder
cd studyB
vercel

# Set environment variables
vercel env add DATABASE_URL
vercel env add SECRET_KEY
vercel env add GROQ_API_KEY

# Deploy to production
vercel --prod
```

## Step 3: Initialize Database

After first deployment, the database tables will be created automatically on the first request.

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | Yes | Flask secret key for sessions |
| `GROQ_API_KEY` | Yes | API key from console.groq.com |
| `MAIL_USERNAME` | No | Gmail address for password reset |
| `MAIL_PASSWORD` | No | Gmail app password |

## Troubleshooting

### "Module not found" errors
Make sure all dependencies are in `requirements.txt`

### Database connection errors
- Check your `DATABASE_URL` is correct
- Ensure it starts with `postgresql://` (not `postgres://`)
- Check if your database allows connections from Vercel's IPs

### Static files not loading
The `vercel.json` routes static files correctly. If issues persist, check the paths.

## Local Development

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py
```
