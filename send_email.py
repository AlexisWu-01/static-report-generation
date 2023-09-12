"""
Author: Andrew DeCandia, Alexis (Xinyi) Wu
Project: Air Partners

Script for sending emails with attachments from a gmail account.
"""
import smtplib
import sys
import os
import pandas as pd
import datetime as dt
import argparse
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders
from utils.zip_directory import zip_directory
from utils.dropbox_util import upload_zip,delete_zip, TransferData


def send_mail(send_from, send_to, subject, message, files=[],
              server="localhost", port=587, username='', password='',
              use_tls=True):
    """
    Compose and send email with provided info and attachments.

    :param send_from: (str) from name
    :param send_to: (list[str]) to name(s)
    :param subject (str): message title
    :param message (html): message body
    :param files (list[str]): list of file paths to be attached to email
    :param server (str): mail server host name
    :param port (int): port number
    :param username (str): server auth username
    :param password (str): server auth password
    :param use_tls (bool): use TLS mode
    :returns: none, sends an email
    """
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'html'))

    for path in files:
        part = MIMEBase('application', "octet-stream")
        with open(path, 'rb') as file:
            part.set_payload(file.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        'attachment; filename={}'.format(Path(path).name))
        msg.attach(part)

    smtp = smtplib.SMTP(server, port)
    if use_tls:
        smtp.starttls()
    try:
        smtp.login(username, password)
        print("Logged in to email account.")
    except smtplib.SMTPAuthenticationError:
        print("SMTP Authentication Error: Unable to login to the email account. Please check your credentials.")
        smtp.quit()
        return
    try:
        smtp.sendmail(send_from, send_to, msg.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")
    smtp.quit()


def get_mailling_list():
    """
    Get list of subscribed emails to send to
    """
    df = pd.read_csv('maillist.csv')
    df = df.loc[df['Status of Subscription'] == 'Subbed']
    mailing_list = df['Emails'].tolist()
    return mailing_list

def handle_dropbox_upload(year_month):
    """ 
    Upload zip file to Dropbox; if file already exists, replace it.
    """
    try:
        upload_zip(year_month)
    except:
        delete_zip(year_month)
        upload_zip(year_month)

def main(year, month, upload_to_dropbox, send_email):
    """Main function to handle the email sending process."""
    date_obj = dt.date(year, month, 1)
    year_month = date_obj.isoformat()[:-3]

    #check if dropbox_creds.json exists and if not, set it up
    if not os.path.exists(TransferData.CRED_FILE):
        TransferData().setup_dropbox_credentials()
    zip_directory(year_month)
    if upload_to_dropbox:
        handle_dropbox_upload(year_month)
    if send_email:
        # Get password from saved location
        with open('creds/app_password.txt', 'r') as f:
            password = f.read().strip()

        # Get list of subscribed emails to send to
        mailing_list = get_mailling_list()

        # Send emails individually to preserve anonymity of subscribers
        for email in mailing_list:
            send_mail(
                send_from="Air Partners Reports <reports@airpartners.org>",
                send_to=[email],
                subject=f'Air Quality Reports {year_month}',
                message="""<a href="https://www.dropbox.com/sh/spwnq0yqvjvewax/AADk0c2Tum-7p_1ul6xiKzrPa?dl=0">These reports</a> 
                have been automatically generated based on last month's air quality data. To access the reports, unzip 
                the folder and navigate to reports then pdfs. In graphs we have included high res images of the graphs 
                used in the reports for use in presentations or other media.<br>
                If you want to know more about how these visuals were made, please visit airpartners.org.<br><br>
                Please note that at the end of this month, the current zip file will be deleted and replaced with this 
                month's data.<br><br>
                Long Link:<br>https://www.dropbox.com/sh/spwnq0yqvjvewax/AADk0c2Tum-7p_1ul6xiKzrPa?dl=0<br><br>
                Best regards,<br>Air Partners<br><br><br>
                <a href="https://forms.gle/z9jPc8QNVRCCyChQ7">Unsubscribe</a>""",
                # files=[],
                server='smtp.gmail.com',
                username='airpartners@airpartners.org',
                password=password
            )

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Send reports via email and/or upload to Dropbox.")
    parser.add_argument("year", type=int, help="Year for the report.")
    parser.add_argument("month", type=int, help="Month for the report.")
    parser.add_argument("--no-email", action="store_false", dest="send_email", help="Do not send emails.")
    parser.add_argument("--no-dropbox", action="store_false", dest="upload_to_dropbox", help="Do not upload to Dropbox.")
    
    args = parser.parse_args()
    
    main(args.year, args.month, upload_to_dropbox = args.upload_to_dropbox, send_email=args.send_email)