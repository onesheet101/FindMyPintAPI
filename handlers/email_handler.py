from email.message import EmailMessage
import smtplib


#As the function name suggests, this just sends a confirmation email to the given address.
def send_confirmation(email_receiver, context, config, email_password):
    email_sender = config.get('EMAIL', 'SENDER')
    email_subject = config.get('EMAIL', 'SUBJECT')
    body = config.get('EMAIL', 'BODY')

    confirmation = EmailMessage()
    confirmation['From'] = email_sender
    confirmation['To'] = email_receiver
    confirmation['Subject'] = email_subject

    confirmation.set_content(body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(email_sender, email_password)
            smtp.sendmail(email_sender, email_receiver, confirmation.as_string())
            return True
    except Exception as e:
        return False
