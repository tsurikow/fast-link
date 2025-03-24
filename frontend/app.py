import streamlit as st
from config import settings
from helpers import (
    login_user,
    register_user,
    create_short_url,
    create_custom_short_url,
    search_url,
    update_url,
    delete_url,
    get_url_stats,
    get_current_user_info,
    fetch_url_list
)
st.set_page_config(page_title="Fast-Link App", layout="wide")

FASTAPI_URL = f"{settings.FASTAPI_URL}:{settings.FASTAPI_PORT}"
APP_TITLE = getattr(settings, "APP_TITLE", "Fast-Link Frontend")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "token" not in st.session_state:
    st.session_state.token = None

def page_login():
    st.header("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        token = login_user(email, password)
        if token:
            st.session_state.token = token
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Login failed. Check your credentials.")

def page_register():
    st.header("Register")
    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Password", type="password", key="reg_password")
    if st.button("Register"):
        if register_user(email, password):
            st.success("Registration successful! Please log in.")
        else:
            st.error("Registration failed. Try a different email.")

def page_logout():
    st.header("Log out")
    if st.button("Log out"):
        st.session_state.logged_in = False
        st.session_state.token = None
        st.rerun()

def page_current_user():
    st.header("Current User Information")
    token = st.session_state.get("token")
    if token:
        user_info = get_current_user_info(token)
        if user_info:
            st.json(user_info)
        else:
            st.error("Failed to retrieve current user information.")
    else:
        st.warning("You are not logged in.")

def page_create_short_url():
    st.header("Create New Short URL")
    original_url = st.text_input("Original URL")
    if st.button("Create URL"):
        token = st.session_state.get("token")
        short_code = create_short_url(original_url, token)
        if short_code:
            st.success(f"Short URL created: {short_code}")
            st.write(f"Access it at: {settings.APP_URL}{short_code}")

def page_custom_short_url():
    st.header("Create Custom Short URL")
    original_url = st.text_input("Original URL", key="custom_original")
    short_code = st.text_input("Custom Short Code", key="custom_code")
    expiration = st.text_input("Expiration (YYYY-MM-DDTHH:MM)", key="custom_expiration")
    if st.button("Create Custom URL"):
        token = st.session_state.get("token")
        if not token:
            st.error("You must be logged in to create a custom short link.")
            return
        data = {
            "original_url": original_url,
            "short_code": short_code,
            "expiration": expiration,
        }
        new_code = create_custom_short_url(data, token)
        if new_code:
            st.success(f"Custom Short URL created: {new_code}")
            st.write(f"Access it at: {settings.APP_URL}{new_code}")

def page_search():
    st.header("Search Short URL by Original URL")
    original_url = st.text_input("Enter Original URL to Search", key="search_url")
    if st.button("Search"):
        results = search_url(original_url)
        if results:
            st.write("Search Results:")
            st.json(results)

def page_update():
    st.header("Update Short URL")
    short_code = st.text_input("Short Code to Update", key="update_code")
    new_original_url = st.text_input("New Original URL", key="update_original")
    regenerate = st.checkbox("Generate new short code", value=True)
    if st.button("Update URL"):
        token = st.session_state.get("token")
        if not token:
            st.error("You must be logged in to update a short link.")
            return
        update_data = {
            "original_url": new_original_url,
            "regenerate": regenerate
        }
        result = update_url(short_code, update_data, token)
        if result:
            st.success("URL updated successfully.")
            st.json(result)

def page_delete():
    st.header("Delete Short URL")
    short_code = st.text_input("Short Code to Delete", key="delete_code")
    if st.button("Delete URL"):
        token = st.session_state.get("token")
        if not token:
            st.error("You must be logged in to delete a short link.")
            return
        result = delete_url(short_code, token)
        if result:
            st.success("URL deleted (moved to expired history) successfully.")
            st.json(result)

def page_url_list():
    st.header("My URL List")
    token = st.session_state.get("token")
    active_urls, expired_urls = fetch_url_list(token)
    st.subheader("Active URLs")
    if active_urls:
        st.table(active_urls)
    else:
        st.write("No active URLs found.")
    st.subheader("Expired URLs")
    if expired_urls:
        st.table(expired_urls)
    else:
        st.write("No expired URLs found.")

def page_stats():
    st.header("Short URL Statistics")
    short_code = st.text_input("Short Code", key="stats_code")
    if st.button("Get Stats"):
        token = st.session_state.get("token")
        stats = get_url_stats(short_code, token)
        if stats:
            st.json(stats)
        else:
            st.error("Failed to retrieve URL stats.")


login_pg = st.Page(page_login, title="Log in", icon=":material/login:")
logout_pg = st.Page(page_logout, title="Log out", icon=":material/logout:")
register_pg = st.Page(page_register, title="Register", icon=":material/person_add:")
current_user_pg = st.Page(page_current_user, title="Current User", icon=":material/account_circle:")
create_pg = st.Page(page_create_short_url, title="Create Short URL", icon=":material/link:")
custom_pg = st.Page(page_custom_short_url, title="Custom Short URL", icon=":material/edit:")
search_pg = st.Page(page_search, title="Search URL", icon=":material/search:")
url_list_pg = st.Page(page_url_list, title="My URLs", icon=":material/link:")
update_pg = st.Page(page_update, title="Update URL", icon=":material/update:")
delete_pg = st.Page(page_delete, title="Delete URL", icon=":material/delete:")
stats_pg = st.Page(page_stats, title="URL Stats", icon=":material/bar_chart:")

if st.session_state.logged_in:
    navigation = st.navigation({
        "Account": [logout_pg, current_user_pg],
        "URLs": [create_pg, custom_pg, url_list_pg, search_pg, update_pg, delete_pg, stats_pg],
    })
else:
    navigation = st.navigation([login_pg, register_pg, create_pg, search_pg, stats_pg])

navigation.run()