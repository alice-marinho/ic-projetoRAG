import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Defina isso no seu arquivo .env ou direto aqui para testar (mas não suba senhas pro GitHub!)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("EMAIL_USER", "seu_email@gmail.com")
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD", "sua_senha_de_app")


def send_approval_email(user_email, user_name):
    """
    Envia um email avisando que a conta foi aprovada.
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = user_email
        msg['Subject'] = "🎉 Seu acesso à Plataforma RAG foi liberado!"

        # Corpo do email em HTML (fica mais bonito)
        html_body = f"""
        <html>
          <body>
            <h2 style="color: #2e6c80;">Olá, {user_name}!</h2>
            <p>Temos ótimas notícias. Sua conta foi <strong>aprovada</strong> por um administrador.</p>
            <p>Você já pode acessar todas as funcionalidades da plataforma, incluindo o Chat Interdisciplinar.</p>
            <br>
            <a href="http://localhost:8501" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Acessar Plataforma Agora</a>
            <p style="font-size: 12px; color: gray;">Se você não solicitou este acesso, ignore este email.</p>
          </body>
        </html>
        """

        msg.attach(MIMEText(html_body, 'html'))

        # Conecta ao servidor e envia
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Criptografia
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, user_email, text)
        server.quit()

        print(f"Email enviado para {user_email}")
        return True

    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        return False