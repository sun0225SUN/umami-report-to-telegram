# Umami Report to Telegram

This project contains a GitHub Actions workflow that sends scheduled daily messages to a Telegram bot.

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

### 3. Configure GitHub Secrets

1. Go to your GitHub repository
2. Click `Settings` -> `Secrets and variables` -> `Actions`
3. Click `New repository secret`
4. Add the following two secrets:
   - `TELEGRAM_BOT_TOKEN`: Your Telegram Bot Token
   - `TELEGRAM_CHAT_ID`: Your Telegram Chat ID

### 4. Adjust Execution Time (Optional)

Edit the cron expression in `.github/workflows/daily-telegram-message.yml`:

```yaml
- cron: '0 0 * * *'  # UTC 00:00 (08:00 Beijing Time)
```

Cron format: `minute hour day month weekday`
- Daily at 09:00 Beijing Time = UTC 01:00: `0 1 * * *`
- Daily at 12:00 Beijing Time = UTC 04:00: `0 4 * * *`
- Daily at 18:00 Beijing Time = UTC 10:00: `0 10 * * *`

### 5. Testing

1. Commit and push your code to GitHub
2. In your GitHub repository's `Actions` tab, you can:
   - Wait for the scheduled task to execute
   - Or click on the workflow and select `Run workflow` to trigger it manually

## Customize Message Content

Edit the `MESSAGE` variable in `.github/workflows/daily-telegram-message.yml` to customize the message content.

## Notes

- GitHub Actions free accounts have 2000 minutes of free usage per month
- Scheduled tasks use UTC time, so be mindful of timezone conversion
- Make sure secrets are properly configured, otherwise the workflow will fail

