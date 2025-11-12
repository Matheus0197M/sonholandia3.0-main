import os, logging
from flask import Flask, render_template, session, redirect, url_for, request, flash
from authlib.integrations.flask_client import OAuth
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
# carrega .env
load_dotenv()

# --- força requests/urllib3 a usar bundle de CA do certifi (útil em dev) ---
import certifi
os.environ.setdefault('REQUESTS_CA_BUNDLE', certifi.where())
os.environ.setdefault('SSL_CERT_FILE', certifi.where())

# logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")

# debug info
logger.debug("GOOGLE_CLIENT_ID=%s", os.getenv("GOOGLE_CLIENT_ID"))
logger.debug("OAUTH_REDIRECT_URI=%s", os.getenv("OAUTH_REDIRECT_URI"))

# configura OAuth (OpenID Connect)
oauth = OAuth(app)
oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@app.route('/')
def index():
    user = session.get('user')
    return render_template('index.html', user=user)

@app.route("/login", methods=["GET", "POST"])  # rota de login que aceita GET e POST
def login():
    if request.method == "POST":  # se o formulário de login foi submetido
        user = request.form.get("user", "").strip()  # pega user enviado
        password = request.form.get("password", "").strip()  # pega password enviado

        if not user or not password:  # valida campos obrigatórios
            flash("Preencha todos os campos.", "warning")  # informa usuário
            return render_template("login.html")  # reexibe formulário

        with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:  # abre conexão com cursor que retorna dicts
            cur.execute("SELECT id_user, senha FROM usuarios WHERE user = %s", (user,))  # busca usuário pelo user
            user = cur.fetchone()  # pega a primeira linha (ou None)

        if user and user["senha"] == password:  # verifica se usuário existe e senha bate (comparação direta, sem hash)
            session["user_id"] = user["id_user"]  # guarda id do usuário na sessão
            session["user"] = user  # guarda user na sessão (útil pra exibir)
            flash(f"Bem-vindo, {user}!", "success")  # mensagem de boas-vindas
            return redirect(url_for("list_items"))  # redireciona para página de itens

        flash("Usuário ou senha inválidos.", "danger")  # mensagem caso login falhe

    return render_template("login.html")  # para GET, renderiza o template de login

@app.route('/loginWithGoogle')
def loginWithGoogle():
    try:
        redirect_uri = os.getenv("OAUTH_REDIRECT_URI")
        if not redirect_uri:
            raise RuntimeError("OAUTH_REDIRECT_URI não configurado no .env")
        return oauth.google.authorize_redirect(redirect_uri)
    except Exception:
        logger.exception("Erro ao iniciar o login com Google")
        return "Erro interno ao tentar logar (veja terminal).", 500

@app.route('/authGoogle')
def authGoogle(): 
    token = oauth.google.authorize_access_token()
    userinfo = oauth.google.parse_id_token(token)
    session['user'] = {
        'id': userinfo.get('sub'),
        'name': userinfo.get('name'),
        'email': userinfo.get('email'),
        'picture': userinfo.get('picture'),
    }
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
