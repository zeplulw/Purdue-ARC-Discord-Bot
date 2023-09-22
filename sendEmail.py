import smtplib
import ssl
import os
import dotenv
from email.message import EmailMessage

dotenv.load_dotenv()

class EmailSender:
    def __init__(self, sender_email, sender_password):
        self.sender_email = sender_email
        self.sender_password = sender_password

    def sendEmail(self, *, receiver: str, message_body: str, subject: str ='Purdue ARC Verification'):
        """
        Send an email.

        Args:
            receiver (str): The email address of the recipient.
            message_body (str): The body of the email message.
            subject (str, optional): The subject of the email (default is "Purdue ARC Verification").
        
        Returns:
            None
        """
        msg = EmailMessage()
        msg['From'] = self.sender_email
        msg['To'] = receiver
        msg['Subject'] = subject
        msg.set_content(message_body)

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL(os.getenv('MAIL_SERVER'), 465, context=context) as smtp:
            smtp.login(self.sender_email, self.sender_password)
            smtp.sendmail(self.sender_email, receiver, msg.as_string())