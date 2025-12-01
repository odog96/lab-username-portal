# Lab Username Portal - Alpha Version

Simple username assignment for hands-on labs with downloadable instructions.

## 🎯 How It Works

### Setup (Admin)
1. Deploy app to Cloudera AI
2. Visit: `https://your-app-url.cdsw.io/admin`
3. Configure lab settings:
   - Lab name (e.g., "AI Workshop 2024")
   - Max users (e.g., 150)
   - **Password** (shared by all users)
   - **Lab URL** (link for users to access the lab)
4. Upload `lab-readme.pdf` to `/home/cdsw/`
5. Share portal URL with participants

### User Experience
1. Visit `https://your-app-url.cdsw.io`
2. Download PDF instructions (optional)
3. Enter email → get username (user001, user002, etc.)
4. **View assigned username, password, and lab URL**
5. Same email → same username (no duplicates, credentials redisplayed)

## 📦 Deployment to Cloudera AI

### Files to Upload
```
/home/cdsw/
  ├── app-alpha.py
  ├── requirements.txt
  └── lab-readme.pdf (your lab instructions)
```

### Create Application
```
Name: Lab Username Portal
Script: app-alpha.py
Kernel: Python 3.9+
Engine: 1 vCPU / 2 GB RAM
```

### Configure
1. App deploys to: `https://[subdomain].ml-xxxxx.cdsw.io`
2. Visit: `/admin` endpoint
3. Set max users and lab name
4. Save configuration

### Share
Users visit: `https://[subdomain].ml-xxxxx.cdsw.io`

## 📄 PDF Download Feature

**Setup:**
- Create your lab instructions as PDF
- Name: `lab-readme.pdf`
- Upload to: `/home/cdsw/` (same directory as app)
- Download link appears automatically on user page

**URL:** `https://your-app-url.cdsw.io/download/readme`

**Performance:** Single replica handles 150 concurrent downloads. Add replicas if needed.

## 📊 Admin Dashboard

**Access:** `https://your-app-url.cdsw.io/admin`

**Features:**
- Configure lab name and max users
- **Set shared password for all users**
- **Set lab URL for all users**
- View real-time assignments
- See email-to-username mappings
- Reset everything for next lab

## 💾 Data Storage

Auto-created JSON files:

**lab_config.json:**
```json
{
  "max_users": 150,
  "lab_name": "AI Workshop",
  "password": "Lab2024!",
  "url": "https://lab.example.com"
}
```

**lab_assignments.json:**
```json
{
  "email_to_user": {
    "john@company.com": 1
  },
  "assigned_users": [1]
}
```

## 🔄 Workflow

**First Lab:**
```
1. Deploy and upload PDF
2. Configure at /admin
3. Share URL
```

**Next Lab:**
```
1. /admin → Reset Everything
2. Update PDF if needed
3. Reconfigure and share
```

## 📱 User Experience

**New User:**
```
Downloads PDF → Enters email → Gets:
  - Username: user001
  - Password: Lab2024!
  - Lab URL: https://lab.example.com (clickable link)
```

**Returning User:**
```
Enters email → "You already have a username: user001"
  - Username: user001 (same as before)
  - Password: Lab2024!
  - Lab URL: https://lab.example.com
```

**Lab Full:**
```
"All 150 slots have been assigned."
```

## 🛠️ API Endpoints

**User:**
- `GET /` - Portal
- `GET /download/readme` - PDF download
- `POST /api/request-username` - Get username

**Admin:**
- `GET /admin` - Dashboard
- `GET/POST /api/config` - Settings
- `GET /api/admin/assignments` - List all
- `POST /api/admin/reset` - Reset everything

## 🆘 Troubleshooting

**"Lab not configured"** → Visit `/admin`, set max users

**PDF download fails** → Verify `lab-readme.pdf` in `/home/cdsw/`

**"All slots assigned"** → Reset or increase max users

**Slow downloads** → Add CML replicas

**Assignments lost** → Check JSON file persistence

## 📁 Final Structure

```
/home/cdsw/
  ├── app-alpha.py
  ├── requirements.txt
  ├── lab-readme.pdf
  ├── lab_config.json (auto-created)
  └── lab_assignments.json (auto-created)
```

---

**Alpha Version:** Username assignment + downloadable instructions.
