# email.py
import os
import smtplib
import secrets
import string
from tools.users_manip import update_user_password, user_exists
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Blueprint, request, jsonify, url_for
from datetime import datetime, timedelta

email_bp = Blueprint("email", __name__)
RESET_TOKENS = {}

# ==========================
# CONFIGURAÇÃO SMTP DINÂMICA
# ==========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # sobe de routes/ para raiz
CREDS_PATH = os.path.join(BASE_DIR, "data", "email_creds.key")

# Se não existir, cria com campos em branco
if not os.path.exists(CREDS_PATH):
    os.makedirs(os.path.dirname(CREDS_PATH), exist_ok=True)
    with open(CREDS_PATH, "w") as f:
        f.write("EMAIL=\nPW_APP=\n")
    print(f"[INFO] Arquivo de credenciais criado em {CREDS_PATH}. Preencha EMAIL e PW_APP.")

SMTP_USER = None
SMTP_PASS = None

# Lê credenciais
with open(CREDS_PATH, "r") as f:
    for line in f:
        line = line.strip()
        if line.startswith("EMAIL="):
            SMTP_USER = line.split("=",1)[1].strip()
        elif line.startswith("PW_APP="):
            SMTP_PASS = line.split("=",1)[1].strip()

# Valida se foram preenchidas
if not SMTP_USER or not SMTP_PASS:
    raise ValueError(f"As credenciais do arquivo {CREDS_PATH} não foram preenchidas! "
                     f"Preencha EMAIL e PW_APP antes de iniciar o app.")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
FROM_EMAIL = "suporte@amapazombies.com.br"

