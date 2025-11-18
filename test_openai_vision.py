#!/usr/bin/env python3
"""
Test script to debug OpenAI Vision API calls for bet slip OCR.
This will help us understand what the API returns and debug parsing issues.
"""

import os
import base64
import requests
import json
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import io

# Load environment variables from .env file
load_dotenv()

def create_test_bet_slip_image():
    """Create a simple test image with bet slip text."""
    # Create a white image
    img = Image.new('RGB', (600, 400), color='white')
    draw = ImageDraw.Draw(img)

    # Try to use a default font
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
        small_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Draw bet slip content
    y_pos = 20
    draw.text((20, y_pos), "DRAFTKINGS BET SLIP", fill='black', font=font)
    y_pos += 40

    draw.text((20, y_pos), "Bet Type: Parlay", fill='black', font=small_font)
    y_pos += 25
    draw.text((20, y_pos), "Wager: $10.00", fill='black', font=small_font)
    y_pos += 25
    draw.text((20, y_pos), "Odds: +250", fill='black', font=small_font)
    y_pos += 25
    draw.text((20, y_pos), "Potential Payout: $35.00", fill='black', font=small_font)
    y_pos += 40

    draw.text((20, y_pos), "Leg 1: Los Angeles Lakers -4.5", fill='black', font=small_font)
    y_pos += 25
    draw.text((20, y_pos), "Leg 2: Boston Celtics ML", fill='black', font=small_font)
    y_pos += 25
    draw.text((20, y_pos), "Leg 3: Game Total Over 220.5", fill='black', font=small_font)

    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    return base64.b64encode(img_bytes.getvalue()).decode('utf-8')

