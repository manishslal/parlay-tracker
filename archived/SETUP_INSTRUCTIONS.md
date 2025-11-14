# Bet Slip OCR Setup Instructions

## ✅ What's Been Completed

1. **Backend API Endpoint** ✓
   - `/api/upload-betslip` route added to Flask
   - Uses GPT-4 Vision to extract bet information
   - Returns structured JSON with all bet details

2. **Frontend UI** ✓
   - Purple "📷 Upload Bet Slip" button in header
   - Mobile-friendly file input (uses camera on phones)
   - Beautiful modal with loading spinner
   - Displays extracted data for review

3. **Dependencies** ✓
   - `openai==1.54.4` installed
   - `Pillow==10.4.0` installed
   - All packages added to `requirements.txt`

4. **Configuration Files** ✓
   - `.env` updated with `OPENAI_API_KEY` placeholder
   - All changes committed and pushed to GitHub

---

## 🔴 ACTION REQUIRED: Get Your OpenAI API Key

### Step 1: Sign Up for OpenAI Account
1. Go to: https://platform.openai.com/signup
2. Sign up with your email or Google account
3. Complete verification

### Step 2: Add Payment Method
1. Go to: https://platform.openai.com/settings/organization/billing/overview
2. Add a credit card
3. Add at least $5-10 credit (won't use much - ~$0.01 per image)

### Step 3: Create API Key
1. Go to: https://platform.openai.com/api-keys
2. Click **"Create new secret key"**
3. Give it a name like "Parlay Tracker OCR"
4. Select permissions: **All** or **GPT-4 Vision access**
5. **Copy the key immediately** (starts with `sk-...`)

### Step 4: Add Key to Your .env File
1. Open `/Users/manishslal/Desktop/Scrapper/.env`
2. Find the line: `OPENAI_API_KEY=your-openai-api-key-here`
3. Replace with your actual key:
   ```bash
   OPENAI_API_KEY=sk-proj-abcd1234...your-actual-key-here
   ```
4. Save the file
5. **IMPORTANT**: Never commit this key to GitHub!

### Step 5: Verify It Works Locally
1. Stop your Flask server if running (Ctrl+C)
2. Restart it:
   ```bash
   cd /Users/manishslal/Desktop/Scrapper
   .venv/bin/python app.py
   ```
3. Open http://localhost:5000
4. Click the "📷 Upload Bet Slip" button
5. Upload a bet slip screenshot
6. Wait ~3-5 seconds for processing
7. Review the extracted data!

### Step 6: Deploy to Render
1. Go to your Render dashboard
2. Find your parlay-tracker service
3. Go to **Environment** tab
4. Add new environment variable:
   - **Key**: `OPENAI_API_KEY`
   - **Value**: `sk-proj-your-actual-key`
5. Click **Save**
6. Render will auto-redeploy

---

## 📱 How to Use the Feature

### On Desktop:
1. Take a screenshot of your bet slip
2. Open your app
3. Click "📷 Upload Bet Slip"
4. Select the screenshot
5. Wait for AI processing
6. Review extracted data
7. Click "Confirm & Save Bet" (coming in Step 5)

### On Mobile:
1. Open your app on phone
2. Click "📷 Upload Bet Slip"
3. Camera opens automatically
4. Take photo of bet slip
5. AI extracts all info
6. Review and confirm

---

## 💰 Cost Information

- **Per bet slip**: ~$0.01
- **100 bet slips**: ~$1.00
- **GPT-4o pricing**: $0.005 per image input

Very affordable! Much cheaper than building a custom ML model.

---

## 🔧 What's Next

### Step 5: Implement Save Functionality
We need to create an endpoint that takes the extracted JSON and inserts it into your database. This will:
- Create the bet record
- Create all bet leg records
- Link them together properly
- Apply team name normalization
- Default the sport field

### Step 6: Testing
Test with bet slips from:
- ✅ DraftKings
- ✅ FanDuel
- ✅ BetMGM
- ✅ Caesars
- ✅ Other sites

We'll iterate on the prompt to improve accuracy.

---

## 🐛 Troubleshooting

### "OpenAI API key not configured" error
- Make sure you added the key to `.env`
- Make sure to remove `your-openai-api-key-here` placeholder
- Restart the Flask server after adding the key
- On Render, make sure you added it to Environment variables

### "Failed to process bet slip" error
- Check if your OpenAI account has credit
- Verify the API key is valid (no typos)
- Check the app logs for details: `tail -f app.log`

### Image upload not working
- Make sure file size is under 10MB
- Supported formats: JPG, PNG, WEBP, GIF
- Try a different browser if issues persist

### Extracted data is incorrect
- This is expected initially - we'll tune the AI prompt
- For now, you can manually edit before saving
- Report issues so we can improve the prompt

---

## 📝 Current Limitations

1. **No save functionality yet** - Step 5 will add this
2. **No editing before save** - coming soon
3. **No batch upload** - one image at a time for now
4. **English only** - may not work with other languages

---

## 🎯 Success Metrics

After you add the API key, test it with 5 different bet slips and check:
- ✅ Bet site identified correctly
- ✅ Total odds extracted
- ✅ All legs captured
- ✅ Player names correct
- ✅ Team names correct
- ✅ Bet types identified (prop/spread/ML/total)
- ✅ Lines/targets extracted

Report any issues and we'll improve the AI prompt!

---

## 🔐 Security Notes

- **Never** commit your OpenAI API key to GitHub
- The `.env` file is in `.gitignore` (safe)
- On Render, environment variables are encrypted
- Each API call is logged for debugging
- Images are processed in memory (not stored permanently)

---

## 📞 Need Help?

If you run into issues:
1. Check the app logs: `tail -f app.log`
2. Check browser console (F12)
3. Test with a simple bet slip first (single bet, not parlay)
4. Take a clear, well-lit photo

Let me know once you've added the API key and we'll test it together!
