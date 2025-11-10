# Umami Report to Telegram

This project contains a GitHub Actions workflow that periodically fetches website statistics from Umami and sends them to Telegram.

## Features

- 📊 Automatically fetch Umami website statistics (pageviews, unique visitors, bounce rate, etc.)
- 📤 Send formatted statistics to Telegram
- ⏰ Support scheduled tasks (default: daily at UTC 00:00)
- 🔧 Support manual trigger

## Setup Instructions

### 1. Create a Telegram Bot

1. Search for `@BotFather` in Telegram
2. Send the `/newbot` command
3. Follow the prompts to set up your bot name and username
4. Get your Bot Token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Get Your Chat ID

There are several methods:

**Method 1: Using @userinfobot**
1. Search for `@userinfobot` in Telegram
2. Send any message, and it will return your Chat ID

**Method 2: Using @getidsbot**
1. Search for `@getidsbot` in Telegram
2. Send any message, and it will return your Chat ID

**Method 3: Via API**
1. First, send a message to your bot
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Find the `chat.id` field in the returned JSON

### 3. Get Umami API Configuration

#### 3.1 Get Umami API URL

This is your Umami instance's base URL, for example:
- `https://analytics.example.com`
- `https://umami.example.com`

#### 3.2 Get Website ID

1. Log in to your Umami dashboard
2. Go to the website settings page
3. You can find the website ID in the URL or on the website details page
4. Website ID is usually a UUID or number

#### 3.3 Authentication Method

The script supports two authentication methods:

**Option A: Self-Hosted Umami (Username/Password)**
- Use your Umami username and password
- The script will automatically login and obtain a token
- Default username is `admin` if not specified
- This is the recommended method for self-hosted instances

**Option B: API Token**
- If you have an API token, you can use it directly
- To get an API token:
  1. Log in to your Umami dashboard
  2. Go to Settings -> API
  3. Create a new API Token
  4. Copy the generated Token (format: `umami_xxxxxxxxxxxxx`)

### 4. Configure GitHub Secrets

1. Go to your GitHub repository
2. Click `Settings` -> `Secrets and variables` -> `Actions`
3. Click `New repository secret`
4. Add the following secrets:

   **Required Secrets:**
   - `UMAMI_API_URL`: Your Umami API base URL (e.g., `https://analytics.example.com`)
   - `UMAMI_WEBSITE_ID`: Your website ID(s) with optional labels. Formats:
     - Single website: `website-id`
     - Single website with label: `website-id:My Website`
     - Multiple websites: `id1,id2,id3`
     - Multiple websites with labels: `id1:Blog,id2:Shop,id3:Main Site`
     - Mixed format: `id1:Blog,id2` (first has label, second uses ID as label)
   - `TELEGRAM_BOT_TOKEN`: Your Telegram Bot Token
   - `TELEGRAM_CHAT_ID`: Your Telegram Chat ID

   **Authentication (choose one):**
   - **For Self-Hosted Umami:**
     - `UMAMI_USER`: Your Umami username (default: `admin` if not set)
     - `UMAMI_PASSWORD`: Your Umami password
   - **For Umami Cloud or if you have API token:**
     - `UMAMI_API_TOKEN`: Your Umami API Token

   **Optional Secrets:**
   - `UMAMI_START_AT`: Start timestamp (milliseconds) or date string (format: `YYYY-MM-DD`, defaults to 24 hours ago)
   - `UMAMI_END_AT`: End timestamp (milliseconds) or date string (format: `YYYY-MM-DD`, defaults to current time)

### 5. Adjust Execution Time (Optional)

Edit the cron expression in `.github/workflows/umami-report.yml`:

```yaml
- cron: '0 0 * * *'  # UTC 00:00 (08:00 Beijing Time)
```

Cron format: `minute hour day month weekday`
- Daily at 09:00 Beijing Time = UTC 01:00: `0 1 * * *`
- Daily at 12:00 Beijing Time = UTC 04:00: `0 4 * * *`
- Daily at 18:00 Beijing Time = UTC 10:00: `0 10 * * *`

### 6. Testing

1. Commit and push your code to GitHub
2. In your GitHub repository's `Actions` tab, you can:
   - Wait for the scheduled task to execute
   - Or click on the workflow and select `Run workflow` to trigger it manually

## Local Run

You can also run the Python script locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
# For self-hosted Umami (recommended):
export UMAMI_API_URL="https://your-umami-instance.com"
export UMAMI_WEBSITE_ID="your-website-id:My Website"  # Format: "id:label" or "id1:Label1,id2:Label2"
export UMAMI_USER="admin"  # Optional, defaults to "admin"
export UMAMI_PASSWORD="your-password"
export TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"

# Or if you have an API token:
export UMAMI_API_URL="https://your-umami-instance.com"
export UMAMI_WEBSITE_ID="id1:Blog,id2:Shop,id3:Main Site"  # Multiple websites with labels
export UMAMI_API_TOKEN="your-api-token"
export TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"

# Run the script
python umami_report.py
```

## Statistics Description

The script will fetch and send the following statistics for each website:

- 👁️ **Views (Pageviews)**: Total number of page visits
- 👤 **Visitors**: Number of unique visitors
- 🔄 **Visits**: Number of unique visits
- ↩️ **Bounces**: Number of visits that left after viewing only one page
- 📉 **Bounce Rate**: Bounces / Visits (percentage)
- ⏱️ **Avg Time**: Average time per visit

When multiple websites are configured, the report will also include a summary section with totals and averages across all websites.

## Notes

- GitHub Actions free accounts have 2000 minutes of free usage per month
- Scheduled tasks use UTC time, so be mindful of timezone conversion
- Make sure all secrets are properly configured, otherwise the workflow will fail
- Ensure your Umami instance allows API access
- For self-hosted Umami, the script will automatically login using username/password and obtain a token
- The login endpoint is expected to be available at `<UMAMI_API_URL>/api/auth/login`
- If using API token, it needs to have permissions to access website statistics
