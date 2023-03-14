from twilio.rest import Client
from formats import g_mail, gmail_password, yahoo_mail
import smtplib
import os


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
        with smtplib.SMTP_SSL("smtp.gmail.com") as connection:
            connection.login(user=g_mail, password=gmail_password)
            connection.sendmail(from_addr=g_mail,
                                to_addrs=self.recipient,
                                msg=f"Subject:Hello {self.subject}\n\n{message}")


