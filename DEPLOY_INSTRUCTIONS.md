# Deploy to Render - Step by Step Guide

## Prerequisites
- A GitHub account (free)
- A Render account (free) - sign up at https://render.com

## Step-by-Step Deployment

### Step 1: Create a GitHub Repository

1. Go to https://github.com and sign in
2. Click the **"+"** button (top right) → **"New repository"**
3. Name it: `epl-exciting-games` (or any name you like)
4. Choose **"Public"** (required for free tier)
5. **Don't** initialize with README (we already have files)
6. Click **"Create repository"**

### Step 2: Push Your Code to GitHub

Open a terminal in your project folder and run these commands:

```powershell
# Initialize git repository
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial commit - EPL Exciting Game Finder"

# Connect to your GitHub repo (replace YOUR-USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR-USERNAME/epl-exciting-games.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Note:** You'll need to enter your GitHub credentials. Use a Personal Access Token instead of password.

### Step 3: Deploy on Render

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Click **"Connect a repository"** 
4. Find and select your `epl-exciting-games` repository
5. Render will auto-detect the `render.yaml` configuration:
   - **Name:** epl-exciting-games (or customize it)
   - **Environment:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:server --bind 0.0.0.0:$PORT`
6. Select **"Free"** instance type
7. Click **"Create Web Service"**

### Step 4: Wait for Deployment

- Render will build and deploy your app (takes 2-5 minutes)
- Watch the logs in the Render dashboard
- Once it shows "Your service is live", you're done!

### Step 5: Access Your App

- Render will give you a URL like: `https://epl-exciting-games.onrender.com`
- Open it in any browser, including your Pixel phone!

## Important Notes

### Free Tier Limitations:
- **App sleeps after 15 minutes** of inactivity
- First request after sleeping takes ~30-60 seconds to wake up
- 750 hours/month (plenty for personal use)

### Keeping Your App Awake (Optional):
- Use a service like **UptimeRobot** (free) to ping your app every 14 minutes
- This keeps it from sleeping during the day

### Troubleshooting:
- If deployment fails, check the logs in Render dashboard
- Make sure all files were pushed to GitHub
- Verify `requirements.txt` has all dependencies

## Alternative: Manual Render Deployment (No GitHub)

If you don't want to use GitHub, you can also deploy manually:
1. On Render dashboard, choose **"Web Service"** → **"Deploy from Git repository"** is not required
2. But this is more manual and less convenient for updates

## Need Help?

If something goes wrong:
- Check Render deployment logs
- Verify your GitHub repo has all files
- Make sure the repo is public (required for free tier)
