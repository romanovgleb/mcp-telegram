#!/usr/bin/env python3
"""
Telegram MCP Server

A Model Context Protocol server that provides functionality to send messages via Telegram Bot API.
Uses simple HTTP GET requests to send messages.
"""

import os
import logging
from typing import Optional
import requests
from urllib.parse import quote

from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("telegram-mcp")

# Create FastMCP server
mcp = FastMCP("Telegram Messenger", dependencies=["requests"])


@mcp.tool()
def send_telegram_message(
    message: str,
    chat_id: Optional[str] = None,
    bot_token: Optional[str] = None
) -> str:
    """
    Send a message via Telegram Bot API using HTTP GET request.
    
    Args:
        message: The message text to send
        chat_id: Telegram chat ID (uses TELEGRAM_CHAT_ID env var if not provided)
        bot_token: Telegram bot token (uses TELEGRAM_BOT_TOKEN env var if not provided)
    
    Returns:
        Status message indicating success or failure
    """
    # Get credentials from environment variables or parameters
    chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
    bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not chat_id:
        return "Error: chat_id is required. Provide it as parameter or set TELEGRAM_CHAT_ID environment variable."
    
    if not bot_token:
        return "Error: bot_token is required. Provide it as parameter or set TELEGRAM_BOT_TOKEN environment variable."
    
    try:
        # URL encode the message to handle special characters
        encoded_message = quote(message)
        
        # Construct the Telegram Bot API URL using the simple GET method
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={encoded_message}"
        
        # Send the request
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("ok"):
                logger.info(f"Message sent successfully to chat {chat_id}")
                return f"Message sent successfully to Telegram chat {chat_id}\nMessage: {message}"
            else:
                error_description = response_data.get("description", "Unknown error")
                logger.error(f"Telegram API error: {error_description}")
                return f"Telegram API error: {error_description}"
        else:
            logger.error(f"HTTP error: {response.status_code}")
            return f"HTTP error: {response.status_code} - {response.text}"
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return f"Request failed: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return f"Unexpected error: {str(e)}"


if __name__ == "__main__":
    # FastMCP handles the server execution automatically
    mcp.run() 