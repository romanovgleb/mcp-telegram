#!/usr/bin/env python3
"""
Telegram Session String Generator

This script generates a session string that can be used for Telegram authentication
with the Telegram MCP server. The session string allows for portable authentication
without storing session files.

Usage:
    python session_string_generator.py

Requirements:
    - telethon
    - python-dotenv

Note on ID Formats:
When using the MCP server, please be aware that all `chat_id` and `user_id`
parameters support integer IDs, string representations of IDs (e.g., "123456"),
and usernames (e.g., "@mychannel").
"""

import os
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
import sys

# Load environment variables from .env file
load_dotenv()

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")

if not API_ID or not API_HASH:
    print("Error: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env file")
    print("Create an .env file with your credentials from https://my.telegram.org/apps")
    sys.exit(1)

# Convert API_ID to integer
try:
    API_ID = int(API_ID)
except ValueError:
    print("Error: TELEGRAM_API_ID must be an integer")
    sys.exit(1)

print("\n----- Telegram Session String Generator -----\n")
print("This script will generate a session string for your Telegram account.")
print(
    "You will be asked to enter your phone number and the verification code sent to your Telegram app."
)
print("The generated session string can be added to your .env file.")
print(
    "\nYour credentials will NOT be stored on any server and are only used for local authentication.\n"
)

try:
    # Connect to Telegram and generate the session string
    with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        # The client.session.save() function from StringSession returns the session string
        session_string = StringSession.save(client.session)

        print("\nAuthentication successful!")
        print("\n----- Your Session String -----")
        print(f"\n{session_string}\n")
        
        # Determine the session variable name
        session_var_name = "TELEGRAM_SESSION_STRING"
        try:
            # Check if .env file exists and find the next available session number
            if os.path.exists(".env"):
                with open(".env", "r") as file:
                    env_contents = file.readlines()
                
                # Find the highest session number
                max_session_num = 0
                for line in env_contents:
                    if line.startswith("TELEGRAM_SESSION_STRING="):
                        max_session_num = max(max_session_num, 1)
                    elif line.startswith("TELEGRAM_SESSION_STRING_"):
                        try:
                            num = int(line.split("_")[3].split("=")[0])
                            max_session_num = max(max_session_num, num)
                        except (ValueError, IndexError):
                            pass
                
                # If base session exists, use next number
                if max_session_num > 0:
                    session_var_name = f"TELEGRAM_SESSION_STRING_{max_session_num + 1}"
        except Exception:
            pass  # Fall back to base session name
        
        print("Add this to your .env file as:")
        print(f"{session_var_name}={session_string}")
        print("\nIMPORTANT: Keep this string private and never share it with anyone!")
        print("\nNote: Multiple session strings allow you to use Telegram MCP in multiple Cursor windows simultaneously.")

        # Optional: auto-update the .env file
        choice = input(
            f"\nWould you like to automatically add this session string to your .env file as {session_var_name}? (y/N): "
        )
        if choice.lower() == "y":
            try:
                # Read the current .env file
                env_contents = []
                if os.path.exists(".env"):
                    with open(".env", "r") as file:
                        env_contents = file.readlines()
                
                # Check if this session variable already exists
                session_string_line_found = False
                for i, line in enumerate(env_contents):
                    if line.startswith(f"{session_var_name}="):
                        env_contents[i] = f"{session_var_name}={session_string}\n"
                        session_string_line_found = True
                        break

                if not session_string_line_found:
                    env_contents.append(f"{session_var_name}={session_string}\n")

                # Write back to the .env file
                with open(".env", "w") as file:
                    file.writelines(env_contents)

                print(f"\n.env file updated successfully! Session added as {session_var_name}")
            except Exception as e:
                print(f"\nError updating .env file: {e}")
                print("Please manually add the session string to your .env file.")

except Exception as e:
    print(f"\nError: {e}")
    print("Failed to generate session string. Please try again.")
    sys.exit(1)
