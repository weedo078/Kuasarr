# -*- coding: utf-8 -*-
# Kuasarr
# Project by weedo078 (Fork von https://github.com/rix1337/Quasarr)

import base64
import json
import os
import pickle
import urllib.parse

import requests
from bs4 import BeautifulSoup

from kuasarr.providers.log import info, debug

hostname = "dl"


def create_and_persist_session(shared_state):
    """Create a new DL session with username/password authentication."""
    host = shared_state.values["config"]("Hostnames").get(hostname)
    if not host:
        debug("DL hostname not configured")
        return None
    
    # Get credentials from config
    credentials_cfg = shared_state.values["config"](hostname.upper())
    user = credentials_cfg.get("user")
    pw = credentials_cfg.get("password")
    
    if not user or not pw:
        info(f"DL credentials not configured - please set username and password in config")
        # Fallback to cookie file method
        return _create_session_from_cookies(shared_state, host)
    
    dl_session = requests.Session()
    dl_session.headers.update({
        'User-Agent': shared_state.values.get("user_agent", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    })
    
    # XenForo login endpoint
    login_url = f"https://www.{host}/login/login"
    
    # First, get the login page to extract CSRF token
    try:
        login_page = dl_session.get(f"https://www.{host}/login/", timeout=30)
        soup = BeautifulSoup(login_page.text, 'html.parser')
        
        # Extract CSRF token from XenForo form
        csrf_token = None
        csrf_input = soup.find('input', {'name': '_xfToken'})
        if csrf_input:
            csrf_token = csrf_input.get('value', '')
        
        # Prepare login data
        login_data = {
            'login': user,
            'password': pw,
            'remember': '1',
            '_xfRedirect': f'https://www.{host}/',
            '_xfToken': csrf_token or ''
        }
        
        # Perform login
        response = dl_session.post(login_url, data=login_data, timeout=30)
        
        # Check if login was successful
        if response.status_code == 200:
            # Check for login indicators in response
            if 'data-logged-in="true"' in response.text or 'xf_user' in str(dl_session.cookies):
                info(f"DL login successful for user: {user}")
                
                # Validate the session
                if validate_session(dl_session, shared_state.values["config"]):
                    # Persist the session to database
                    _persist_session_to_db(shared_state, dl_session)
                    return dl_session
                else:
                    debug("DL session validation failed after login")
            else:
                info(f"DL login failed - check credentials for user: {user}")
        else:
            info(f"DL login request failed with status: {response.status_code}")
            
    except Exception as e:
        info(f"DL login error: {e}")
    
    # Fallback to cookie file method
    debug("Falling back to cookie file authentication")
    return _create_session_from_cookies(shared_state, host)


def _create_session_from_cookies(shared_state, host):
    """Fallback: Create session from cookie files (legacy method)."""
    dl_session = requests.Session()
    dl_session.headers.update({
        'User-Agent': shared_state.values.get("user_agent", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    })
    
    # Define cookie file paths
    cookie_paths = [
        "/app/dl_cookies.json",
        "/config/dl_cookies.json", 
        "dl_cookies.json"
    ]
    
    cookies_loaded = False
    for cookie_path in cookie_paths:
        if os.path.exists(cookie_path):
            try:
                with open(cookie_path, 'r') as f:
                    cookies_data = json.load(f)
                
                debug(f"Loading cookies from {cookie_path}")
                
                # Handle different cookie file formats
                if isinstance(cookies_data, list):
                    for cookie in cookies_data:
                        if cookie.get('domain') and host.strip().lower() in cookie['domain'].lower():
                            dl_session.cookies.set(
                                cookie['name'], 
                                cookie['value'], 
                                domain=cookie['domain'],
                                path=cookie.get('path', '/'),
                                secure=cookie.get('secure', False)
                            )
                            cookies_loaded = True
                
                elif 'cookie_details' in cookies_data:
                    cookie_details = cookies_data['cookie_details']
                    for name, details in cookie_details.items():
                        if details.get('domain') and host.strip().lower() in details['domain'].lower():
                            dl_session.cookies.set(
                                name,
                                details['value'],
                                domain=details['domain'],
                                path=details.get('path', '/'),
                                secure=details.get('secure', False)
                            )
                            cookies_loaded = True
                
                elif 'cookies' in cookies_data:
                    simple_cookies = cookies_data['cookies']
                    
                    for name, value in simple_cookies.items():
                        domain_to_use = f"www.{host.strip()}"
                        path_to_use = '/'
                        secure_to_use = True
                        
                        if 'cookie_details' in cookies_data and name in cookies_data['cookie_details']:
                            details = cookies_data['cookie_details'][name]
                            domain_to_use = details.get('domain', domain_to_use)
                            path_to_use = details.get('path', path_to_use)
                            secure_to_use = details.get('secure', secure_to_use)
                        
                        dl_session.cookies.set(
                            name,
                            value,
                            domain=domain_to_use,
                            path=path_to_use,
                            secure=secure_to_use
                        )
                        cookies_loaded = True
                
                if cookies_loaded:
                    debug(f"Successfully loaded cookies from {cookie_path}")
                    break
                    
            except Exception as e:
                debug(f"Failed to load cookies from {cookie_path}: {e}")
                continue
        
    if not cookies_loaded:
        debug("No valid cookie file found for DL")
        return None
    
    # Validate the session
    if validate_session(dl_session, shared_state.values["config"]):
        _persist_session_to_db(shared_state, dl_session)
        info(f"DL session created from cookies for {host}")
        return dl_session
    else:
        debug("DL cookie session validation failed")
        return None


def retrieve_and_validate_session(shared_state):
    """Retrieve and validate existing DL session from database."""
    session_string = shared_state.values["database"]("sessions").retrieve("dl")
    if not session_string:
        debug("No existing DL session found, creating new one")
        return create_and_persist_session(shared_state)
    
    try:
        serialized_session = base64.b64decode(session_string.encode('utf-8'))
        dl_session = pickle.loads(serialized_session)
        if not isinstance(dl_session, requests.Session):
            raise ValueError("Retrieved object is not a valid requests.Session instance.")
        
        # Validate the session
        hostname = shared_state.values["config"]("Hostnames").get("dl")
        if validate_session(dl_session, shared_state.values["config"]):
            debug("Retrieved DL session is valid")
            return dl_session
        else:
            debug("Retrieved DL session is invalid, creating new one")
            return create_and_persist_session(shared_state)
            
    except Exception as e:
        debug(f"DL session retrieval failed: {e}")
        return create_and_persist_session(shared_state)


def validate_session(session, config):
    """
    Validate a DL session by checking if we can access protected content.
    Uses the hostname from config instead of hardcoded values.
    """
    try:
        host = config("Hostnames").get(hostname)
        if not host:
            debug("DL hostname not configured for validation")
            return False
        
        # Check account page first
        account_url = f"https://www.{host}/account/"
        account_response = session.get(account_url, timeout=30)
        
        debug(f"DL validation: Account page status {account_response.status_code}, {len(session.cookies)} cookies")
        
        # Login required indicators
        login_indicators = [
            'Sie müssen sich registrieren',
            'Anmelden oder registrieren',
            'Log in or register',
            'Du musst dich einloggen',
            'data-logged-in="false"'
        ]
        
        # Success indicators
        success_indicators = [
            'data-logged-in="true"',
            'xf_user',
        ]
        
        # Check for login indicators
        for indicator in login_indicators:
            if indicator in account_response.text:
                debug(f"DL validation failed: login required ({indicator})")
                return False
        
        # Check for success indicators
        for indicator in success_indicators:
            if indicator in account_response.text:
                debug("DL validation successful: logged in")
                return True
        
        # Also check cookies for xf_user
        if any('xf_user' in cookie.name for cookie in session.cookies):
            debug("DL validation successful: xf_user cookie present")
            return True
        
        debug("DL validation: no clear indicators found")
        return False
        
    except Exception as e:
        debug(f"DL validation error: {e}")
        return False


def invalidate_session(shared_state):
    """Invalidate the current DL session."""
    db = shared_state.values["database"]("sessions")
    db.delete("dl")
    debug('DL session marked as invalid!')


def _persist_session_to_db(shared_state, sess):
    """
    Serialize & store the given requests.Session into the database under "dl".
    """
    blob = pickle.dumps(sess)
    token = base64.b64encode(blob).decode("utf-8")
    shared_state.values["database"]("sessions").update_store("dl", token)


def fetch_via_requests_session(shared_state, method: str, target_url: str, post_data: dict = None, timeout: int = 30):
    """
    Execute a request using the DL session.
    
    Args:
        shared_state: Shared state object
        method: "GET" or "POST"
        post_data: For POST only (will be sent as form-data)
        timeout: Request timeout in seconds
    
    Returns:
        Response object or None if session is invalid
    """
    sess = retrieve_and_validate_session(shared_state)
    if not sess:
        debug("Could not retrieve valid DL session")
        return None

    try:
        # Execute request
        if method.upper() == "GET":
            resp = sess.get(target_url, timeout=timeout)
        else:  # POST
            resp = sess.post(target_url, data=post_data, timeout=timeout)

        # Re-persist cookies, since the site might have modified them during the request
        _persist_session_to_db(shared_state, sess)

        return resp
        
    except Exception as e:
        debug(f"DL request failed: {e}")
        return None
