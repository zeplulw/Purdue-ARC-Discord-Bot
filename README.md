Setup Instructions
1. Create and populate .env in root directory:
    - EMAIL_ADDRESS: Email Address
    - EMAIL_PASSWORD: Email Password
    - MAIL_SERVER: SMTP Mail Server Address
    - BOT_TOKEN: Discord Bot Token

    *README won't be more specific until final publish.*

2. Create `db.json` based on `db_schema.json`. Good luck.

    Populate `options`

2. Execute main.py based on OS:

    **Windows**: Run `./start.ps1`.

    *It will ask if you would like to run in the background. Selecting* `y` *will use* `pythonw.exe` *to run* `main.py`*, and can only be killed using Resource Monitor or the terminal*

    **Linux** *untested*

    1. Create virtual environment

        `python -m venv <venv_name>`.
    2. Activate `venv`.

        `./<venv_name>/bin/activate`.
    3. Install required packages

        `pip install -r requirements.txt`.
    4. Run `main.py`

        `python main.py`
        