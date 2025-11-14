# Bet Slip OCR Implementation Guide

## Overview
Use Vision-capable LLMs to extract bet information from uploaded bet slip images.

## Option 1: OpenAI GPT-4 Vision (Recommended)

### Setup
```bash
pip install openai pillow
```

### Backend Implementation (Flask)
```python
import openai
import base64
from flask import request, jsonify

# In app.py
openai.api_key = os.getenv('OPENAI_API_KEY')

@app.route('/api/upload-betslip', methods=['POST'])
def upload_betslip():
    """Extract bet information from uploaded image using GPT-4 Vision"""
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    image_file = request.files['image']
    
    # Read and encode image
    image_data = base64.b64encode(image_file.read()).decode('utf-8')
    
    # Create prompt for GPT-4 Vision
    prompt = """
    Analyze this bet slip image and extract ALL information in JSON format.
    
    Extract:
    - bet_site: Name of betting platform (DraftKings, FanDuel, etc.)
    - bet_type: "parlay" or "single"
    - total_odds: American odds format (e.g., +450, -110)
    - wager_amount: Dollar amount wagered
    - potential_payout: Potential winnings
    - bet_date: Date of bet (if visible)
    - legs: Array of individual bets, each containing:
      - sport: NFL, NBA, MLB, NHL, etc.
      - player_name: Full player name (for props)
      - team_name: Full team name
      - bet_type: "player_prop", "moneyline", "spread", "total"
      - stat_type: For props (e.g., "Passing Yards", "Receiving Yards", "Points")
      - bet_line_type: "over" or "under" (for props/totals)
      - target_value: The line (e.g., 250.5 for yards, 6.5 for spread)
      - odds: Individual leg odds (e.g., -110)
      - game_info: "Away Team @ Home Team" format
      - game_date: Date of game (if visible)
    
    Return ONLY valid JSON. If information is unclear or missing, use null.
    
    Example output:
    {
      "bet_site": "DraftKings",
      "bet_type": "parlay",
      "total_odds": "+450",
      "wager_amount": 25.00,
      "potential_payout": 137.50,
      "bet_date": "2024-11-12",
      "legs": [
        {
          "sport": "NFL",
          "player_name": "Justin Jefferson",
          "bet_type": "player_prop",
          "stat_type": "Receiving Yards",
          "bet_line_type": "over",
          "target_value": 75.5,
          "odds": "-110",
          "game_info": "Vikings @ Bears",
          "game_date": "2024-11-12"
        }
      ]
    }
    """
    
    try:
        # Call GPT-4 Vision API
        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",  # or "gpt-4o" for newer model
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000,
            temperature=0.1  # Low temperature for consistent extraction
        )
        
        # Parse response
        extracted_data = response.choices[0].message.content
        bet_data = json.loads(extracted_data)
        
        # Validate and insert into database
        # (Use existing insertion logic from manual bet entry)
        
        return jsonify({
            'success': True,
            'data': bet_data,
            'message': 'Bet slip processed successfully'
        })
        
    except json.JSONDecodeError:
        return jsonify({'error': 'Failed to parse bet data'}), 500
    except Exception as e:
        app.logger.error(f"Bet slip extraction error: {e}")
        return jsonify({'error': str(e)}), 500
```

### Frontend (HTML + JavaScript)
```html
<!-- Add to your HTML -->
<div class="upload-section">
    <h3>Upload Bet Slip</h3>
    <input type="file" id="betslipImage" accept="image/*" capture="camera">
    <button onclick="uploadBetSlip()">Extract Bet Info</button>
    <div id="extractedData"></div>
</div>

<script>
async function uploadBetSlip() {
    const fileInput = document.getElementById('betslipImage');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select an image');
        return;
    }
    
    const formData = new FormData();
    formData.append('image', file);
    
    // Show loading state
    document.getElementById('extractedData').innerHTML = 'Processing image...';
    
    try {
        const response = await fetch('/api/upload-betslip', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Display extracted data for user review
            displayExtractedBet(result.data);
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Upload error:', error);
        alert('Failed to process bet slip');
    }
}

function displayExtractedBet(data) {
    // Show extracted data in a form for user to review/edit before submitting
    const html = `
        <div class="extracted-bet">
            <h4>Review Extracted Bet</h4>
            <p><strong>Site:</strong> ${data.bet_site}</p>
            <p><strong>Type:</strong> ${data.bet_type}</p>
            <p><strong>Odds:</strong> ${data.total_odds}</p>
            <p><strong>Wager:</strong> $${data.wager_amount}</p>
            <p><strong>Potential Payout:</strong> $${data.potential_payout}</p>
            
            <h5>Legs:</h5>
            <ul>
                ${data.legs.map(leg => `
                    <li>
                        ${leg.player_name || leg.team_name} - 
                        ${leg.stat_type || leg.bet_type} 
                        ${leg.bet_line_type || ''} ${leg.target_value || ''}
                        (${leg.odds})
                    </li>
                `).join('')}
            </ul>
            
            <button onclick="confirmAndSaveBet(${JSON.stringify(data)})">
                Confirm & Save Bet
            </button>
            <button onclick="editBet(${JSON.stringify(data)})">
                Edit Before Saving
            </button>
        </div>
    `;
    
    document.getElementById('extractedData').innerHTML = html;
}
</script>
```

