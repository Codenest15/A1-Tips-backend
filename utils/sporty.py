from curl_cffi import requests
from datetime import datetime

def get_booking(code: str):
    url = f"https://www.sportybet.com/api/gh/orders/share/{code}?_t=1757526666143"
    
    try:
        # The 'impersonate' flag perfectly mimics Chrome's TLS fingerprint
        res = requests.get(url, impersonate="chrome110")
        res.raise_for_status()
        data = res.json().get("data", {})

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
                "home": outcome["homeTeamName"],
                "away": outcome["awayTeamName"],
                "prediction": final_prediction,
                "odd": odd,
                "sport": outcome["sport"]["name"],
                "tournament": outcome["sport"]["category"]["tournament"]["name"]
            })

        return {
            "deadline": deadline,
            "shareCode": data["shareCode"],
            "shareURL": data["shareURL"],
            "games": games
        }

    except requests.RequestException as e:
        return {"error": f"Request failed: {e}"}
