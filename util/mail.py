import smtplib
import socket
from email.mime.text import MIMEText
import datetime


class Email(object):
    def __init__(self, email_from, email_to, email_server, email_port,
                 email_password, bot_name):
        self.email_from = email_from
        self.email_to = email_to
        self.email_server = email_server
        self.email_port = email_port
        self.email_password = email_password
        self.bot_name = bot_name
        self._last_email_file = r"/tmp/oandabotemail.time"

    def _saveLastEmailTimestamp(self):
        try:
            file = open(self._last_email_file, "w")
            file.write(datetime.datetime.now().strftime("%s"))
            file.close()
        except:
            pass

    def _loadLastEmailTimestamp(self):
        timestamp = 0
        try:
            file = open(self._last_email_file, "r")
            timestamp = int(f.read())
            file.close()
        except:
            pass

        return ts

    def _can_email(self):
        now = int(datetime.datetime.now().strftime("%s"))
        then = self._loadLastEmailTimestamp()
        if now - then <= 30:
            return False
        return True

    def Send(self, text):

        if not self._can_email():
            self._saveLastEmailTimestamp()
            return

        hostname = socket.gethostname()

        txt = "This is a message from oandabot " + \
            self.bot_name + "(" + hostname + ")"
        txt += text

        e = MIMEText(txt, 'plain')
        e['Subject'] = "Oandabot " + self.bot_name + "(" + hostname + ")"
        e['From'] = self.email_from
        e['To'] = self.email_to

        s = smtplib.SMTP(self.email_server, self.email_port)
        s.login(self.email_from, self.email_password)
        s.sendmail(self.email_from, self.email_to, e.as_string())
        s.quit()

        self._saveLastEmailTimestamp()