def encode_image_to_base64(image_path):
    """Encode an image file to base64 string."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"❌ Error encoding image: {e}")
        return None

def test_openai_vision_api(image_path=None, image_url=None, image_data=None):
    """
    Test the OpenAI Vision API with either a local image file or URL.
    """

    # Get API key
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print('❌ OPENAI_API_KEY not found in environment variables')
        print('💡 Make sure to set: export OPENAI_API_KEY="your-key-here"')
        return None

    print('✅ OpenAI API key found')

    # Prepare image data
    image_b64 = None
    if image_path:
        print(f'📁 Using local image: {image_path}')
        image_b64 = encode_image_to_base64(image_path)
        if not image_b64:
            return None
    elif image_data:
        print('🖼️  Using provided image data')
        image_b64 = image_data
    elif image_url:
        print(f'🌐 Using image URL: {image_url}')
        # For URLs, we'll pass the URL directly to OpenAI
    else:
        print('⚠️  No image provided, using a minimal test image')
        # Minimal 1x1 pixel PNG for testing API connectivity
        image_b64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='

    # Prepare the API request
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    # Build the content array
    content = [
        {
            'type': 'text',
            'text': '''Extract betting information from this bet slip image. You are an expert at reading sports betting slips. Return ONLY a valid JSON object with this exact structure. Do not include any markdown formatting, code blocks, or additional text.

CRITICAL INSTRUCTIONS:
- Look for the betting site name (DraftKings, FanDuel, BetMGM, Caesars, etc.)
- Identify the bet type: "parlay" for multiple legs, "single" for one leg, "teaser" for adjusted spreads, "round_robin" for combinations
- Extract the total wager amount and potential payout
- Parse each betting leg carefully - these are the individual bets that make up the parlay/single

FOR EACH LEG, identify:
- Player name (for player props) or team name (for game bets)
- The stat being bet on (points, rebounds, passing yards, total points, spread, moneyline, etc.)
- The betting line (the number, like +4.5, -110, over 45.5, etc.)
- Whether it's over/under for totals, or the direction for spreads
- Individual leg odds if shown separately

EXAMPLES of how to parse different bet types:

Moneyline: "Los Angeles Lakers ML" → team: "Los Angeles Lakers", stat: "moneyline", line: 0
Spread: "Boston Celtics -3.5" → team: "Boston Celtics", stat: "spread", line: -3.5
Total: "Game Total Over 220.5" → team: "Game Total", stat: "total_points", line: 220.5, stat_add: "over"
Player Prop: "LeBron James Over 25.5 Points" → player: "LeBron James", team: "Los Angeles Lakers", stat: "points", line: 25.5, stat_add: "over"

{
  "bet_site": "name of the betting site (e.g., DraftKings, FanDuel, Caesars, BetMGM)",
  "bet_type": "parlay|single|teaser|round_robin",
  "total_odds": "number like +150, -120, or the American odds format",
  "wager_amount": "number like 10.00, 25.50 - the amount being wagered",
  "potential_payout": "number like 35.00 - total amount you'd receive including wager",
  "bet_date": "YYYY-MM-DD format if visible, otherwise omit",
  "legs": [
    {
      "player": "Player name (ONLY for player props, otherwise omit this field)",
      "team": "Team name or 'Game Total' for totals bets",
      "stat": "stat type: 'moneyline', 'spread', 'total_points', 'passing_yards', 'points', 'rebounds', 'assists', etc.",
      "line": "the betting line as a number: -3.5, +150, 25.5, 220.5, etc.",
      "stat_add": "'over' or 'under' for totals/player props, omit for moneyline/spread",
      "odds": "leg-specific odds if shown (like -110), otherwise omit"
    }
  ]
}

IMPORTANT:
- Only include fields that are clearly visible in the image
- For team names, use the full name as shown (e.g., "Kansas City Chiefs", not "Chiefs")
- For stats, be specific: "passing_yards" not "passing", "total_points" not "totals"
- If a leg has both player and team, include both fields
- Return ONLY the JSON object, no explanations or additional text.'''
        }
    ]

    # Add image content
    if image_url:
        content.append({
            'type': 'image_url',
            'image_url': {'url': image_url}
        })
    else:
        content.append({
            'type': 'image_url',
            'image_url': {'url': f'data:image/png;base64,{image_b64}'}
        })

    payload = {
        'model': 'gpt-4o',
        'messages': [{'role': 'user', 'content': content}],
        'max_tokens': 1500,
        'temperature': 0.1  # Low temperature for consistent parsing
    }

    try:
        print('🔄 Making API call to OpenAI Vision API...')
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=60
        )

        print(f'📊 Response status: {response.status_code}')

        if response.status_code == 200:
            result = response.json()
            print('✅ API call successful')

            if 'choices' in result and result['choices']:
                content = result['choices'][0]['message']['content']
                print('\n📄 Raw content received:')
                print('=' * 50)
                print(content)
                print('=' * 50)

                # Try to parse as JSON
                try:
                    parsed = json.loads(content)
                    print('✅ Content is valid JSON')
                    print('\n📋 Parsed structure:')
                    print(json.dumps(parsed, indent=2))

                    # Validate structure
                    required_fields = ['bet_site', 'bet_type', 'legs']
                    missing_fields = [field for field in required_fields if field not in parsed]
                    if missing_fields:
                        print(f'⚠️  Missing required fields: {missing_fields}')
                    else:
                        print('✅ All required fields present')

                    return parsed

                except json.JSONDecodeError as e:
                    print(f'❌ Content is not valid JSON: {e}')

                    # Try to extract JSON from the content
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        try:
                            extracted = json.loads(json_match.group())
                            print('✅ Found JSON in content:')
                            print(json.dumps(extracted, indent=2))
                            return extracted
                        except json.JSONDecodeError as e2:
                            print(f'❌ Extracted content is not valid JSON: {e2}')
                    else:
                        print('❌ No JSON found in content')

                    return None
            else:
                print('❌ No choices in response')
                print('Full response:', json.dumps(result, indent=2))
                return None
        else:
            print(f'❌ API call failed: {response.status_code}')
            try:
                error_data = response.json()
                print('Error details:', json.dumps(error_data, indent=2))
            except:
                print('Error response:', response.text[:500])
            return None

    except requests.exceptions.Timeout:
        print('❌ Request timed out')
        return None
    except Exception as e:
        print(f'❌ Exception during API call: {e}')
        return None

def test_transform_function():
    """Test the transform_extracted_bet_data function with sample OCR data."""
    # Copy the transform function locally to avoid import issues
    def transform_extracted_bet_data(data):
        """Transform frontend extracted bet data to internal format."""
        # Map frontend field names to internal format
        transformed = {
            'wager': float(data.get('wager_amount', 0)) if data.get('wager_amount') else None,
            'potential_winnings': float(data.get('potential_payout', 0)) if data.get('potential_payout') else None,
            'final_odds': data.get('total_odds'),
            'bet_date': data.get('bet_date'),
            'betting_site_id': data.get('bet_site'),
            'bet_type': data.get('bet_type', 'parlay'),
            'legs': []
        }

        # Transform legs
        for leg in data.get('legs', []):
            # Determine the display bet type from the stat
            stat = leg.get('stat', '')
            display_bet_type = 'spread' if 'spread' in stat.lower() else \
                              'moneyline' if 'moneyline' in stat.lower() or stat.lower() == 'ml' else \
                              'total' if 'total' in stat.lower() or 'points' in stat.lower() else \
                              stat.lower()

            # Determine home_team and away_team based on bet type
            team_name = leg.get('team', '')
            if team_name == 'Game Total' or display_bet_type == 'total':
                # For totals, we don't have specific teams
                home_team = 'Game Total'
                away_team = 'Game Total'
            elif display_bet_type == 'moneyline' or display_bet_type == 'spread':
                # For game bets, try to split the team name or use defaults
                home_team = team_name
                away_team = 'TBD'  # We'll need to determine this from game data later
            else:
                # For player props, use the player's team
                player_team = leg.get('team', '')
                home_team = player_team
                away_team = 'TBD'

            transformed_leg = {
                'player_name': leg.get('player'),
                'team_name': leg.get('team'),
                'stat_type': leg.get('stat'),  # Frontend expects stat_type for display
                'bet_type': display_bet_type,  # Frontend also checks bet_type for logic
                'target_value': leg.get('line'),
                'bet_line_type': 'over' if leg.get('stat_add') == 'over' else 'under' if leg.get('stat_add') == 'under' else None,
                'odds': leg.get('odds'),
                # Required BetLeg fields - provide proper defaults for OCR bets
                'home_team': home_team,
                'away_team': away_team,
                'sport': 'NBA' if 'lakers' in team_name.lower() or 'celtics' in team_name.lower() else 'NFL'  # Default sport detection
            }
            transformed['legs'].append(transformed_leg)

        return transformed

    # Sample data from our OpenAI test
    sample_data = {
        "bet_site": "DraftKings",
        "bet_type": "parlay",
        "total_odds": "+250",
        "wager_amount": "10.00",
        "potential_payout": "35.00",
        "legs": [
            {
                "team": "Los Angeles Lakers",
                "stat": "spread",
                "line": -4.5
            },
            {
                "team": "Boston Celtics",
                "stat": "moneyline",
                "line": 0
            },
            {
                "team": "Game Total",
                "stat": "total_points",
                "line": 220.5,
                "stat_add": "over"
            }
        ]
    }

    print('🧪 Testing transform_extracted_bet_data function...')
    try:
        transformed = transform_extracted_bet_data(sample_data)
        print('✅ Transform successful')
        print('📋 Transformed data:')
        print(json.dumps(transformed, indent=2))

        # Check for required fields
        for leg in transformed.get('legs', []):
            required_fields = ['home_team', 'away_team', 'target_value']
            missing = [field for field in required_fields if field not in leg or leg[field] is None]
            if missing:
                print(f'❌ Leg missing required fields: {missing}')
                print(f'   Leg data: {leg}')
            else:
                print(f'✅ Leg has all required fields: home_team="{leg["home_team"]}", away_team="{leg["away_team"]}", target_value={leg["target_value"]}')

        return transformed

    except Exception as e:
        print(f'❌ Transform failed: {e}')
        return None

def main():
    import sys

    print('🧪 OpenAI Vision API Test for Bet Slip OCR')
    print('=' * 50)

    # Test the transform function first
    test_transform_function()
    print()

    # Check command line arguments
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        if not Path(image_path).exists():
            print(f'❌ Image file not found: {image_path}')
            return
        result = test_openai_vision_api(image_path=image_path)
    else:
        print('💡 No image file provided, testing with generated bet slip image')
        # Generate a test bet slip image
        test_image_data = create_test_bet_slip_image()
        result = test_openai_vision_api(image_data=test_image_data)

    if result:
        print('\n🎉 Test completed successfully!')
        print('📊 Summary:')
        print(f'   - Bet site: {result.get("bet_site", "N/A")}')
        print(f'   - Bet type: {result.get("bet_type", "N/A")}')
        print(f'   - Legs found: {len(result.get("legs", []))}')
        print(f'   - Wager amount: {result.get("wager_amount", "N/A")}')
        print(f'   - Total odds: {result.get("total_odds", "N/A")}')
    else:
        print('\n❌ Test failed - check the output above for details')

if __name__ == '__main__':
    main()