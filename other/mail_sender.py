from celery import Celery
from celery.schedules import crontab
import time
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from other.config import get_users_emails, get_new_films

rabbit_host = os.environ.get('RABBITMQ_HOST', 'localhost')
app = Celery('other.mail_sender', broker=f'pyamqp://guest:guest@{rabbit_host}//')

app.conf.imports = ('other.mail_sender',)

app.conf.beat_schedule = {
    'send-news-every-minute': {
        'task': 'mail_sender.start_newsletter_process',
        'schedule': crontab(hour=15, minute=0),
    },
}
app.conf.timezone = 'UTC'

@app.task
def send_registration_email(email, name):
    print(f"--- [EMAIL] Починаю відправку листа на {email} для {name} ---")

    smtp_host = os.environ.get('SMTP_HOST', 'localhost')
    smtp_port = int(os.environ.get('SMTP_PORT', 1025))
    smtp_user = os.environ.get('SMTP_USER')
    smtp_password = os.environ.get('SMTP_PASSWORD')
    smtp_from = os.environ.get('SMTP_FROM', 'noreply@example.com')

    msg = MIMEMultipart()
    msg['From'] = smtp_from
    msg['To'] = email
    msg['Subject'] = "Activation profile!"

    body = f"Hello {name},\n\nYour profile has been activated successfully."
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.ehlo()
        
        if smtp_port == 587:
            server.starttls()
            server.ehlo()

        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)

        server.sendmail(smtp_from, email, msg.as_string())
        server.quit()
        
        time.sleep(2)
        print(f"--- [EMAIL] Лист успішно відправлено на {email}! ---")
        return "Email Sent"

    except Exception as e:
        print(f"--- [EMAIL] Помилка при відправці листа: {e} ---")
        return f"Error: {e}"

@app.task
def send_personal_film_news(email, name):
    films = get_new_films()

    print(f"--- [EMAIL] Формую персональний лист для {name} ({email}) ---")

    smtp_host = os.environ.get('SMTP_HOST', 'localhost')
    smtp_port = int(os.environ.get('SMTP_PORT', 1025))
    smtp_user = os.environ.get('SMTP_USER')
    smtp_password = os.environ.get('SMTP_PASSWORD')
    smtp_from = os.environ.get('SMTP_FROM', 'noreply@example.com')

    msg = MIMEMultipart()
    msg['From'] = smtp_from
    msg['To'] = email
    msg['Subject'] = f"Новини кіно для {name}!"

    body = f"""Привіт, {name}!
    
    Новинки на сьогодні: {",".join(film.name for film in films)}
    """
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.ehlo()
        
        if smtp_port == 587:
            server.starttls()
            server.ehlo()

        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)

        server.sendmail(smtp_from, email, msg.as_string())
        server.quit()
        
        return f"News sent to {name}"
    except Exception as e:
        print(f"--- [EMAIL ERROR] {email}: {e} ---")
        return f"Error: {e}"

@app.task
def start_newsletter_process():
    print("--- [BEAT] Починаю масову розсилку ---")
    try:
        users = get_users_emails()
        
        print(f"--- [BEAT] Знайдено {len(users)} користувачів ---")

        for user in users:
            send_personal_film_news.delay(user.email, user.first_name)
    except Exception as e:
        print(f"--- [BEAT ERROR] {e} ---")
