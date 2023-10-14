import smtplib
import ssl
import os
import dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

dotenv.load_dotenv()

class EmailSender:
    def __init__(self, sender_email: str, sender_password: str):
        self.sender_email = sender_email
        self.sender_password = sender_password

    # Will be used later to generalize sending multiple types of emails
    #
    # def __send_email(self, *, receiver: str, subject: str, body: str, body_type: str) -> None:
    #     msg = MIMEMultipart()
    #     msg['From'] = self.sender_email
    #     msg['To'] = receiver
    #     msg['Subject'] = subject
    #     msg.attach(MIMEText(body, body_type))

    #     with smtplib.SMTP_SSL(os.getenv('MAIL_SERVER'), 465, context=ssl.create_default_context()) as smtp:
    #         smtp.login(self.sender_email, self.sender_password)
    #         smtp.sendmail(self.sender_email, receiver, msg.as_string())

    def send_verification_email(self, *, username: str, receiver: str, verification_code: str, subject: str ='Purdue ARC Verification') -> None:
        
        """
        Send an email.

        Args:
            username (str): The username of the recipient.
            receiver (str): The email address of the recipient.
            verification_code (int): The body of the email message.
            subject (str, optional): The subject of the email (default is "Purdue ARC Verification").
        
        Returns:
            None
        """

        html = f"""
        <html>
            <head>
                <link rel="preconnect" href="https://fonts.googleapis.com">
                <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
                <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;700&family=Roboto+Mono:wght@500&display=swap" rel="stylesheet">
                <style>
                    * {{
                        font-family: sans-serif;
                        color: #141d3f;
                    }}
                    .container {{
                        width: 100%;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 2rem;
                        background-color: #316bcb;
                    }}
                    .container2 {{
                    width: calc(100% - 4rem);
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 2rem;
                    background-color: #fff;
                    border-radius: .5rem;
                    }}
                    h1 {{
                        margin: 0 auto;
                        font-size: 1.25rem;
                    }}
                    p {{
                        margin: 0 auto;
                    }}
                    span {{
                        font-weight: bold;
                        font-size: 1.5rem;
                    }}
                    code {{
                        font-family: monospace;
                        padding: 0.2rem 0.5rem;
                    }}
                    img {{
                        max-width: 300px;
                        margin: 0 auto;
                    }}
                    #verification-code {{
                        font-size: 2rem;
                        font-weight: bold;
                        display: inline-block;
                        width: 100%;
                        text-align: center;
                    }}
                    header {{
                        font-size: 2rem;
                        margin: 8px;
                        text-align: center;
                    }}

                    header img {{
                        padding: 1rem;
                        border-radius: .5rem;
                        background-color: #141d3f;
                        margin: 0 auto;
                    }}
                </style>
            </head>
            <body>
                <div class='container'>
                    <div class="container2">
                        <h1>Purdue ARC Verification (<i>{username}</i>)</h1>
                        <br>
                        <p>Your verification code is:</p>
                        <br>
                        <code id='verification-code'>{verification_code}</code>
                        <br><br>
                        <i>To use the code, simply paste the following: <code>/verify  verification_code:{verification_code}</code><br>You can also manually type <code>/verify</code> and paste the code</i>
                        <br><br>
                        <p>Thank you for joining Purdue ARC, whether you're a visitor or getting involved in a project!</p>
                    </div>
                </div>
            </body>
        </html>
        """
      
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = receiver
        msg['Subject'] = subject
        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP_SSL(os.getenv('MAIL_SERVER'), 465, context=ssl.create_default_context()) as smtp:
            smtp.login(self.sender_email, self.sender_password)
            smtp.sendmail(self.sender_email, receiver, msg.as_string())