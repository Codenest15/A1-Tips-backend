from curl_cffi import requests
from curl_cffi.requests.errors import RequestsError
from datetime import datetime
import time

def get_booking(code: str):
    # Dynamically generate the timestamp to bypass stale request checks
    current_timestamp = int(time.time() * 1000)
    url = f"https://www.sportybet.com/api/gh/orders/share/{code}?_t={current_timestamp}"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json"
    }
    
    try:
        res = requests.get(url,headers=headers, impersonate="chrome110")
        res.raise_for_status()
        
        # Safely attempt to parse the JSON
        try:
            json_response = res.json()
        except ValueError:
            # If JSON parsing fails, the server likely returned an anti-bot HTML page
            return {"error": f"Server blocked the request. Returned non-JSON content: {res.text[:150]}..."}

        data = json_response.get("data", {})
        
        # Check if data actually exists before trying to access 'deadline'
        if not data:
             return {"error": "No data found in the response."}

        # Format deadline from ms timestamp to ISO string
        deadline = datetime.utcfromtimestamp(data["deadline"] / 1000).strftime("%Y-%m-%dT%H:%M:%S")

        games = []
        for outcome in data.get("outcomes", []):
            markets = outcome.get("markets", [])
            prediction_parts = []
            odd = None

            # Process all markets for this outcome
            for market in markets:
                market_desc = market.get("desc", "")
                market_outcomes = market.get("outcomes", [])

                for market_outcome in market_outcomes:
                    selection = market_outcome.get("desc", "")
                    odds_value = float(market_outcome.get("odds", 0))

                    # Build enhanced prediction string
                    if market_desc and market_desc != "1X2":
                        enhanced_prediction = f"{selection} ({market_desc})"
                    else:
                        market_extensions = market.get("marketExtendVOS", [])
                        if market_extensions:
                            extensions = [ext.get("name", "") for ext in market_extensions if ext.get("name")]
                            if extensions:
                                enhanced_prediction = f"{selection} {' '.join(extensions)} ({market_desc})"
                            else:
                                enhanced_prediction = f"{selection} ({market_desc})"
                        else:
                            enhanced_prediction = f"{selection} ({market_desc})"

                    prediction_parts.append(enhanced_prediction)

                    if not odd:  
                        odd = odds_value

            final_prediction = " & ".join(prediction_parts) if prediction_parts else "Unknown"

            games.append({
                "home": outcome.get("homeTeamName", "Unknown"),
                "away": outcome.get("awayTeamName", "Unknown"),
                "prediction": final_prediction,
                "odd": odd,
                "sport": outcome.get("sport", {}).get("name", "Unknown"),
                "tournament": outcome.get("sport", {}).get("category", {}).get("tournament", {}).get("name", "Unknown")
            })

        return {
            "deadline": deadline,
            "shareCode": data.get("shareCode"),
            "shareURL": data.get("shareURL"),
            "games": games
        }

    # Catch the correct curl_cffi networking errors
    except RequestsError as e:
        return {"error": f"Network request failed: {e}"}
    
    # Catch any other unexpected python errors
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}