# ==========================
# Rota: requisitar reset
# ==========================
@email_bp.route("/forgot_password", methods=["POST"])
def forgot_password():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"status": "error", "message": "Informe o email."}), 400

    if not user_exists(email):
        return jsonify({"status": "error", "message": "Email não cadastrado."}), 404

    token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    RESET_TOKENS[token] = {
        "email": email,
        "expires": datetime.now() + timedelta(hours=1)
    }

    reset_link = url_for("email.reset_password", token=token, _external=True)

    # Monta mensagem HTML estilizada
    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f2f2f2;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 20px auto;
                background-color: #ffffff;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }}
            .header {{
                background-color: darkgreen;
                text-align: center;
                padding: 25px;
            }}
            .header img {{
                max-width: 100%;
                height: auto;
            }}
            .content {{
                padding: 35px;
                color: #333333;
                line-height: 1.6;
                font-size: 16px;
                font-family: Arial, sans-serif;
            }}
            .btn {{
                display: inline-block;
                padding: 14px 28px;
                background-color: darkgreen;
                color: white !important;
                text-decoration: none;
                font-weight: bold;
                font-size: 16px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .btn:hover {{
                background-color: #006400;
            }}
            .fallback {{
                font-size: 13px;
                color: #555555;
                word-break: break-all;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="https://amapazombies.com.br/static/images/amapazombies_logo.png" alt="Amapá Zombies">
            </div>
            <div class="content">
                <p>Olá,</p>
                <p>Você solicitou a redefinição de senha no <b>Amapá Zombies</b>.</p>
                <p>Este link é válido por <b>1 hora</b> e deve ser usado apenas por você. Não compartilhe com ninguém.</p>
                <p>Clique no botão abaixo para redefinir sua senha:</p>
                <p style="text-align:center;">
                    <a class="btn" href="{reset_link}">Redefinir senha</a>
                </p>
                <p class="fallback">Caso o botão não funcione, copie e cole este link no navegador:</p>
                <p class="fallback">{reset_link}</p>
                <p>Se você não solicitou esta ação, ignore este email.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Monta mensagem MIME
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Recuperação de Senha - Amapá Zombies"
    msg["From"] = f"Amapá Zombies <{FROM_EMAIL}>"
    msg["To"] = email
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, email, msg.as_string())
        return jsonify({"status": "success", "message": "Email de recuperação enviado."})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Erro ao enviar: {str(e)}"}), 500

# ==========================
# Rota: resetar senha
# ==========================
@email_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    info = RESET_TOKENS.get(token)

    # ================== TOKEN INVÁLIDO OU EXPIRADO ==================
    if not info or datetime.now() > info["expires"]:
        return f"""
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
            <link rel="icon" type="image/png" href="https://amapazombies.com.br/static/images/icon.png" />
            <title>Token inválido - Amapá Zombies</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f2f2f2;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    color: darkgreen;
                    text-align: center;
                }}
                .logo {{
                    position: absolute;
                    top: 20px;
                    left: 20px;  /* Alterado para esquerda */
                }}
                .logo img {{
                    height: 60px;
                }}
                .container {{
                    background-color: #ffffff;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 0 15px rgba(0,0,0,0.2);
                    max-width: 400px;
                    width: 100%;
                }}
                h2 {{
                    margin-bottom: 20px;
                }}
                p {{
                    margin-bottom: 30px;
                }}
                .btn {{
                    padding: 12px 24px;
                    background-color: white;
                    border: 2px solid darkgreen;
                    border-radius: 8px;
                    color: darkgreen;
                    font-weight: bold;
                    text-decoration: none;
                    display: inline-block;
                    cursor: pointer;
                }}
                .btn:hover {{
                    background-color: darkgreen;
                    color: white;
                }}
            </style>
        </head>
        <body>
            <a class="logo" href="https://amapazombies.com.br">
                <img src="https://amapazombies.com.br/static/images/common/amapazombies.png" alt="Amapá Zombies">
            </a>
            <div class="container">
                <h2>Token inválido ou expirado</h2>
                <p>O link que você tentou acessar não é mais válido. Por favor, solicite uma nova redefinição de senha.</p>
                <a class="btn" href="https://amapazombies.com.br">Voltar para página inicial</a>
            </div>
        </body>
        </html>
        """, 400

    # ================== GET: PÁGINA DE REDEFINIÇÃO ==================
    if request.method == "GET":
        reset_html = f"""
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
            <link rel="icon" type="image/png" href="https://amapazombies.com.br/static/images/icon.png" />
            <title>Redefinir Senha - Amapá Zombies</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f2f2f2;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    height: 100vh;
                    margin: 0;
                    color: darkgreen;
                }}
                .logo {{
                    position: absolute;
                    top: 20px;
                    left: 20px;
                }}
                .logo img {{
                    height: 60px;
                }}
                .form-container {{
                    background-color: #ffffff;
                    width: 400px;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 0 15px rgba(0,0,0,0.2);
                    text-align: center;
                    position: relative;
                }}
                input[type="password"] {{
                    width: 100%;
                    padding: 12px;
                    margin: 15px 0;
                    border: 2px solid darkgreen;
                    border-radius: 8px;
                    font-size: 16px;
                }}
                button {{
                    width: 100%;
                    padding: 14px;
                    background-color: darkgreen;
                    color: white;
                    font-size: 16px;
                    font-weight: bold;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                }}
                button:disabled {{
                    background-color: #999;
                    cursor: not-allowed;
                }}
                button:hover:not(:disabled) {{
                    background-color: #006400;
                }}
                h2 {{
                    margin-bottom: 20px;
                }}
                .password-tooltip {{
                    display: none;
                    position: absolute;
                    bottom: 100%;
                    left: 0;
                    width: 100%;
                    text-align: left;
                    background-color: darkgreen;
                    border-radius: 8px;
                    padding: 15px;
                    font-size: 14px;
                    line-height: 1.5;
                    color: #ff4d4d;
                    margin-bottom: 10px;
                }}
                .password-tooltip p {{
                    margin: 5px 0;
                }}
                .password-tooltip p.valid {{
                    color: greenyellow;
                    font-weight: bold;
                }}
                .input-wrapper {{
                    position: relative;
                    width: 100%;
                }}
            </style>
        </head>
        <body>
            <a class="logo" href="https://amapazombies.com.br">
                <img src="https://amapazombies.com.br/static/images/common/amapazombies.png" alt="Amapá Zombies">
            </a>
            <div class="form-container">
                <h2>Redefinir Senha</h2>
                <form method="POST" id="reset-form">
                    <div class="input-wrapper">
                        <div class="password-tooltip" id="password-tooltip">
                            <p id="rule-password-length">• Mínimo de 8 caracteres</p>
                            <p id="rule-password-upper">• Deve conter pelo menos uma letra maiúscula</p>
                            <p id="rule-password-lower">• Deve conter pelo menos uma letra minúscula</p>
                            <p id="rule-password-number">• Deve conter pelo menos um número</p>
                            <p id="rule-password-special">• Deve conter pelo menos um caractere especial (!@#$%^&*)</p>
                        </div>
                        <input type="password" id="password" name="password" placeholder="Nova senha" required>
                    </div>
                    <button type="submit" id="submit-btn" disabled>Salvar</button>
                </form>
            </div>
            <script>
            const passwordInput = document.getElementById("password");
            const passwordTooltip = document.getElementById("password-tooltip");
            const submitBtn = document.getElementById("submit-btn");

            const rules = [
                document.getElementById("rule-password-length"),
                document.getElementById("rule-password-upper"),
                document.getElementById("rule-password-lower"),
                document.getElementById("rule-password-number"),
                document.getElementById("rule-password-special")
            ];

            passwordInput.addEventListener("focus", () => {{
                passwordTooltip.style.display = "block";
            }});

            passwordInput.addEventListener("blur", () => {{
                passwordTooltip.style.display = "none";
            }});

            passwordInput.addEventListener("input", (e) => {{
                const value = e.target.value.trim();
                let allValid = true;

                if (value.length >= 8) {{ rules[0].classList.add("valid"); }} else {{ rules[0].classList.remove("valid"); allValid=false; }}
                if (/[A-Z]/.test(value)) {{ rules[1].classList.add("valid"); }} else {{ rules[1].classList.remove("valid"); allValid=false; }}
                if (/[a-z]/.test(value)) {{ rules[2].classList.add("valid"); }} else {{ rules[2].classList.remove("valid"); allValid=false; }}
                if (/[0-9]/.test(value)) {{ rules[3].classList.add("valid"); }} else {{ rules[3].classList.remove("valid"); allValid=false; }}
                if (/[!@#$%^&*]/.test(value)) {{ rules[4].classList.add("valid"); }} else {{ rules[4].classList.remove("valid"); allValid=false; }}

                submitBtn.disabled = !allValid;
            }});
            </script>
        </body>
        </html>
        """
        return reset_html

    # ================== POST: PROCESSA NOVA SENHA ==================
    if request.method == "POST":
        new_password = request.form.get("password")

        import re
        errors = []
        if len(new_password) < 8:
            errors.append("Senha deve ter pelo menos 8 caracteres.")
        if not re.search(r"[A-Z]", new_password):
            errors.append("Senha deve ter pelo menos uma letra maiúscula.")
        if not re.search(r"[a-z]", new_password):
            errors.append("Senha deve ter pelo menos uma letra minúscula.")
        if not re.search(r"[0-9]", new_password):
            errors.append("Senha deve ter pelo menos um número.")
        if not re.search(r"[!@#$%^&*]", new_password):
            errors.append("Senha deve ter pelo menos um caractere especial (!@#$%^&*).")

        if errors:
            return "<br>".join(errors), 400

        email = info["email"]

        if update_user_password(email, new_password):
            del RESET_TOKENS[token]

            # ================== PÁGINA DE SUCESSO COM REDIRECIONAMENTO ==================
            return f"""
            <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
                <link rel="icon" type="image/png" href="https://amapazombies.com.br/static/images/icon.png" />
                <title>Senha redefinida - Amapá Zombies</title>
                <meta http-equiv="refresh" content="5; url=https://amapazombies.com.br">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background-color: #f2f2f2;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        color: darkgreen;
                        text-align: center;
                    }}
                    .logo {{
                        position: absolute;
                        top: 20px;
                        left: 20px;
                    }}
                    .logo img {{
                        height: 60px;
                    }}
                    .container {{
                        background-color: #ffffff;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 0 15px rgba(0,0,0,0.2);
                        max-width: 400px;
                        width: 100%;
                    }}
                    h2 {{
                        margin-bottom: 20px;
                    }}
                    p {{
                        margin-bottom: 30px;
                    }}
                    .btn {{
                        padding: 12px 24px;
                        background-color: white;
                        border: 2px solid darkgreen;
                        border-radius: 8px;
                        color: darkgreen;
                        font-weight: bold;
                        text-decoration: none;
                        display: inline-block;
                        cursor: pointer;
                    }}
                    .btn:hover {{
                        background-color: darkgreen;
                        color: white;
                    }}
                </style>
            </head>
            <body>
                <a class="logo" href="https://amapazombies.com.br">
                    <img src="https://amapazombies.com.br/static/images/common/amapazombies.png" alt="Amapá Zombies">
                </a>
                <div class="container">
                    <h2>Senha redefinida com sucesso!</h2>
                    <p>Você será redirecionado automaticamente para a página inicial em 5 segundos.</p>
                    <a class="btn" href="https://amapazombies.com.br">Ir agora para página inicial</a>
                </div>
            </body>
            </html>
            """
        else:
            return "Usuário não encontrado.", 404
