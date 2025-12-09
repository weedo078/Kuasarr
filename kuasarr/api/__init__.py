# -*- coding: utf-8 -*-
# Kuasarr
# Project by weedo078 (Fork von https://github.com/rix1337/Quasarr)

import os

from bottle import Bottle, static_file
from kuasarr.api.arr import setup_arr_routes
from kuasarr.api.captcha import setup_captcha_routes
from kuasarr.api.config import setup_config
from kuasarr.api.hosters import setup_hosters_routes
from kuasarr.api.sponsors_helper import setup_sponsors_helper_routes
from kuasarr.api.statistics import setup_statistics
from kuasarr.providers import shared_state
from kuasarr.providers.html_templates import render_button, render_centered_html
from kuasarr.providers.web_server import Server
from kuasarr.storage.config import Config


def get_api(shared_state_dict, shared_state_lock):
    shared_state.set_state(shared_state_dict, shared_state_lock)

    app = Bottle()

    setup_arr_routes(app)
    setup_captcha_routes(app)
    setup_config(app, shared_state)
    setup_hosters_routes(app)
    setup_statistics(app, shared_state)
    setup_sponsors_helper_routes(app)

    # Serve static files (logo)
    @app.get('/static/<filename:path>')
    def serve_static(filename):
        static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
        return static_file(filename, root=static_dir)

    @app.get('/')
    def index():
        protected = shared_state.get_db("protected").retrieve_all_titles()
        api_key = Config('API').get('key')

        captcha_hint = ""
        if protected:
            plural = 's' if len(protected) > 1 else ''
            captcha_hint += f"""
            <div class="section">
                <h2>Link{plural} waiting for CAPTCHA solution</h2>
                """

            if not shared_state.values.get("helper_active"):
                captcha_hint += """
                <p>
                    Enable the integrated CaptchaHelper to automatically decrypt protected packages.
                </p>
                """

            plural = 's' if len(protected) > 1 else ''
            captcha_hint += f"""
                <p>{render_button(f"Solve CAPTCHA{plural}", 'primary', {'onclick': "location.href='/captcha'"})}</p>
            </div>
            <hr>
            """

        info = f"""
        <div class="header-section">
            <img src="/static/logo.png" alt="Kuasarr Logo" class="main-logo"/>
            <p class="tagline">Automated Downloads for Sonarr & Radarr</p>
        </div>

        {captcha_hint}

        <div class="section">
            <h2>📖 Setup Instructions</h2>
            <p>
                <a href="https://github.com/weedo078/kuasarr" target="_blank">
                    📚 Refer to the README for detailed instructions.
                </a>
            </p>
        </div>

        <hr>

        <div class="section">
            <h2>🔧 API Configuration</h2>
            <p>Use the URL and API Key below to set up a <strong>Newznab Indexer</strong> and <strong>SABnzbd Download Client</strong> in Radarr/Sonarr:</p>

            <details id="apiDetails">
                <summary id="apiSummary">🔑 Show API Settings</summary>
                <div class="api-settings">

                    <h3>🌐 URL</h3>
                    <div class="url-wrapper">
                      <input id="urlInput" class="copy-input" type="text" readonly value="{shared_state.values['internal_address']}" />
                      <button id="copyUrl" class="btn-primary small">📋 Copy</button>
                    </div>

                    <h3>🔐 API Key</h3>
                    <div class="api-key-wrapper">
                      <input id="apiKeyInput" class="copy-input" type="password" readonly value="{api_key}" />
                      <button id="toggleKey" class="btn-secondary small">👁️ Show</button>
                      <button id="copyKey" class="btn-primary small">📋 Copy</button>
                    </div>

                    <p>{render_button("🔄 Regenerate API key", "secondary", {"onclick": "if(confirm('Regenerate API key?')) location.href='/regenerate-api-key';"})}</p>
                </div>
            </details>
        </div>

        <hr>

        <div class="section">
            <h2>⚡ Quick Actions</h2>
            <div class="action-grid">
                <button class="action-btn" onclick="location.href='/hostnames'">
                    <span class="action-icon">🌍</span>
                    <span class="action-text">Update Hostnames</span>
                </button>
                <button class="action-btn" onclick="location.href='/hosters'">
                    <span class="action-icon">🚫</span>
                    <span class="action-text">Manage Hosters</span>
                </button>
                <button class="action-btn" onclick="location.href='/statistics'">
                    <span class="action-icon">📊</span>
                    <span class="action-text">View Statistics</span>
                </button>
                <button class="action-btn" onclick="location.href='/captcha'">
                    <span class="action-icon">🔓</span>
                    <span class="action-text">CAPTCHA Queue</span>
                </button>
            </div>
        </div>

        <style>
            .header-section {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .main-logo {{
                width: 150px;
                height: auto;
                margin-bottom: 10px;
                filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2));
            }}
            .tagline {{
                font-size: 1.1em;
                color: #666;
                margin: 0;
            }}
            body.dark .tagline {{
                color: #aaa;
            }}
            .section {{ margin: 20px 0; }}
            .api-settings {{ padding: 15px 0; }}
            hr {{ margin: 25px 0; border: none; border-top: 1px solid #ddd; }}
            details {{ margin: 10px 0; }}
            summary {{ 
                cursor: pointer; 
                padding: 8px 0; 
                font-weight: 500;
            }}
            summary:hover {{ 
                color: #0066cc; 
            }}
            .action-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
                gap: 12px;
                margin-top: 15px;
            }}
            .action-btn {{
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 20px 15px;
                border: 1px solid rgba(13, 110, 253, 0.3);
                border-radius: 12px;
                background: linear-gradient(135deg, rgba(13, 110, 253, 0.08) 0%, rgba(13, 110, 253, 0.15) 100%);
                cursor: pointer;
                transition: all 0.2s ease;
            }}
            .action-btn:hover {{
                transform: translateY(-3px);
                box-shadow: 0 6px 20px rgba(13, 110, 253, 0.25);
                border-color: #0d6efd;
            }}
            .action-icon {{
                font-size: 2em;
                margin-bottom: 8px;
            }}
            .action-text {{
                font-size: 0.9em;
                font-weight: 500;
                color: #1f2933;
            }}
            @media (prefers-color-scheme: dark) {{
                .action-text {{
                    color: #f8f9fa;
                }}
            }}
            body.dark .action-btn {{
                background: linear-gradient(135deg, rgba(13, 110, 253, 0.15) 0%, rgba(13, 110, 253, 0.25) 100%);
            }}
        </style>

        <script>
          const urlInput = document.getElementById('urlInput');
          const copyUrlBtn = document.getElementById('copyUrl');

          if (copyUrlBtn) {{
            copyUrlBtn.onclick = () => {{
              urlInput.select();
              document.execCommand('copy');
              copyUrlBtn.innerText = '✅ Copied!';
              setTimeout(() => {{ copyUrlBtn.innerText = '📋 Copy'; }}, 2000);
            }};
          }}

          const apiInput = document.getElementById('apiKeyInput');
          const toggleBtn = document.getElementById('toggleKey');
          const copyBtn = document.getElementById('copyKey');

          if (toggleBtn) {{
            toggleBtn.onclick = () => {{
              const isHidden = apiInput.type === 'password';
              apiInput.type = isHidden ? 'text' : 'password';
              toggleBtn.innerText = isHidden ? '🙈 Hide' : '👁️ Show';
            }};
          }}

          if (copyBtn) {{
            copyBtn.onclick = () => {{
              apiInput.type = 'text';
              apiInput.select();
              document.execCommand('copy');
              copyBtn.innerText = '✅ Copied!';
              toggleBtn.innerText = '🙈 Hide';
              setTimeout(() => {{ copyBtn.innerText = '📋 Copy'; }}, 2000);
            }};
          }}

          // Handle details toggle
          const apiDetails = document.getElementById('apiDetails');
          const apiSummary = document.getElementById('apiSummary');

          if (apiDetails && apiSummary) {{
            apiDetails.addEventListener('toggle', () => {{
              if (apiDetails.open) {{
                apiSummary.textContent = '🔒 Hide API Settings';
              }} else {{
                apiSummary.textContent = '🔑 Show API Settings';
              }}
            }});
          }}
        </script>
        """
        return render_centered_html(info)

    @app.get('/regenerate-api-key')
    def regenerate_api_key():
        api_key = shared_state.generate_api_key()
        return f"""
        <script>
          alert('API key replaced with: {api_key}');
          window.location.href = '/';
        </script>
        """

    Server(app, listen='0.0.0.0', port=shared_state.values["port"]).serve_forever()



