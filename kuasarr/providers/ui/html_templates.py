# -*- coding: utf-8 -*-
# Kuasarr
# Project by weedo078 (Fork von https://github.com/rix1337/Quasarr)

import kuasarr.providers.ui.html_images as images
from kuasarr.providers.version import get_version


def render_centered_html(inner_content):
    head = '''
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="theme-color" content="#0d6efd">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <title>kuasarr</title>
        <link rel="icon" href="''' + images.logo + '''" type="image/png">
        <link rel="manifest" href="/static/manifest.webmanifest">
        <link rel="apple-touch-icon" href="/static/logo-192.png">
        <style>
            /* Theme variables */
            :root {
                --bg-color: #f8f9fa;
                --fg-color: #212529;
                --card-bg: #ffffff;
                --card-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
                --primary: #0d6efd;
                --primary-hover: #0b5ed7;
                --secondary: #6c757d;
                --secondary-hover: #5c636a;
                --code-bg: #e9ecef;
                --spacing: 1rem;
                --border-radius: 0.5rem;
                --info-border: #2d5a2d;
                --setup-border: var(--primary);
                --divider-color: #dee2e6;
                --btn-subtle-bg: #e9ecef;
                --btn-subtle-border: #ced4da;
            }
            @media (prefers-color-scheme: dark) {
                :root {
                    --bg-color: #121212;
                    --fg-color: #e9ecef;
                    --card-bg: #1e1e1e;
                    --card-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.5);
                    --code-bg: #2d2d2d;
                    --primary: #375a7f;
                    --primary-hover: #2b4764;
                    --secondary: #444444;
                    --secondary-hover: #333333;
                    --info-border: #4a8c4a;
                    --setup-border: var(--primary);
                    --divider-color: #444;
                    --btn-subtle-bg: #444;
                    --btn-subtle-border: #666;
                }
            }
            /* Info box styling */
            .info-box {
                border: 1px solid var(--info-border);
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 24px;
            }
            .info-box h3 {
                margin-top: 0;
                color: var(--info-border);
            }
            /* Setup box styling */
            .setup-box {
                border: 1px solid var(--setup-border);
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 24px;
            }
            .setup-box h3 {
                margin-top: 0;
                color: var(--setup-border);
            }
            /* Subtle button styling */
            .btn-subtle {
                background: var(--btn-subtle-bg);
                color: var(--fg-color);
                border: 1px solid var(--btn-subtle-border);
                padding: 6px 12px;
                border-radius: 4px;
                cursor: pointer;
            }
            /* Divider styling */
            .section-divider {
                margin-top: 20px;
                padding-top: 20px;
                border-top: 1px solid var(--divider-color);
            }
            /* Logo and heading alignment */
            h1 {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 0.5rem;
                font-size: 2rem;
            }
            .logo {
                width: 48px;
                height: 48px;
                margin-right: 0.5rem;
            }
            /* Form labels and inputs */
            label {
                display: block;
                font-weight: 600;
                margin-bottom: 0.5rem;
            }
            input, select {
                display: block;
                width: 100%;
                padding: 0.6rem 0.75rem;
                font-size: 1rem;
                border: 1px solid #ced4da;
                border-radius: var(--border-radius);
                background-color: var(--card-bg);
                color: var(--fg-color);
                box-sizing: border-box;
                transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
            }
            input:focus, select:focus {
                border-color: var(--primary);
                outline: 0;
                box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
            }
            *, *::before, *::after {
                box-sizing: border-box;
            }
            /* make body a column flex so footer can stick to bottom */
            html, body {
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                background-color: var(--bg-color);
                color: var(--fg-color);
                font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue',
                    'Noto Sans', Arial, sans-serif;
                line-height: 1.6;
                display: flex;
                flex-direction: column;
                min-height: 100vh;
            }
            .outer {
                flex: 1;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: var(--spacing);
            }
            .inner {
                background-color: var(--card-bg);
                border-radius: 1rem;
                box-shadow: var(--card-shadow);
                padding: calc(var(--spacing) * 2.5);
                text-align: center;
                width: 100%;
                max-width: fit-content;
            }
            /* No padding on the sides for captcha view on small screens */
            @media (max-width: 600px) {
                body:has(iframe) .outer {
                    padding-left: 0;
                    padding-right: 0;
                }
                body:has(iframe) .inner {
                    padding-left: 0;
                    padding-right: 0;
                }
            }
            h2 {
                margin-top: var(--spacing);
                margin-bottom: 0.75rem;
                font-size: 1.5rem;
            }
            h3 {
                margin-top: var(--spacing);
                margin-bottom: 0.5rem;
                font-size: 1.125rem;
                font-weight: 500;
            }
            p {
                margin: 0.5rem 0;
            }
            .copy-input {
                background-color: var(--code-bg);
            }
            .url-wrapper .api-key-wrapper {
                display: flex;
                gap: 0.5rem;
                flex-wrap: wrap;
                justify-content: center;
                margin-bottom: var(--spacing);
            }
            .captcha-container {
                background-color: var(--secondary);
            }
            button {
                padding: 0.6rem 1.2rem;
                font-size: 1rem;
                border-radius: var(--border-radius);
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease-in-out;
                border: none;
                margin-top: 0.75rem;
                display: inline-block;
            }
            .btn-primary {
                background-color: var(--primary);
                color: #fff;
            }
            .btn-primary:hover {
                background-color: var(--primary-hover);
                transform: translateY(-1px);
            }
            .btn-secondary {
                background-color: var(--secondary);
                color: #fff;
            }
            .btn-secondary:hover {
                background-color: var(--secondary-hover);
                transform: translateY(-1px);
            }
            button:active {
                transform: translateY(0);
            }
            button:disabled {
                opacity: 0.65;
                cursor: not-allowed;
                transform: none;
            }
            a {
                color: var(--primary);
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
            /* footer styling */
            footer {
                text-align: center;
                font-size: 0.75rem;
                color: var(--secondary);
                padding: 0.5rem 0;
            }
        </style>
    </head>'''

    sw_script = '''
        <script>
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('/static/sw.js')
                    .catch(function(err) {
                        console.log('SW registration failed:', err);
                    });
            }
        </script>
    '''

    body = f'''
    {head}
    <body>
        <div class="outer">
            <div class="inner">
                {inner_content}
            </div>
        </div>
        <footer>
            kuasarr v.{get_version()}
        </footer>
        {sw_script}
    </body>
    '''
    return f'<!DOCTYPE html><html lang="en">{body}</html>'


