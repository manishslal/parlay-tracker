# 🔧 PWA Reinstallation Guide (Android)

## The Problem
When you first installed the app, the manifest.json wasn't properly configured, so Android registered it as just a shortcut to the website instead of a true PWA.

## The Fix
I've made two critical changes:

1. **Added `scope` to manifest.json** - Tells Android this is a full app, not just a bookmark
2. **Added explicit routes in app.py** - Ensures manifest.json, service-worker.js, and icons are served correctly

## 📱 How to Reinstall (Takes 2 minutes)

### Step 1: Uninstall the Old Version
1. **Find the app icon** on your home screen
2. **Long press** on the icon
3. Select **"Remove"** or **"Uninstall"** or **"Remove from Home screen"**
4. Confirm removal

### Step 2: Clear Chrome Cache (Important!)
1. Open **Chrome** on your phone
2. Tap the **three dots menu** (⋮) → **Settings**
3. Scroll to **Privacy and security** → **Clear browsing data**
4. Select **Time range: All time**
5. Check:
   - ✅ **Cookies and site data**
   - ✅ **Cached images and files**
6. Tap **Clear data**

### Step 3: Wait for Render Deployment (~2 minutes)
The fixes are deploying to Render right now. Wait about 2 minutes before proceeding.

You can check deployment status at: https://dashboard.render.com

### Step 4: Reinstall as PWA
1. Open **Chrome** (not any other browser)
2. Go to your app URL: `https://your-app-name.onrender.com`
3. Look for the install prompt at the bottom of the screen:
   - "Add Parlay Tracker to Home screen"
   - Or tap the **three dots menu** (⋮) → **"Install app"** or **"Add to Home screen"**
4. Tap **"Install"** or **"Add"**
5. Chrome should say something like "Parlay Tracker installed"

### Step 5: Test Standalone Mode
1. **Close Chrome completely** (swipe it away from recent apps)
2. Go to your **home screen**
3. **Tap the new app icon**
4. **Verify**: The app should open **WITHOUT** any browser UI:
   - ❌ No address bar at the top
   - ❌ No Chrome tabs
   - ❌ No browser menu button
   - ✅ Just the app, full screen
   - ✅ Status bar at top matches app theme (purple)

### Step 6: Verify It's Working
- The app should feel like a native app
- Switching between apps should show "Parlay Tracker" as a separate app (not Chrome)
- The back button should navigate within the app, not close it

---

## 🐛 Still Not Working?

If it still opens in Chrome after reinstalling:

### Option A: Force PWA Install
1. In Chrome, go to your app URL
2. Tap **three dots menu** (⋮) → **Settings** (while on your site)
3. Look for **"Add to Home screen"** or **"Install app"**
4. Make sure it says **"Install"** not just "Add to Home screen"

### Option B: Check Manifest Loading
1. In Chrome on your phone, open your app
2. Type in the address bar: `chrome://inspect/#devices`
3. Or tap menu → **More tools** → **Developer tools**
4. Check **Console** tab for errors mentioning manifest.json

### Option C: Manual Verification
1. In Chrome, go to: `https://your-app.onrender.com/manifest.json`
2. You should see the JSON manifest
3. Verify it includes: `"display": "standalone"` and `"scope": "/"`

### Option D: Try Another PWA-Compatible Browser
- **Chrome** (recommended for Android)
- **Samsung Internet** (also supports PWA)
- **Microsoft Edge** (supports PWA)

---

## ✅ Success Indicators

You'll know it worked when:
- ✅ App opens **without** Chrome's address bar
- ✅ App appears as separate entry in recent apps (not under Chrome)
- ✅ Status bar color matches app theme (purple: #140d52)
- ✅ App has proper icon (purple "P" logo)
- ✅ Full-screen experience (no browser UI)

---

## 🎯 What Changed?

### Before:
```json
"start_url": "/",
"display": "standalone"
```

### After:
```json
"start_url": "/?source=pwa",
"scope": "/",
"display": "standalone"
```

The `scope` property tells Android: "Everything under this domain is part of the app," which is required for true standalone mode.

### Plus:
Added explicit Flask routes for:
- `/manifest.json` (with correct MIME type)
- `/service-worker.js`
- `/media/icons/*` (all app icons)

This ensures Android can fetch all PWA files without authentication issues.

---

## 📊 Verification Checklist

After reinstalling, verify:

- [ ] App icon appears on home screen with purple "P" logo
- [ ] Tapping icon opens app WITHOUT browser UI
- [ ] Status bar is purple (not white/gray)
- [ ] Recent apps shows "Parlay Tracker" as separate app
- [ ] Back button navigates within app (doesn't close it immediately)
- [ ] App feels native (smooth, integrated with Android)

---

## 🚀 Next Steps After Installation Works

Once you confirm standalone mode is working:

1. **Phase 2: Upgrade Render to Starter** ($7/mo)
   - Eliminates cold starts
   - Always-on for instant access

2. **Phase 3: Add Authentication**
   - Password-protect admin functions
   - Secure data modifications

---

## 💡 Pro Tip

After successful installation, you can:
- Add the app to your dock for quick access
- Use Android's "Digital Wellbeing" to track usage
- The app will work partially offline thanks to service worker caching
- Updates happen automatically (checks hourly)

---

**Questions?** Let me know if you need help debugging!
