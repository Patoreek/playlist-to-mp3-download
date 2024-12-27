import os
import json
from datetime import datetime

# Path to quota data file
QUOTA_DATA_FILE = "backend/data/youtube_quota_data.json"

def load_quota_data():
    """Load the quota data from the JSON file or initialize it if not present."""
    if not os.path.exists(QUOTA_DATA_FILE):
        reset_quota_data()
    with open(QUOTA_DATA_FILE, "r") as file:
        return json.load(file)

def save_quota_data(data):
    """Save the quota data to the JSON file."""
    with open(QUOTA_DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

def reset_quota_data():
    """Reset quota data at the start of a new day."""
    data = {
        "quota_used": 0,
        "daily_quota_limit": 10000,  # Adjust as needed
        "updated_at": datetime.now().isoformat(),
        "refreshed_on": datetime.now().date().isoformat()
    }
    save_quota_data(data)

def check_and_update_quota():
    """Check if the quota needs to be reset and update the last-used timestamp."""
    data = load_quota_data()
    today = datetime.now().date()
    refreshed_on = datetime.fromisoformat(data["refreshed_on"]).date()

    if today > refreshed_on:
        reset_quota_data()
        data = load_quota_data()  # Reload after reset

    # Update `updated_at` to the current time
    data["updated_at"] = datetime.now().isoformat()
    save_quota_data(data)

    return data

def can_make_api_call():
    """Check if the quota usage is below the 90% threshold and provide warnings at various levels."""
    data = load_quota_data()
    quota_used = data["quota_used"]
    daily_quota_limit = data["daily_quota_limit"]

    # Calculate percentage of quota used
    quota_percentage = quota_used / daily_quota_limit * 100

   
    # Return appropriate status and message based on quota usage
    if quota_percentage >= 90:
        return {"value": "restricted", "message": "You have used 90% or more of your API quota. Further API calls will be restricted."}
    elif quota_percentage >= 75:
        return {"value": "warning_75", "message": "75% of your API quota is used. Consider reducing API calls."}
    elif quota_percentage >= 50:
        return {"value": "warning_50", "message": "50% of your API quota is used. Be mindful of the remaining quota."}
    elif quota_percentage >= 25:
        return {"value": "warning_25", "message": "25% of your API quota is used. Keep an eye on your usage."}

    # If less than 25% quota is used, return 'ok'
    return {"value": True, "message": "API quota is under control."}

def increment_quota_usage(units):
    """Increment the quota usage by the specified number of units."""
    data = check_and_update_quota()
    data["quota_used"] += units
    save_quota_data(data)