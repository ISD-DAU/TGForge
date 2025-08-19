import streamlit as st
import asyncio
import pandas as pd
import io
from telegram_client import create_client, delete_session_file
from fetch_channel import fetch_channel_data
from fetch_forwards import fetch_forwards
from fetch_messages import fetch_messages
from fetch_participants import fetch_participants
from telethon.errors import PhoneNumberInvalidError, PhoneCodeInvalidError, SessionPasswordNeededError
import nest_asyncio
import re

nest_asyncio.apply()

# --- Ensure an Event Loop Exists ---
import sys
if "event_loop" not in st.session_state:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # Windows fix
    st.session_state.event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(st.session_state.event_loop)
else:
    asyncio.set_event_loop(st.session_state.event_loop)  # Keep the same event loop

def clean_column_name(name):
    name = str(name)
    # Step 1: Remove everything up to and including 't.me/'
    name = re.sub(r'^.*t\.me/', '', name)
    # Step 2: Replace disallowed characters with underscores (allow letters, numbers, _ and -)
    name = re.sub(r'[^a-zA-Z0-9_\-]', '_', name)
    return name

# --- Streamlit UI ---
st.title("TGForge")
st.logo("logo.png", size='large')  # Official app logo

# Ensure session state variables are initialized
if "auth_step" not in st.session_state:
    st.session_state.auth_step = 1
    st.session_state.authenticated = False
    st.session_state.client = None

# --- Step 1: Enter API Credentials ---
if st.session_state.auth_step == 1:
    st.subheader("Enter Telegram API Credentials")

    api_id = st.text_input("API ID", value=st.session_state.get("api_id", ""))
    api_hash = st.text_input("API Hash", value=st.session_state.get("api_hash", ""))
    phone_number = st.text_input("Phone Number (e.g., +1 2224448888)")

    col1, col2 = st.columns([2, 1])

    with col1:
        if st.button("Next"):
            if api_id and api_hash and phone_number:
                try:
                    st.session_state.api_id = api_id
                    st.session_state.api_hash = api_hash
                    st.session_state.phone_number = phone_number.strip()

                    if st.session_state.client is None:
                        st.session_state.client = create_client(int(api_id), api_hash)

                    async def connect_and_send_code():
                        await st.session_state.client.connect()
                    
                        # 1) Already authorized? Skip code.
                        if await st.session_state.client.is_user_authorized():
                            return {"status": "already_authorized"}
                    
                        # 2) Request code (optionally force SMS)
                        force_sms = st.session_state.get("force_sms", False)
                        sent = await st.session_state.client.send_code_request(
                            st.session_state.phone_number,
                            force_sms=force_sms
                        )
                    
                        # Store for Step 2 / debugging
                        st.session_state.sent_code = {
                            "type": type(sent.type).__name__,  # e.g. SentCodeTypeApp/Sms/Call
                            "next_type": type(sent.next_type).__name__ if getattr(sent, "next_type", None) else None,
                            "timeout": getattr(sent, "timeout", None)
                        }
                        return {"status": "code_sent"}

                    st.write("Connecting with Telegram's API...")
                    result = st.session_state.event_loop.run_until_complete(connect_and_send_code())

                    if result == "already_authorized":
                        st.session_state.authenticated = True
                        st.session_state.auth_step = 3
                    else:
                        st.session_state.auth_step = 2

                    st.rerun()

                except PhoneNumberInvalidError:
                    st.error("Invalid phone number. Please check and try again.")
                except Exception as e:
                    st.error(f"Error: {e}")

    with col2:
        if st.button("Reset Session"):
            # Best-effort logout + delete session
            try:
                if st.session_state.get("client"):
                    st.session_state.event_loop.run_until_complete(st.session_state.client.log_out())
            except Exception:
                pass
            delete_session_file()
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


