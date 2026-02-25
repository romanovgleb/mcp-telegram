"""
Telegram MCP startup: lock, connect to Telegram, run MCP server.
Separated from main.py to keep the tool-heavy main module lighter.
"""
import os
import sys
import time
import asyncio
import sqlite3
import logging
import fcntl
import signal
from typing import List, Callable, Any

import nest_asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
import telethon.errors.rpcerrorlist

logger = logging.getLogger("telegram_mcp")


def run_telegram_mcp(
    mcp: Any,
    session_strings: List[str],
    api_id: int,
    api_hash: str,
    session_name: str,
    set_client: Callable[[Any], None],
) -> None:
    nest_asyncio.apply()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    lock_file_path = os.path.join(script_dir, ".telegram_mcp.lock")
    lock_file = None
    lock_acquired = False

    def _try_acquire_lock():
        nonlocal lock_file, lock_acquired
        lock_file = open(lock_file_path, "a")
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            lock_file.seek(0)
            lock_file.write(str(os.getpid()))
            lock_file.truncate()
            lock_file.flush()
            lock_acquired = True
            return True
        except OSError:
            lock_file.close()
            lock_file = None
            return False

    def _stale_lock_pid():
        try:
            if not os.path.exists(lock_file_path):
                return None
            with open(lock_file_path, "r") as f:
                raw = f.read().strip()
            return int(raw) if raw else None
        except Exception:
            return None

    try:
        for attempt in range(2):
            if _try_acquire_lock():
                break
            pid = _stale_lock_pid()
            if pid is not None:
                try:
                    os.kill(pid, 0)
                except OSError:
                    # Process dead: stale lock
                    try:
                        if os.path.exists(lock_file_path):
                            os.remove(lock_file_path)
                    except Exception:
                        pass
                    if attempt == 0:
                        continue
            # Lock held by live process: wait up to 30s for it to exit (e.g. other Cursor closed)
            holder_pid = _stale_lock_pid()
            for _ in range(15):
                time.sleep(2)
                if _try_acquire_lock():
                    break
                holder_pid = _stale_lock_pid()
            else:
                msg = (
                    "Telegram MCP: Another instance is already running (lock held). "
                    "Only one instance can run."
                )
                if holder_pid is not None:
                    msg += f" Process {holder_pid} holds the lock. To free it: kill {holder_pid} (or close the other Cursor window that uses Telegram MCP)."
                else:
                    msg += " Exit that instance or wait and retry."
                print(msg, file=sys.stderr)
                sys.exit(0)
            if lock_acquired:
                break
    except Exception as lock_error:
        if lock_file:
            lock_file.close()
            lock_file = None
        logger.warning(f"Could not check for other instances: {lock_error}")

    async def _main() -> None:
        nonlocal lock_file, lock_acquired
        client = None

        async def _disconnect_and_stop() -> None:
            c = client
            if c:
                try:
                    await c.disconnect()
                except Exception:
                    pass
            set_client(None)
            if lock_file and lock_acquired:
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                    lock_file.close()
                    if os.path.exists(lock_file_path):
                        os.remove(lock_file_path)
                except Exception:
                    pass
            asyncio.get_running_loop().stop()

        def _on_signal() -> None:
            asyncio.ensure_future(_disconnect_and_stop())

        for sig in (signal.SIGTERM, signal.SIGHUP):
            try:
                asyncio.get_running_loop().add_signal_handler(sig, _on_signal)
            except (NotImplementedError, OSError):
                pass

        async def _parent_watchdog() -> None:
            try:
                ppid = os.getppid()
                while True:
                    await asyncio.sleep(3)
                    try:
                        if os.getppid() != ppid:
                            break
                        os.kill(ppid, 0)
                    except OSError:
                        break
                await _disconnect_and_stop()
            except asyncio.CancelledError:
                pass

        parent_watchdog_task = asyncio.ensure_future(_parent_watchdog())

        if session_strings:
            last_attempt_was_duplicated = False
            for attempt in (1, 2):
                if attempt == 2 and last_attempt_was_duplicated:
                    logger.info("All sessions were in use; waiting 90s then retrying once...")
                    if lock_file and lock_acquired:
                        try:
                            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                            lock_file.close()
                            lock_file = None
                            lock_acquired = False
                        except Exception:
                            pass
                    await asyncio.sleep(90)
                    try:
                        lock_file = open(lock_file_path, "w")
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                        lock_file.write(str(os.getpid()))
                        lock_file.flush()
                        lock_acquired = True
                    except OSError:
                        if lock_file:
                            lock_file.close()
                            lock_file = None
                        print(
                            "Telegram MCP: Another instance started during retry wait. Exiting.",
                            file=sys.stderr,
                        )
                        sys.exit(0)
                    except Exception:
                        if lock_file:
                            lock_file.close()
                            lock_file = None
                        lock_acquired = False

                all_failed_duplicated = True
                for idx, session_string in enumerate(session_strings):
                    for conn_attempt in range(3):
                        try:
                            if conn_attempt > 0:
                                await asyncio.sleep(5)
                                logger.info(
                                    f"Retrying connection with session {idx + 1} (attempt {conn_attempt + 1}/3)..."
                                )
                            else:
                                logger.info(
                                    f"Trying to connect with session {idx + 1}/{len(session_strings)}..."
                                )
                            temp_client = TelegramClient(
                                StringSession(session_string),
                                api_id,
                                api_hash,
                                auto_reconnect=False,
                            )
                            await temp_client.start()
                            client = temp_client
                            set_client(client)
                            all_failed_duplicated = False
                            logger.info(f"Successfully connected using session {idx + 1}")
                            break
                        except telethon.errors.rpcerrorlist.AuthKeyDuplicatedError:
                            logger.warning(f"Session {idx + 1} is already in use, trying next session...")
                            try:
                                await temp_client.disconnect()
                            except Exception:
                                pass
                            break
                        except Exception as e:
                            all_failed_duplicated = False
                            logger.warning(
                                f"Error connecting with session {idx + 1}: {e}. Trying next session..."
                            )
                            try:
                                await temp_client.disconnect()
                            except Exception:
                                pass
                            err_str = str(e).lower()
                            if conn_attempt < 2 and (
                                "closed" in err_str or "connection" in err_str or "bytes read" in err_str
                            ):
                                continue
                            break
                    if client is not None:
                        break
                last_attempt_was_duplicated = all_failed_duplicated
                if client is not None:
                    break
                if attempt == 2 or not last_attempt_was_duplicated:
                    break

            if client is None:
                error_msg = (
                    f"Failed to connect with any of the {len(session_strings)} configured sessions. "
                    "All sessions are either already in use or invalid. "
                    "In Telegram go to Settings → Privacy and Security → Active Sessions and terminate other sessions, "
                    "or wait 2–3 minutes and retry. "
                    "You can also generate more session strings using session_string_generator.py "
                    "and add them to your .env as TELEGRAM_SESSION_STRING_2, TELEGRAM_SESSION_STRING_3, etc."
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg)
        else:
            logger.info("No session strings found, using file-based session...")
            client = TelegramClient(
                session_name, api_id, api_hash, auto_reconnect=False
            )
            try:
                await client.start()
            except Exception as e:
                logger.error(f"Error starting client with file-based session: {e}")
                raise
            set_client(client)

        try:
            logger.info("Telegram client started. Running MCP server...")
            await mcp.run_stdio_async()
        except Exception as e:
            logger.error(f"Error running MCP server: {e}")
            if isinstance(e, sqlite3.OperationalError) and "database is locked" in str(e):
                logger.error("Database lock detected. Please ensure no other instances are running.")
            raise
        finally:
            parent_watchdog_task.cancel()
            try:
                await parent_watchdog_task
            except asyncio.CancelledError:
                pass
            if client:
                try:
                    await client.disconnect()
                except Exception:
                    pass
            set_client(None)
            if lock_file and lock_acquired:
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                    lock_file.close()
                    if os.path.exists(lock_file_path):
                        os.remove(lock_file_path)
                except Exception:
                    pass

    try:
        asyncio.run(_main())
    except SystemExit:
        if lock_file and lock_acquired:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
                if os.path.exists(lock_file_path):
                    os.remove(lock_file_path)
            except Exception:
                pass
        raise
