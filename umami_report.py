#!/usr/bin/env python3
"""
Umami Report to Telegram
Fetch Umami website statistics and send to Telegram
"""

import os
import sys
import requests
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any


def login_umami(api_url: str, username: str, password: str) -> str:
    """
    Login to Umami API and get authentication token

    Args:
        api_url: Umami API base URL (e.g., https://your-umami-instance.com)
        username: Umami username (default: "admin")
        password: Umami password

    Returns:
        Authentication token
    """
    login_url = f"{api_url.rstrip('/')}/api/auth/login"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "username": username,
        "password": password,
    }

    try:
        response = requests.post(login_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        token = data.get("token")
        if not token:
            raise Exception("No token received from login response")
        return token
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_detail = response.json()
        except:
            error_detail = response.text
        raise Exception(
            f"Failed to login to Umami (HTTP {response.status_code}): {error_detail}"
        )
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to login to Umami: {e}")


def parse_time_param(time_str: Optional[str]) -> Optional[int]:
    """
    Convert time parameter to milliseconds timestamp

    Args:
        time_str: Date string (YYYY-MM-DD) or timestamp string

    Returns:
        Milliseconds timestamp, or None if input is None
    """
    if not time_str:
        return None

    # If it's a pure number, assume it's a timestamp
    if time_str.isdigit():
        # If it's a second-level timestamp, convert to milliseconds
        timestamp = int(time_str)
        if (
            timestamp < 10000000000
        ):  # Less than this value means it's a second-level timestamp
            return timestamp * 1000
        return timestamp

    # Try to parse date string (YYYY-MM-DD)
    try:
        dt = datetime.strptime(time_str, "%Y-%m-%d")
        # Set to start of day (00:00:00)
        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        return int(dt.timestamp() * 1000)
    except ValueError:
        raise ValueError(
            f"Unable to parse time parameter: {time_str}, please use YYYY-MM-DD format or timestamp"
        )


def get_umami_stats(
    api_url: str,
    website_id: str,
    api_token: str,
    start_at: Optional[str] = None,
    end_at: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetch website statistics from Umami API

    Args:
        api_url: Umami API base URL (e.g., https://your-umami-instance.com)
        website_id: Website ID
        api_token: Umami API Token
        start_at: Start timestamp (milliseconds) or date string (YYYY-MM-DD)
        end_at: End timestamp (milliseconds) or date string (YYYY-MM-DD)

    Returns:
        Dictionary containing statistics data
    """
    # Build complete API URL
    url = f"{api_url.rstrip('/')}/api/websites/{website_id}/stats"

    # Set request headers
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/json",
    }

    # Build query parameters, convert to milliseconds timestamp
    params = {}
    if start_at:
        params["startAt"] = parse_time_param(start_at)
    if end_at:
        # If it's a date string, set to end of day (23:59:59)
        if end_at and not end_at.isdigit():
            try:
                dt = datetime.strptime(end_at, "%Y-%m-%d")
                dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
                params["endAt"] = int(dt.timestamp() * 1000)
            except ValueError:
                params["endAt"] = parse_time_param(end_at)
        else:
            params["endAt"] = parse_time_param(end_at)

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()

        # Get response data
        data = response.json()

        # Handle different response formats
        # Umami v3.0 may return an array or a dictionary
        if isinstance(data, list):
            # If it's an array, convert to dictionary format
            # Combine all stats from the array
            combined_stats = {}
            for item in data:
                if isinstance(item, dict):
                    combined_stats.update(item)
            if combined_stats:
                return combined_stats
            else:
                # If array is empty or can't be combined, return first item or empty dict
                return data[0] if data and isinstance(data[0], dict) else {}
        elif isinstance(data, dict):
            return data
        else:
            print(
                f"⚠️ Warning: API response is not a dictionary or array. Type: {type(data)}"
            )
            print(f"Response content (first 500 chars): {str(data)[:500]}")
            raise Exception(f"Unexpected API response format: {type(data)}")
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_detail = response.json()
        except:
            error_detail = response.text
        raise Exception(
            f"Failed to fetch Umami statistics (HTTP {response.status_code}): {error_detail}"
        )
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch Umami statistics: {e}")


def format_single_website_stats(stats: Dict[str, Any], website_label: str) -> str:
    """
    Format statistics for a single website

    Args:
        stats: Statistics data returned from Umami API
        website_label: Website label (display name)

    Returns:
        Formatted message string for a single website
    """
    # Ensure stats is a dictionary
    if not isinstance(stats, dict):
        raise ValueError(f"Expected dict, got {type(stats)}: {stats}")

    # Extract statistics data according to Umami API v3.0 format
    # Try multiple possible field names for pageviews
    # According to Umami API docs, the field should be "pageviews"
    pageviews = 0
    # Try all possible field names
    for field_name in [
        "pageviews",
        "pageViews",
        "views",
        "page_views",
        "page_views_count",
    ]:
        if field_name in stats and stats[field_name] is not None:
            try:
                val = stats[field_name]
                if isinstance(val, (int, float)):
                    pageviews = int(val)
                    break
                elif isinstance(val, str) and val.isdigit():
                    pageviews = int(val)
                    break
            except (ValueError, TypeError):
                continue

    # If still 0, check if it's in a nested structure or try visits as fallback
    if pageviews == 0:
        # Sometimes pageviews might be equal to visits or in a different structure
        # Check if there's a comparison object
        if "comparison" in stats and isinstance(stats["comparison"], dict):
            for field_name in ["pageviews", "pageViews", "views"]:
                if field_name in stats["comparison"]:
                    try:
                        val = stats["comparison"][field_name]
                        if isinstance(val, (int, float)):
                            pageviews = int(val)
                            break
                    except (ValueError, TypeError):
                        continue
    visitors = (
        int(stats.get("visitors", 0))
        if isinstance(stats.get("visitors"), (int, float))
        else 0
    )
    visits = (
        int(stats.get("visits", 0))
        if isinstance(stats.get("visits"), (int, float))
        else 0
    )
    bounces = (
        int(stats.get("bounces", 0))
        if isinstance(stats.get("bounces"), (int, float))
        else 0
    )
    totaltime = (
        int(stats.get("totaltime", 0))
        if isinstance(stats.get("totaltime"), (int, float))
        else 0
    )

    # Format website section with cleaner format
    message = f"<b>{website_label}</b>\n"
    message += f"👁️ Views: {pageviews:,}\n"
    message += f"👤 Visitors: {visitors:,}\n"
    message += f"🔄 Visits: {visits:,}\n"

    # Calculate bounce rate
    if visits > 0:
        bounce_rate = (bounces / visits) * 100
        message += f"📉 Bounce Rate: {bounce_rate:.1f}%\n"

    # Format average time per visit
    if totaltime > 0 and visits > 0:
        avg_time_seconds = totaltime // visits
        avg_minutes = avg_time_seconds // 60
        avg_seconds = avg_time_seconds % 60
        if avg_minutes > 0:
            message += f"⏱️ Avg Time: {avg_minutes}m {avg_seconds}s\n"
        else:
            message += f"⏱️ Avg Time: {avg_seconds}s\n"

    message += f"\n"

    return message


def format_stats_message(
    websites_stats: list,
    start_at: Optional[str] = None,
    end_at: Optional[str] = None,
) -> str:
    """
    Format statistics data as Telegram message for multiple websites

    Args:
        websites_stats: List of tuples (website_id, website_label, stats_dict)
        start_at: Start time (for display purposes)
        end_at: End time (for display purposes)

    Returns:
        Formatted message string
    """
    # Get current time in UTC+8
    utc8 = timezone(timedelta(hours=8))
    current_time = datetime.now(utc8).strftime("%Y-%m-%d %H:%M:%S UTC+8")

    # Header
    message = f"📊 <b>Umami Statistics Report</b>\n"
    message += f"⏰ {current_time}\n"

    # Determine period description
    period_text = "Last 24 Hours"
    if start_at and end_at:
        try:
            if start_at.isdigit() and end_at.isdigit():
                start_dt = datetime.fromtimestamp(int(start_at) / 1000)
                end_dt = datetime.fromtimestamp(int(end_at) / 1000)
                duration = end_dt - start_dt
                hours = duration.total_seconds() / 3600
                if hours <= 24.1:
                    period_text = "Last 24 Hours"
                else:
                    period_text = f"{start_dt.strftime('%m/%d %H:%M')} - {end_dt.strftime('%m/%d %H:%M')}"
        except:
            pass

    message += f"📅 {period_text}\n"
    message += f"\n"

    # Calculate totals
    total_pageviews = 0
    total_visitors = 0
    total_visits = 0
    total_bounces = 0
    total_totaltime = 0

    # Format each website
    for website_id, website_label, stats in websites_stats:
        if isinstance(stats, dict):
            # Extract pageviews using same logic as format_single_website_stats
            pageviews_val = 0
            # Try all possible field names
            for field_name in [
                "pageviews",
                "pageViews",
                "views",
                "page_views",
                "page_views_count",
            ]:
                if field_name in stats and stats[field_name] is not None:
                    try:
                        val = stats[field_name]
                        if isinstance(val, (int, float)):
                            pageviews_val = int(val)
                            break
                        elif isinstance(val, str) and val.isdigit():
                            pageviews_val = int(val)
                            break
                    except (ValueError, TypeError):
                        continue

            # If still 0, check comparison object
            if (
                pageviews_val == 0
                and "comparison" in stats
                and isinstance(stats["comparison"], dict)
            ):
                for field_name in ["pageviews", "pageViews", "views"]:
                    if field_name in stats["comparison"]:
                        try:
                            val = stats["comparison"][field_name]
                            if isinstance(val, (int, float)):
                                pageviews_val = int(val)
                                break
                        except (ValueError, TypeError):
                            continue

            total_pageviews += pageviews_val
            total_visitors += (
                int(stats.get("visitors", 0))
                if isinstance(stats.get("visitors"), (int, float))
                else 0
            )
            total_visits += (
                int(stats.get("visits", 0))
                if isinstance(stats.get("visits"), (int, float))
                else 0
            )
            total_bounces += (
                int(stats.get("bounces", 0))
                if isinstance(stats.get("bounces"), (int, float))
                else 0
            )
            total_totaltime += (
                int(stats.get("totaltime", 0))
                if isinstance(stats.get("totaltime"), (int, float))
                else 0
            )
            message += format_single_website_stats(stats, website_label)
        else:
            message += f"<b>{website_label}</b>\n"
            message += f"⚠️ Failed to fetch data\n\n"

    # Summary
    if len(websites_stats) > 1:
        message += f"\n<b>📈 Summary</b>\n"
        message += f"👁️  Total Views: {total_pageviews:,}\n"
        message += f"👤  Total Visitors: {total_visitors:,}\n"
        message += f"🔄  Total Visits: {total_visits:,}\n"

        if total_visits > 0:
            avg_bounce_rate = (total_bounces / total_visits) * 100
            message += f"📉  Avg Bounce Rate: {avg_bounce_rate:.1f}%\n"

        if total_visits > 0 and total_totaltime > 0:
            avg_time_seconds = total_totaltime // total_visits
            avg_minutes = avg_time_seconds // 60
            avg_seconds = avg_time_seconds % 60
            if avg_minutes > 0:
                message += f"⏱️  Avg Visit Duration: {avg_minutes}m {avg_seconds}s\n"
            else:
                message += f"⏱️  Avg Visit Duration: {avg_seconds}s\n"

    return message


def send_telegram_message(bot_token: str, chat_id: str, message: str) -> None:
    """
    Send message to Telegram

    Args:
        bot_token: Telegram Bot Token
        chat_id: Telegram Chat ID
        message: Message to send
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
    }

    try:
        response = requests.post(url, json=data, timeout=30)
        response.raise_for_status()
        print("✅ Message successfully sent to Telegram")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to send Telegram message: {e}")


def main():
    """Main function"""
    # Get configuration from environment variables
    umami_api_url = os.getenv("UMAMI_API_URL")
    umami_website_id = os.getenv("UMAMI_WEBSITE_ID")
    umami_api_token = os.getenv("UMAMI_API_TOKEN")
    umami_user = os.getenv("UMAMI_USER", "admin")
    umami_password = os.getenv("UMAMI_PASSWORD")
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    # Optional: time range parameters (defaults to last 24 hours)
    start_at = os.getenv("UMAMI_START_AT")
    end_at = os.getenv("UMAMI_END_AT")

    # Validate required configuration
    missing_vars = []
    if not umami_api_url:
        missing_vars.append("UMAMI_API_URL")
    if not umami_website_id:
        missing_vars.append("UMAMI_WEBSITE_ID")
    if not telegram_bot_token:
        missing_vars.append("TELEGRAM_BOT_TOKEN")
    if not telegram_chat_id:
        missing_vars.append("TELEGRAM_CHAT_ID")

    # Authentication: either API token or username/password
    if not umami_api_token and not umami_password:
        missing_vars.append("UMAMI_API_TOKEN or UMAMI_PASSWORD")

    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)

    # Get authentication token
    if umami_api_token:
        # Use provided API token
        auth_token = umami_api_token
        print("🔑 Using provided API token")
    else:
        # Login with username and password to get token
        print(f"🔐 Logging in to Umami with username: {umami_user}")
        auth_token = login_umami(umami_api_url, umami_user, umami_password)
        print("✅ Successfully logged in and obtained token")

    try:
        # If no time range specified, default to last 24 hours
        if not start_at or not end_at:
            now = datetime.now()
            end_time = int(now.timestamp() * 1000)  # Current time in milliseconds
            start_time = int(
                (now - timedelta(hours=24)).timestamp() * 1000
            )  # 24 hours ago in milliseconds
            start_at = str(start_time)
            end_at = str(end_time)
            print(f"📡 Fetching Umami statistics (Last 24 hours)...")
        else:
            print(f"📡 Fetching Umami statistics...")

        print(f"   API URL: {umami_api_url}")

        # Parse website IDs and labels
        # Format: "id1:label1,id2:label2" or "id1,id2" (uses ID as label)
        website_configs = []
        for item in umami_website_id.split(","):
            item = item.strip()
            if not item:
                continue
            if ":" in item:
                # Format: id:label
                parts = item.split(":", 1)
                website_id = parts[0].strip()
                website_label = parts[1].strip()
                if website_id and website_label:
                    website_configs.append((website_id, website_label))
            else:
                # Format: id (use ID as label)
                website_configs.append((item, item))

        print(f"   Websites: {len(website_configs)} website(s)")
        for website_id, website_label in website_configs:
            if website_id == website_label:
                print(f"     - {website_id}")
            else:
                print(f"     - {website_label} ({website_id})")

        if start_at and end_at:
            # Try to format time range for display
            try:
                if start_at.isdigit():
                    start_dt = datetime.fromtimestamp(int(start_at) / 1000)
                    end_dt = datetime.fromtimestamp(int(end_at) / 1000)
                    print(
                        f"   Time Range: {start_dt.strftime('%Y-%m-%d %H:%M:%S')} to {end_dt.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                else:
                    print(f"   Time Range: {start_at} to {end_at}")
            except:
                print(f"   Time Range: {start_at} to {end_at}")

        # Fetch statistics data for each website
        websites_stats = []
        for website_id, website_label in website_configs:
            try:
                print(f"   📡 Fetching stats for: {website_label} ({website_id})")
                stats = get_umami_stats(
                    api_url=umami_api_url,
                    website_id=website_id,
                    api_token=auth_token,
                    start_at=start_at,
                    end_at=end_at,
                )
                # Debug: print actual response structure
                if isinstance(stats, dict):
                    print(f"   📋 Response keys: {list(stats.keys())}")
                    print(f"   📋 Full response: {stats}")
                    # Check all possible pageview fields
                    for key in ["pageviews", "pageViews", "views", "page_views"]:
                        if key in stats:
                            print(
                                f"   📋 Found '{key}': {stats[key]} (type: {type(stats[key])})"
                            )
                websites_stats.append((website_id, website_label, stats))
                print(f"   ✅ Successfully fetched statistics for {website_label}")
            except Exception as e:
                print(f"   ⚠️ Failed to fetch statistics for {website_label}: {e}")
                websites_stats.append((website_id, website_label, None))

        if not websites_stats:
            raise Exception("No statistics were successfully fetched for any website")

        # Format message
        message = format_stats_message(websites_stats, start_at, end_at)

        # Send to Telegram
        print("📤 Sending message to Telegram...")
        send_telegram_message(telegram_bot_token, telegram_chat_id, message)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
