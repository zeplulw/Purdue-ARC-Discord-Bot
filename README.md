Setup Instructions
1. Create and populate .env in root directory:
    - EMAIL_ADDRESS: Email Address
    - EMAIL_PASSWORD: Email Password
    - MAIL_SERVER: SMTP Mail Server Address
    - BOT_TOKEN: Discord Bot Token
    - GUILD_LIST: List of guilds for commands to register in. **(Will be removed after transferred to global slash commands)**

    *README won't be more specific until final publish.*
2. Create virtual environment: `python -m venv <venv_name>`.
3. Activate venv.
    - Windows: `./<venv_name>/Scripts/Activate.ps1`
    - Linux: `./<venv_name>/bin/activate`.
4. Set up packages: `pip install -r requirements.txt`.
5. Run `main.py`: `python main.py`
    - Persistent after terminal close: `nohup python main.py &`