---

## Option 2: Claude 3 Vision (Anthropic)

### Setup
```bash
pip install anthropic
```

### Implementation
```python
import anthropic

client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

@app.route('/api/upload-betslip-claude', methods=['POST'])
def upload_betslip_claude():
    image_file = request.files['image']
    image_data = base64.b64encode(image_file.read()).decode('utf-8')
    
    message = client.messages.create(
        model="claude-3-opus-20240229",  # or claude-3-sonnet for cheaper
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Extract bet information from this image in JSON format... [same prompt as above]"
                    }
                ],
            }
        ],
    )
    
    # Parse and return
    bet_data = json.loads(message.content[0].text)
    return jsonify({'success': True, 'data': bet_data})
```

---

## Option 3: Google Gemini Vision (Budget)

### Setup
```bash
pip install google-generativeai
```

### Implementation
```python
import google.generativeai as genai

genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

@app.route('/api/upload-betslip-gemini', methods=['POST'])
def upload_betslip_gemini():
    from PIL import Image
    import io
    
    image_file = request.files['image']
    image = Image.open(io.BytesIO(image_file.read()))
    
    model = genai.GenerativeModel('gemini-pro-vision')
    response = model.generate_content([
        "Extract bet information from this image in JSON format... [same prompt]",
        image
    ])
    
    bet_data = json.loads(response.text)
    return jsonify({'success': True, 'data': bet_data})
```

---

## Cost Comparison

| Provider | Model | Cost per Image | Quality | Speed |
|----------|-------|----------------|---------|-------|
| OpenAI | GPT-4o | ~$0.01 | ⭐⭐⭐⭐⭐ | Fast |
| Anthropic | Claude 3 Opus | ~$0.015 | ⭐⭐⭐⭐⭐ | Fast |
| Anthropic | Claude 3 Sonnet | ~$0.003 | ⭐⭐⭐⭐ | Fast |
| Google | Gemini Pro Vision | ~$0.0025 | ⭐⭐⭐⭐ | Medium |

---

## Implementation Roadmap

### Phase 1: Basic OCR (1-2 days)
1. Add file upload endpoint to Flask
2. Integrate GPT-4 Vision API
3. Display extracted data in UI for review

### Phase 2: Validation & Editing (2-3 days)
1. Let users review/edit extracted data before saving
2. Add confidence scores
3. Handle unclear/missing fields

### Phase 3: Auto-insertion (1 day)
1. Parse JSON and insert directly into database
2. Use existing bet insertion logic
3. Handle errors gracefully

### Phase 4: Improvements (ongoing)
1. Support multiple bet slip formats
2. Add bet site templates for better accuracy
3. Handle handwritten notes
4. Mobile app integration

---

## Best Practices

### 1. Always Review Before Saving
- Show extracted data to user for confirmation
- Allow manual editing of incorrect fields
- Track accuracy metrics

### 2. Handle Edge Cases
- Multiple bets on one slip
- Partial visibility
- Unusual bet types
- Foreign languages

### 3. Optimize Costs
- Compress images before sending (max 1024px width)
- Cache common bet slip templates
- Use cheaper models for simple slips

### 4. Security
- Validate file types (only images)
- Limit file size (max 10MB)
- Store images temporarily, delete after processing
- Don't expose API keys to frontend

---

## Environment Variables Required

Add to your `.env` file:
```bash
# Choose one or more
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
```

---

## Mobile-Friendly Considerations

```html
<!-- Optimize for mobile camera -->
<input 
    type="file" 
    accept="image/*" 
    capture="environment"  <!-- Use rear camera on mobile -->
    id="betslipCamera"
>

<style>
/* Make upload button prominent on mobile */
@media (max-width: 768px) {
    .upload-section {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
    }
    
    .upload-button {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: #007bff;
        color: white;
        font-size: 24px;
    }
}
</style>
```

---

## Testing Strategy

1. **Test with real bet slips** from major sites:
   - DraftKings
   - FanDuel
   - BetMGM
   - Caesars

2. **Edge cases to test:**
   - Blurry images
   - Poor lighting
   - Partial screenshots
   - Different bet types (parlays, teasers, round robins)

3. **Accuracy tracking:**
   - Log extraction accuracy
   - Track which fields are most error-prone
   - Improve prompts based on failures

---

## Next Steps

1. Choose your Vision LLM provider (recommend starting with OpenAI GPT-4 Vision)
2. Get API key from provider
3. Implement the upload endpoint in `app.py`
4. Add upload button to your frontend
5. Test with real bet slips
6. Iterate on the prompt to improve accuracy

**Estimated development time: 3-5 days for MVP**
