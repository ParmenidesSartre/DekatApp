# Render.com Deployment Guide for SmartMaps SaaS

This guide will help you deploy your Django application to Render.com in 2025.

## Prerequisites

1. A [Render.com](https://render.com) account
2. Git repository (GitHub, GitLab, or Bitbucket)
3. Your code pushed to the repository

## Files Created for Deployment

- `requirements.txt` - Python dependencies
- `build.sh` - Build script for Render
- `render.yaml` - Infrastructure as Code configuration
- `.env.example` - Environment variables template
- `.gitignore` - Files to exclude from Git
- Updated `config/settings.py` - Production-ready settings

## Step 1: Prepare Your Repository

1. **Initialize Git (if not already done):**
   ```bash
   git init
   git add .
   git commit -m "Initial commit with Render deployment configuration"
   ```

2. **Push to your Git hosting service:**
   ```bash
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

## Step 2: Deploy to Render

### Option A: Using render.yaml (Recommended - Infrastructure as Code)

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Blueprint"**
3. Connect your repository
4. Render will automatically detect `render.yaml` and create:
   - Web Service (Django app)
   - PostgreSQL Database
5. Click **"Apply"**

### Option B: Manual Setup

1. **Create PostgreSQL Database:**
   - Go to Render Dashboard
   - Click **"New +"** → **"PostgreSQL"**
   - Name: `smartmaps-db`
   - Plan: Choose **Starter** (free for 90 days)
   - Click **"Create Database"**
   - Copy the **Internal Database URL**

2. **Create Web Service:**
   - Click **"New +"** → **"Web Service"**
   - Connect your repository
   - Configure:
     - **Name:** `smartmaps-saas`
     - **Runtime:** Python 3
     - **Build Command:** `./build.sh`
     - **Start Command:** `gunicorn config.wsgi:application`
   - Click **"Create Web Service"**

## Step 3: Configure Environment Variables

In your Render Web Service dashboard, go to **"Environment"** and add:

| Key | Value | Notes |
|-----|-------|-------|
| `SECRET_KEY` | Click "Generate" | Auto-generate a secure key |
| `DEBUG` | `False` | Never set to True in production |
| `ALLOWED_HOSTS` | `your-app-name.onrender.com` | Replace with your actual Render URL |
| `DATABASE_URL` | (Auto-set if using Blueprint) | From PostgreSQL database |
| `PYTHON_VERSION` | `3.12.0` | Optional, Render auto-detects |

## Step 4: First Deployment

1. Render will automatically build and deploy when you push to your repository
2. Check the **"Logs"** tab to monitor deployment progress
3. Initial deployment takes 3-5 minutes

## Step 5: Create Superuser

After first deployment, open the **Shell** tab in your Render Web Service and run:

```bash
python manage.py createsuperuser
```

Follow the prompts to create your admin account.

## Step 6: Configure Your Domain (Optional)

1. In Web Service settings, go to **"Settings"** → **"Custom Domain"**
2. Add your domain (e.g., `smartmaps.yourdomain.com`)
3. Update DNS records as instructed
4. Update `ALLOWED_HOSTS` environment variable with your custom domain

## Important Notes

### Media Files (User Uploads)

The current setup uses local file storage. For production, you should:

1. **Set up AWS S3 or Cloudinary:**
   - Add `django-storages` and `boto3` to requirements.txt
   - Configure S3 bucket
   - Update settings.py to use S3 for media files

2. **Why?** Render's file system is ephemeral - uploaded files will be lost on redeploy

### Static Files

- Static files are handled by **WhiteNoise** (already configured)
- Automatically served from `/staticfiles/` directory
- Compressed and cached for performance

### Database Backups

- Render's free PostgreSQL expires after 90 days
- For production, upgrade to paid plan with automatic backups
- Alternatively, set up manual backup cron jobs

### Security Checklist

✅ `DEBUG=False` in production
✅ Strong `SECRET_KEY` generated
✅ `ALLOWED_HOSTS` properly configured
✅ HTTPS enabled (automatic on Render)
✅ Security headers configured (in settings.py)
✅ Database connection pooling enabled

## Automatic Deploys

Render automatically deploys when you push to your main branch:

```bash
git add .
git commit -m "Update feature X"
git push origin main
```

## Monitoring & Logs

- **Logs:** Real-time logs in Render dashboard
- **Metrics:** CPU, Memory usage in "Metrics" tab
- **Health Checks:** Render automatically monitors your app

## Troubleshooting

### "No module named 'app'" Error
**Problem:** Render is using default start command instead of the one specified in render.yaml.

**Solution:**
1. Go to your Web Service in Render dashboard
2. Navigate to **Settings** → **Build & Deploy**
3. Set **Start Command** manually to: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
4. Click **Save Changes**
5. Trigger a manual deploy

### Build fails
- Check `build.sh` permissions: `chmod +x build.sh`
- Verify all dependencies in `requirements.txt`
- Check logs for specific error messages
- Ensure Python version is compatible (3.12.0)

### Database connection errors
- Verify `DATABASE_URL` is set correctly
- Ensure database and web service are in same region
- Check database is running and accessible
- Wait for database to fully initialize before first deploy

### Static files not loading
- Ensure `python manage.py collectstatic` runs in build.sh
- Verify `STATIC_ROOT` is set in settings.py
- Check WhiteNoise middleware is before other middleware

### 502 Bad Gateway
- Check start command is correct: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
- Verify `WSGI_APPLICATION` setting in settings.py
- Check logs for application startup errors
- Ensure `ALLOWED_HOSTS` includes your Render domain

### Database tables don't exist (ProgrammingError: relation does not exist)
**Problem:** Migrations didn't run during deployment, so database tables are missing.

**Solution:** Migrations now run automatically on every startup via the `start.sh` script. If you still see this error:
1. Check the startup logs to see if migrations ran successfully
2. Verify `DATABASE_URL` environment variable is set correctly
3. Ensure the database is accessible from your web service
4. Trigger a manual redeploy to run migrations again

## Cost Estimates (2025)

- **Free Tier:**
  - Web Service: Free (with limitations)
  - PostgreSQL: Free for 90 days

- **Starter Tier (Recommended for Production):**
  - Web Service: $7/month (512MB RAM, always on)
  - PostgreSQL: $7/month (256MB RAM, backups included)

- **Total:** ~$14/month for small production app

## Support

- [Render Documentation](https://render.com/docs)
- [Render Community](https://community.render.com/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)

## Next Steps After Deployment

1. Set up email service (SendGrid, Mailgun, or AWS SES)
2. Configure Google OAuth credentials for production domain
3. Set up AWS S3 for media file storage
4. Configure custom domain and SSL
5. Set up monitoring and error tracking (Sentry)
6. Create backup strategy for database and media files
