import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from urllib.parse import urlparse

# Config and Error Handling
def get_config():
    try:
        return {
            "web": {
                "client_id": st.secrets["GOOGLE_CLIENT_ID"],
                "client_secret": st.secrets["GOOGLE_CLIENT_SECRET"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [st.secrets.get("DEPLOYMENT_URL", "https://your-app-name.streamlit.app")],
                "javascript_origins": [st.secrets.get("DEPLOYMENT_URL", "https://your-app-name.streamlit.app")]
            }
        }
    except KeyError:
        st.error("""
        Missing required secrets. Please add the following to your secrets:
        - GOOGLE_CLIENT_ID
        - GOOGLE_CLIENT_SECRET
        - DEPLOYMENT_URL
        
        Go to your Streamlit app settings -> Secrets and add them in TOML format:
        ```toml
        GOOGLE_CLIENT_ID = "your-google-client-id"
        GOOGLE_CLIENT_SECRET = "your-google-client-secret"
        DEPLOYMENT_URL = "https://your-app-name.streamlit.app"
        ```
        """)
        st.stop()

# Google Authentication Class
class GoogleAuth:
    def __init__(self, client_config):
        self.client_config = client_config
        self.flow = None
    
    def get_redirect_uri(self):
        return self.client_config['web']['redirect_uris'][0]
        
    def initialize_flow(self):
        self.flow = Flow.from_client_config(
            self.client_config,
            scopes=['https://www.googleapis.com/auth/userinfo.profile', 
                   'https://www.googleapis.com/auth/userinfo.email'],
            redirect_uri=self.get_redirect_uri()
        )
    
    def get_authorization_url(self):
        if not self.flow:
            self.initialize_flow()
        auth_url, _ = self.flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        return auth_url
    
    def get_user_info(self, code):
        if not self.flow:
            self.initialize_flow()
        self.flow.fetch_token(code=code)
        credentials = self.flow.credentials
        
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        return user_info

# Session State Initialization
def initialize_session_state():
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'authentication_error' not in st.session_state:
        st.session_state.authentication_error = None
    st.session_state.current_url = st.secrets.get("DEPLOYMENT_URL", "https://your-app-name.streamlit.app")

# Main Application
def main():
    st.set_page_config(
        page_title="YouTube Chatbot Login",
        page_icon="🤖",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Create two columns for the header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🤖 YouTube Chatbot")
    
    # Show any authentication errors
    if st.session_state.authentication_error:
        st.error(st.session_state.authentication_error)
        st.session_state.authentication_error = None
    
    try:
        # Get configuration
        GOOGLE_CLIENT_CONFIG = get_config()
        
        # Initialize Google Auth
        auth = GoogleAuth(GOOGLE_CLIENT_CONFIG)
        
        # Check if user is logged in
        if st.session_state.user_info is None:
            if 'code' not in st.experimental_get_query_params():
                st.info("Please login to continue")
                # Show login button
                try:
                    auth_url = auth.get_authorization_url()
                    st.markdown(
                        f'<div style="display: flex; justify-content: center; margin: 20px;">'
                        f'<a href="{auth_url}" target="_self">'
                        '<button style="background-color: #4285F4; color: white; '
                        'padding: 12px 24px; border: none; border-radius: 4px; '
                        'cursor: pointer; font-size: 16px; display: flex; '
                        'align-items: center; gap: 10px;">'
                        'Log in with Google</button></a></div>', 
                        unsafe_allow_html=True
                    )
                except Exception as e:
                    st.error(f"Failed to generate authentication URL: {str(e)}")
            else:
                # Handle the OAuth callback
                with st.spinner("Authenticating..."):
                    code = st.experimental_get_query_params()['code'][0]
                    try:
                        user_info = auth.get_user_info(code)
                        st.session_state.user_info = user_info
                        # Clear the URL parameters
                        st.experimental_set_query_params()
                        st.experimental_rerun()
                    except Exception as e:
                        st.session_state.authentication_error = f"Authentication failed: {str(e)}"
                        st.experimental_set_query_params()
                        st.experimental_rerun()
        else:
            # Show user info in the header's second column
            with col2:
                st.write(f"👤 {st.session_state.user_info['name']}")
                if st.button("Logout", type="primary", key="logout"):
                    st.session_state.user_info = None
                    st.experimental_rerun()
            
            # Main app content
            st.write("---")
            st.success("You're successfully logged in! The chatbot is ready to use.")
            
            # Add your chatbot UI and functionality here
            st.write("Your chatbot interface goes here!")
            
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.stop()

if __name__ == "__main__":
    main()
