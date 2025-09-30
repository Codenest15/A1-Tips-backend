import requests
from datetime import datetime

def get_booking(code: str):
    url = f"https://www.sportybet.com/api/gh/orders/share/{code}?_t=1757526666143"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers)
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
                        # For non-1X2 markets, include market type
                        enhanced_prediction = f"{selection} ({market_desc})"
                    else:
                        # For 1X2 markets, check for extensions
                        market_extensions = market.get("marketExtendVOS", [])
                        if market_extensions:
                            # Add any extensions found
                            extensions = [ext.get("name", "") for ext in market_extensions if ext.get("name")]
                            if extensions:
                                enhanced_prediction = f"{selection} {' '.join(extensions)} ({market_desc})"
                            else:
                                enhanced_prediction = f"{selection} ({market_desc})"
                        else:
                            enhanced_prediction = f"{selection} ({market_desc})"

                    prediction_parts.append(enhanced_prediction)

                    if not odd:  # Take the first odds value
                        odd = odds_value

            # Join all predictions with " & "
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
