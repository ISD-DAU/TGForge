# fetch_users.py
import streamlit as st

async def fetch_user_data(client, user_ids):
    """Fetches detailed information for users by their IDs."""
    results = []
    
    for user_id in user_ids:
        try:
            # Check if cancelled
            if st.session_state.get("cancel_fetch", False):
                st.warning("Fetch cancelled by user.")
                break
            
            # Convert to int if string
            if isinstance(user_id, str):
                user_id = int(user_id.strip())
            
            # Get the user entity by ID
            user = await client.get_entity(user_id)
            
            # Extract photo information
            photo_id = None
            photo_dc_id = None
            if user.photo:
                photo_id = getattr(user.photo, 'photo_id', None)
                photo_dc_id = getattr(user.photo, 'dc_id', None)
            
            # Extract status information
            status = "Unknown"
            if user.status:
                status_type = type(user.status).__name__
                if "Online" in status_type:
                    status = "Online"
                elif "Offline" in status_type:
                    status = "Offline"
                elif "Recently" in status_type:
                    status = "Recently"
                elif "LastWeek" in status_type:
                    status = "Last Week"
                elif "LastMonth" in status_type:
                    status = "Last Month"
            
            # Extract usernames (primary and alternates)
            primary_username = user.username if user.username else None
            alternate_usernames = []
            if hasattr(user, 'usernames') and user.usernames:
                alternate_usernames = [u.username for u in user.usernames if hasattr(u, 'username')]
            
            # Build user info dictionary
            user_info = {
                'User ID': user.id,
                'First Name': user.first_name,
                'Last Name': user.last_name,
                'Username': f"@{primary_username}" if primary_username else "No Username",
                'Alternate Usernames': ", ".join(alternate_usernames) if alternate_usernames else "None",
                'Phone': user.phone if user.phone else "Not Available",
                'Is Bot': "Yes" if user.bot else "No",
                'Verified': "Yes" if user.verified else "No",
                'Premium': "Yes" if user.premium else "No",
                'Scam': "Yes" if user.scam else "No",
                'Fake': "Yes" if user.fake else "No",
                'Restricted': "Yes" if user.restricted else "No",
                'Deleted': "Yes" if user.deleted else "No",
                'Status': status,
                'Access Hash': user.access_hash,
                'Photo ID': photo_id,
                'Photo DC ID': photo_dc_id,
                'Support': "Yes" if user.support else "No",
                'Contact': "Yes" if user.contact else "No",
                'Mutual Contact': "Yes" if user.mutual_contact else "No",
                'Close Friend': "Yes" if getattr(user, 'close_friend', False) else "No",
                'Stories Hidden': "Yes" if getattr(user, 'stories_hidden', False) else "No",
                'Language Code': user.lang_code if user.lang_code else "Not Available",
            }
            
            results.append(user_info)
            
        except ValueError as e:
            st.error(f"Invalid user ID format: {user_id}")
            results.append({
                'User ID': user_id,
                'Error': f"Invalid ID format: {e}"
            })
        except Exception as e:
            st.error(f"Error fetching user ID {user_id}: {e}")
            results.append({
                'User ID': user_id,
                'Error': str(e)
            })
    
    return results
