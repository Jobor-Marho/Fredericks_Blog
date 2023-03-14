from twilio.rest import Client
import smtplib
from dotenv.main import load_dotenv
import os


load_dotenv()
class NotificationManager:
    def __init__(self, msg: str, recipient: str, subject: str):
        self.message_data = msg
        self.recipient = recipient
        self.subject = subject
        # self.send_sms(self.message_data)
        self.send_email(self.message_data)

    def send_sms(self, message):
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        client = Client(account_sid, auth_token)

        client.messages.create(
            body=message,
            from_='+13465155809',
            to='+2349030480419'
        )

    def send_email(self, message):
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com") as connection:
                connection.login(user=os.environ['G_MAIL'], password=os.environ['GMAIL_PASSWORD'])
                connection.sendmail(from_addr=os.environ['G_MAIL'],
                                    to_addrs=self.recipient,
                                    msg=f"Subject:Hello {self.subject}\n\n{message}")
        except smtplib.SMTPServerDisconnected:
            return False
        else:
            return True

