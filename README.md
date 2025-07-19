# Telegram MCP Server

A Model Context Protocol (MCP) server that enables AI assistants to send messages via Telegram Bot API using simple HTTP GET requests.

## Features

- 🚀 **Simple messaging**: Send Telegram messages with a single tool call
- 🔒 **Secure**: Uses environment variables for credentials (no hardcoded tokens)
- ⚡ **Fast**: Built with FastMCP for optimal performance
- 🛠️ **Flexible**: Support for custom chat IDs and bot tokens per message
- 📝 **Easy setup**: Quick installation and configuration

## Installation

### Prerequisites

- Python 3.8+
- A Telegram bot token (see [Creating a Bot](#creating-a-telegram-bot))
- Your Telegram chat ID (see [Getting Your Chat ID](#getting-your-chat-id))

### Install Dependencies

```bash
# Using uv (recommended)
uv pip install fastmcp requests

# Or using pip
pip install fastmcp requests
```

## Setup

### Creating a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Save the bot token (format: `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`)

### Getting Your Chat ID

1. Send a message to your bot
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Look for `"chat":{"id":123456789}` in the response
4. Save this chat ID

### Environment Variables

Create a `.env` file or set environment variables:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

## Usage

### Running the Server

```bash
# Development mode with MCP Inspector
fastmcp dev telegram_mcp_server.py

# Install in Claude Desktop
fastmcp install telegram_mcp_server.py

# Or run directly
python telegram_mcp_server.py
```

### Using with Claude Desktop

1. Install the server:
   ```bash
   fastmcp install telegram_mcp_server.py -e TELEGRAM_BOT_TOKEN=your_token -e TELEGRAM_CHAT_ID=your_chat_id
   ```

2. The server will be available in Claude Desktop as "Telegram Messenger"

3. Use it in your conversations:
   - "Send a Telegram message saying 'Hello from Claude!'"
   - "Notify me on Telegram that the task is complete"

### Tool: send_telegram_message

Sends a message via Telegram Bot API.

**Parameters:**
- `message` (required): The text message to send
- `chat_id` (optional): Target chat ID (uses env var if not provided)
- `bot_token` (optional): Bot token (uses env var if not provided)

**Examples:**

```python
# Using environment variables
send_telegram_message("Hello, World!")

# Using custom credentials
send_telegram_message(
    message="Custom message",
    chat_id="123456789",
    bot_token="your_custom_token"
)
```

## Configuration

### MCP Client Configuration

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "telegram": {
      "command": "fastmcp",
      "args": ["run", "telegram_mcp_server.py"],
      "env": {
        "TELEGRAM_BOT_TOKEN": "your_bot_token_here",
        "TELEGRAM_CHAT_ID": "your_chat_id_here"
      }
    }
  }
}
```

### Multiple Chat Support

You can send messages to different chats by providing the `chat_id` parameter:

```python
# Send to a group chat
send_telegram_message("Group notification", chat_id="-1001234567890")

# Send to a different user
send_telegram_message("Direct message", chat_id="987654321")
```

## Development

### Project Structure

```
telegram-mcp/
├── telegram_mcp_server.py  # Main MCP server
├── pyproject.toml          # Project configuration
├── README.md               # This file
├── .env.example            # Environment variables template
└── .gitignore              # Git ignore rules
```

### Testing

Test your server using the MCP Inspector:

```bash
# Start development server
fastmcp dev telegram_mcp_server.py

# Open http://localhost:3000 in your browser
# Test the send_telegram_message tool
```

### Error Handling

The server provides detailed error messages:

- ❌ Missing credentials (bot token or chat ID)
- ❌ Telegram API errors (invalid token, chat not found, etc.)
- ❌ Network connectivity issues
- ❌ Invalid message format

## Security Notes

- **Never commit credentials**: Use environment variables or `.env` files
- **Bot token security**: Keep your bot token private
- **Chat ID privacy**: Don't expose chat IDs in public repositories
- **Rate limiting**: Telegram has rate limits; excessive requests may be blocked

## API Reference

### Telegram Bot API

This server uses the Telegram Bot API's `sendMessage` method via HTTP GET:

```
https://api.telegram.org/bot<token>/sendMessage?chat_id=<chat_id>&text=<message>
```

For more information, see the [Telegram Bot API documentation](https://core.telegram.org/bots/api).

## Troubleshooting

### Common Issues

**"Bot token is required"**
- Set the `TELEGRAM_BOT_TOKEN` environment variable
- Or provide `bot_token` parameter in the tool call

**"Chat ID is required"**
- Set the `TELEGRAM_CHAT_ID` environment variable  
- Or provide `chat_id` parameter in the tool call

**"Forbidden: bot was blocked by the user"**
- The user has blocked your bot
- Start a conversation with the bot first

**"Bad Request: chat not found"**
- Invalid chat ID
- Verify the chat ID is correct

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with MCP Inspector
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- 📖 [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- 🤖 [Telegram Bot API](https://core.telegram.org/bots/api)
- 🚀 [FastMCP Documentation](https://github.com/jlowin/fastmcp)

## Changelog

### v0.1.0
- Initial release
- Basic Telegram messaging functionality
- Environment variable support
- FastMCP integration 