# Webhook Configuration Generator

This directory contains auto-generated webhook configuration files.

## Files

- `generate_webhook_config.py` - Script to generate webhook URLs from environment
- `WEBHOOK_CONFIG.md` - Auto-generated webhook documentation (DO NOT EDIT MANUALLY)
- `webhook_config.json` - Auto-generated JSON config (DO NOT EDIT MANUALLY)

## Usage

To regenerate webhook configuration with latest environment values:

```bash
cd docs
python3 generate_webhook_config.py
```

This will:
1. Read your `.env` file
2. Fetch your AWS API Gateway URL from CloudFormation
3. Generate `WEBHOOK_CONFIG.md` with correct URLs
4. Generate `webhook_config.json` for programmatic use

## Configuration Sources

The script reads from:
- `backend/.env` - Environment variables
- AWS CloudFormation Stack - API Gateway URL
- AWS Secrets Manager - Meta credentials (optional)

## Security Note

⚠️ **DO NOT commit `webhook_config.json` or `WEBHOOK_CONFIG.md` if they contain sensitive data!**

These files are in `.gitignore` by default.