def render_button(text, button_type="primary", attributes=None):
    cls = "btn-primary" if button_type == "primary" else "btn-secondary"
    attr_str = ''
    if attributes:
        attr_str = ' '.join(f'{key}="{value}"' for key, value in attributes.items())
    return f'<button class="{cls}" {attr_str}>{text}</button>'


def render_form(header, form="", script=""):
    content = f'''
    <h1><img src="{images.logo}" type="image/png" alt="kuasarr logo" class="logo"/>kuasarr</h1>
    <h2>{header}</h2>
    {form}
    {script}
    '''
    return render_centered_html(content)


def render_success(message, timeout=10, optional_text=""):
    button_html = render_button(f"Wait time... {timeout}", "secondary", {"id": "nextButton", "disabled": "true"})
    script = f'''
        <script>
            let counter = {timeout};
            const btn = document.getElementById('nextButton');
            const interval = setInterval(() => {{
                counter--;
                btn.innerText = `Wait time... ${{counter}}`;
                if (counter === 0) {{
                    clearInterval(interval);
                    btn.innerText = 'Continue';
                    btn.disabled = false;
                    btn.className = 'btn-primary';
                    btn.onclick = () => window.location.href = '/';
                }}
            }}, 1000);
        </script>
    '''
    content = f'''<h1><img src="{images.logo}" type="image/png" alt="kuasarr logo" class="logo"/>kuasarr</h1>
    <h2>{message}</h2>
    {optional_text}
    {button_html}
    {script}
    '''
    return render_centered_html(content)


def render_fail(message):
    button_html = render_button("Back", "secondary", {"onclick": "window.location.href='/'"})
    return render_centered_html(f"""<h1><img src="{images.logo}" type="image/png" alt="kuasarr logo" class="logo"/>kuasarr</h1>
        <h2>{message}</h2>
        {button_html}
    """)



