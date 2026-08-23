import os
import sqlite3
from datetime import date
from functools import wraps

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "mercado-ads-trilha-3")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["DATABASE"] = os.getenv(
    "DATABASE_PATH", os.path.join(app.instance_path, "ecommerce.db")
)


def conectar_banco():
    if "db" not in g:
        os.makedirs(app.instance_path, exist_ok=True)
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def fechar_banco(_=None):
    banco = g.pop("db", None)
    if banco is not None:
        banco.close()


def criar_banco():
    banco = conectar_banco()
    banco.executescript(
        """
        CREATE TABLE IF NOT EXISTS usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS categoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            descricao TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS anuncio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            preco REAL NOT NULL CHECK (preco >= 0),
            data_criacao TEXT NOT NULL,
            usuario_id INTEGER NOT NULL,
            categoria_id INTEGER NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE,
            FOREIGN KEY (categoria_id) REFERENCES categoria(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS pergunta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT NOT NULL,
            data TEXT NOT NULL,
            usuario_id INTEGER NOT NULL,
            anuncio_id INTEGER NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE,
            FOREIGN KEY (anuncio_id) REFERENCES anuncio(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS resposta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT NOT NULL,
            data TEXT NOT NULL,
            pergunta_id INTEGER NOT NULL UNIQUE,
            usuario_id INTEGER NOT NULL,
            FOREIGN KEY (pergunta_id) REFERENCES pergunta(id) ON DELETE CASCADE,
            FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS compra (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            quantidade INTEGER NOT NULL CHECK (quantidade > 0),
            valor_total REAL NOT NULL CHECK (valor_total >= 0),
            comprador_id INTEGER NOT NULL,
            anuncio_id INTEGER NOT NULL,
            FOREIGN KEY (comprador_id) REFERENCES usuario(id) ON DELETE CASCADE,
            FOREIGN KEY (anuncio_id) REFERENCES anuncio(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS favorito (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            usuario_id INTEGER NOT NULL,
            anuncio_id INTEGER NOT NULL,
            UNIQUE (usuario_id, anuncio_id),
            FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE,
            FOREIGN KEY (anuncio_id) REFERENCES anuncio(id) ON DELETE CASCADE
        );
        """
    )
    banco.commit()


@app.before_request
def carregar_usuario_logado():
    usuario_id = session.get("usuario_id")
    if usuario_id is None:
        g.usuario = None
    else:
        g.usuario = conectar_banco().execute(
            "SELECT id, nome, email FROM usuario WHERE id = ?", (usuario_id,)
        ).fetchone()


def login_obrigatorio(funcao):
    @wraps(funcao)
    def funcao_protegida(*args, **kwargs):
        if g.usuario is None:
            flash("Faça login para acessar esta página.", "aviso")
            return redirect(url_for("login"))
        return funcao(*args, **kwargs)

    return funcao_protegida


ENTIDADES = {
    "usuarios": {
        "titulo": "Usuários",
        "singular": "usuário",
        "tabela": "usuario",
        "lista_sql": "SELECT id, nome, email FROM usuario ORDER BY nome",
        "colunas": [("Nome", "nome"), ("E-mail", "email")],
        "descricao": "nome",
        "campos": [
            {"nome": "nome", "rotulo": "Nome", "tipo": "text"},
            {"nome": "email", "rotulo": "E-mail", "tipo": "email"},
            {"nome": "senha", "rotulo": "Senha", "tipo": "password", "especial": "senha"},
        ],
    },
    "categorias": {
        "titulo": "Categorias",
        "singular": "categoria",
        "tabela": "categoria",
        "lista_sql": "SELECT id, nome, descricao FROM categoria ORDER BY nome",
        "colunas": [("Nome", "nome"), ("Descrição", "descricao")],
        "descricao": "nome",
        "campos": [
            {"nome": "nome", "rotulo": "Nome", "tipo": "text"},
            {"nome": "descricao", "rotulo": "Descrição", "tipo": "textarea"},
        ],
    },
    "anuncios": {
        "titulo": "Anúncios",
        "singular": "anúncio",
        "tabela": "anuncio",
        "lista_sql": """
            SELECT a.id, a.titulo, printf('R$ %.2f', a.preco) AS preco,
                   u.nome AS proprietario, c.nome AS categoria
            FROM anuncio a
            JOIN usuario u ON u.id = a.usuario_id
            JOIN categoria c ON c.id = a.categoria_id
            ORDER BY a.titulo
        """,
        "colunas": [("Título", "titulo"), ("Preço", "preco"), ("Proprietário", "proprietario"), ("Categoria", "categoria")],
        "descricao": "titulo",
        "aviso": "Cadastre pelo menos um usuário e uma categoria antes de criar um anúncio.",
        "campos": [
            {"nome": "titulo", "rotulo": "Título", "tipo": "text"},
            {"nome": "descricao", "rotulo": "Descrição", "tipo": "textarea"},
            {"nome": "preco", "rotulo": "Preço", "tipo": "number", "passo": "0.01", "minimo": "0", "converter": float},
            {"nome": "data_criacao", "rotulo": "Data", "tipo": "date", "padrao": "hoje"},
            {"nome": "usuario_id", "rotulo": "Proprietário", "tipo": "select", "opcoes_sql": "SELECT id, nome FROM usuario ORDER BY nome", "converter": int},
            {"nome": "categoria_id", "rotulo": "Categoria", "tipo": "select", "opcoes_sql": "SELECT id, nome FROM categoria ORDER BY nome", "converter": int},
        ],
    },
    "perguntas": {
        "titulo": "Perguntas",
        "singular": "pergunta",
        "tabela": "pergunta",
        "lista_sql": """
            SELECT p.id, p.texto, u.nome AS usuario, a.titulo AS anuncio,
                   strftime('%d/%m/%Y', p.data) AS data
            FROM pergunta p
            JOIN usuario u ON u.id = p.usuario_id
            JOIN anuncio a ON a.id = p.anuncio_id
            ORDER BY p.id
        """,
        "colunas": [("Pergunta", "texto"), ("Usuário", "usuario"), ("Anúncio", "anuncio"), ("Data", "data")],
        "descricao": "texto",
        "campos": [
            {"nome": "texto", "rotulo": "Pergunta", "tipo": "textarea"},
            {"nome": "data", "rotulo": "Data", "tipo": "date", "padrao": "hoje"},
            {"nome": "usuario_id", "rotulo": "Usuário", "tipo": "select", "opcoes_sql": "SELECT id, nome FROM usuario ORDER BY nome", "converter": int},
            {"nome": "anuncio_id", "rotulo": "Anúncio", "tipo": "select", "opcoes_sql": "SELECT id, titulo AS nome FROM anuncio ORDER BY titulo", "converter": int},
        ],
    },
    "respostas": {
        "titulo": "Respostas",
        "singular": "resposta",
        "tabela": "resposta",
        "lista_sql": """
            SELECT r.id, r.texto, p.texto AS pergunta, u.nome AS usuario,
                   strftime('%d/%m/%Y', r.data) AS data
            FROM resposta r
            JOIN pergunta p ON p.id = r.pergunta_id
            JOIN usuario u ON u.id = r.usuario_id
            ORDER BY r.id
        """,
        "colunas": [("Resposta", "texto"), ("Pergunta", "pergunta"), ("Usuário", "usuario"), ("Data", "data")],
        "descricao": "texto",
        "aviso": "Cada pergunta pode possuir somente uma resposta.",
        "campos": [
            {"nome": "texto", "rotulo": "Resposta", "tipo": "textarea"},
            {"nome": "data", "rotulo": "Data", "tipo": "date", "padrao": "hoje"},
            {"nome": "pergunta_id", "rotulo": "Pergunta", "tipo": "select", "opcoes_sql": "SELECT id, substr(texto, 1, 70) AS nome FROM pergunta ORDER BY id", "converter": int},
            {"nome": "usuario_id", "rotulo": "Usuário que respondeu", "tipo": "select", "opcoes_sql": "SELECT id, nome FROM usuario ORDER BY nome", "converter": int},
        ],
    },
    "compras": {
        "titulo": "Compras",
        "singular": "compra",
        "tabela": "compra",
        "lista_sql": """
            SELECT c.id, strftime('%d/%m/%Y', c.data) AS data,
                   u.nome AS comprador, a.titulo AS anuncio, c.quantidade,
                   printf('R$ %.2f', c.valor_total) AS valor_total
            FROM compra c
            JOIN usuario u ON u.id = c.comprador_id
            JOIN anuncio a ON a.id = c.anuncio_id
            ORDER BY c.id
        """,
        "colunas": [("Data", "data"), ("Comprador", "comprador"), ("Anúncio", "anuncio"), ("Qtd.", "quantidade"), ("Total", "valor_total")],
        "descricao": "id",
        "campos": [
            {"nome": "data", "rotulo": "Data", "tipo": "date", "padrao": "hoje"},
            {"nome": "quantidade", "rotulo": "Quantidade", "tipo": "number", "padrao": 1, "passo": "1", "minimo": "1", "converter": int},
            {"nome": "valor_total", "rotulo": "Valor total", "tipo": "number", "passo": "0.01", "minimo": "0", "converter": float},
            {"nome": "comprador_id", "rotulo": "Comprador", "tipo": "select", "opcoes_sql": "SELECT id, nome FROM usuario ORDER BY nome", "converter": int},
            {"nome": "anuncio_id", "rotulo": "Anúncio", "tipo": "select", "opcoes_sql": "SELECT id, titulo AS nome FROM anuncio ORDER BY titulo", "converter": int},
        ],
    },
    "favoritos": {
        "titulo": "Favoritos",
        "singular": "favorito",
        "tabela": "favorito",
        "lista_sql": """
            SELECT f.id, strftime('%d/%m/%Y', f.data) AS data,
                   u.nome AS usuario, a.titulo AS anuncio
            FROM favorito f
            JOIN usuario u ON u.id = f.usuario_id
            JOIN anuncio a ON a.id = f.anuncio_id
            ORDER BY f.id
        """,
        "colunas": [("Data", "data"), ("Usuário", "usuario"), ("Anúncio", "anuncio")],
        "descricao": "id",
        "campos": [
            {"nome": "data", "rotulo": "Data", "tipo": "date", "padrao": "hoje"},
            {"nome": "usuario_id", "rotulo": "Usuário", "tipo": "select", "opcoes_sql": "SELECT id, nome FROM usuario ORDER BY nome", "converter": int},
            {"nome": "anuncio_id", "rotulo": "Anúncio", "tipo": "select", "opcoes_sql": "SELECT id, titulo AS nome FROM anuncio ORDER BY titulo", "converter": int},
        ],
    },
}


def obter_configuracao(entidade):
    if entidade not in ENTIDADES:
        return None
    return ENTIDADES[entidade]


def montar_campos(configuracao, registro=None, edicao=False):
    banco = conectar_banco()
    campos = []
    for definicao in configuracao["campos"]:
        item = definicao.copy()
        nome = item["nome"]
        if item.get("especial") == "senha":
            item["valor"] = ""
            item["required"] = not edicao
            if edicao:
                item["rotulo"] = "Senha (deixe vazio para manter)"
        elif registro is not None:
            item["valor"] = registro[nome]
            item["required"] = True
        else:
            item["valor"] = date.today().isoformat() if item.get("padrao") == "hoje" else item.get("padrao", "")
            item["required"] = True
        if "opcoes_sql" in item:
            item["opcoes"] = [(linha["id"], linha["nome"]) for linha in banco.execute(item["opcoes_sql"]).fetchall()]
        campos.append(item)
    return campos


def ler_formulario(configuracao, edicao=False):
    dados = {}
    for campo in configuracao["campos"]:
        nome = campo["nome"]
        valor = request.form.get(nome, "").strip()
        if campo.get("especial") == "senha":
            if edicao and not valor:
                continue
            valor = generate_password_hash(valor)
        elif campo.get("converter") and valor:
            valor = campo["converter"](valor)
        dados[nome] = valor
    return dados


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.usuario is not None:
        return redirect(url_for("inicio"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        usuario = conectar_banco().execute(
            "SELECT * FROM usuario WHERE lower(email) = ?", (email,)
        ).fetchone()

        if usuario is None or not check_password_hash(usuario["senha"], senha):
            flash("E-mail ou senha incorretos.", "erro")
        else:
            session.clear()
            session["usuario_id"] = usuario["id"]
            flash(f"Bem-vindo, {usuario['nome']}!", "sucesso")
            return redirect(url_for("inicio"))

    return render_template("login.html", titulo="Entrar")


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if g.usuario is not None:
        return redirect(url_for("inicio"))

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        if not nome or not email or not senha:
            flash("Preencha todos os campos.", "erro")
        elif len(senha) < 6:
            flash("A senha deve possuir pelo menos 6 caracteres.", "erro")
        else:
            banco = conectar_banco()
            try:
                banco.execute(
                    "INSERT INTO usuario (nome, email, senha) VALUES (?, ?, ?)",
                    (nome, email, generate_password_hash(senha)),
                )
                banco.commit()
                flash("Conta criada com sucesso. Agora faça o login.", "sucesso")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                banco.rollback()
                flash("Este e-mail já está cadastrado.", "erro")

    return render_template("cadastro.html", titulo="Criar conta")


@app.route("/logout")
@login_obrigatorio
def logout():
    session.clear()
    flash("Você saiu do sistema.", "sucesso")
    return redirect(url_for("login"))


@app.route("/")
@login_obrigatorio
def inicio():
    banco = conectar_banco()
    contagens = {
        "usuarios": banco.execute("SELECT COUNT(*) FROM usuario").fetchone()[0],
        "categorias": banco.execute("SELECT COUNT(*) FROM categoria").fetchone()[0],
        "anuncios": banco.execute("SELECT COUNT(*) FROM anuncio").fetchone()[0],
        "compras": banco.execute("SELECT COUNT(*) FROM compra").fetchone()[0],
    }
    return render_template("index.html", contagens=contagens)


@app.route("/<entidade>")
@login_obrigatorio
def listar(entidade):
    configuracao = obter_configuracao(entidade)
    if not configuracao:
        return "Entidade não encontrada", 404
    registros = [
        dict(linha)
        for linha in conectar_banco().execute(configuracao["lista_sql"]).fetchall()
    ]
    return render_template("lista.html", titulo=configuracao["titulo"], entidade=entidade,
                           registros=registros, colunas=configuracao["colunas"])


@app.route("/<entidade>/novo", methods=["GET", "POST"])
@login_obrigatorio
def novo(entidade):
    configuracao = obter_configuracao(entidade)
    if not configuracao:
        return "Entidade não encontrada", 404
    if request.method == "POST":
        banco = conectar_banco()
        try:
            dados = ler_formulario(configuracao)
            colunas = ", ".join(dados.keys())
            marcadores = ", ".join("?" for _ in dados)
            banco.execute(f"INSERT INTO {configuracao['tabela']} ({colunas}) VALUES ({marcadores})", tuple(dados.values()))
            banco.commit()
            flash(f"{configuracao['singular'].capitalize()} cadastrado com sucesso.", "sucesso")
            return redirect(url_for("listar", entidade=entidade))
        except (sqlite3.IntegrityError, ValueError):
            banco.rollback()
            flash("Não foi possível salvar. Verifique os dados e tente novamente.", "erro")
    return render_template("formulario.html", titulo=f"Novo {configuracao['singular']}",
                           entidade=entidade, campos=montar_campos(configuracao),
                           aviso=configuracao.get("aviso"))


@app.route("/<entidade>/<int:id>/editar", methods=["GET", "POST"])
@login_obrigatorio
def editar(entidade, id):
    configuracao = obter_configuracao(entidade)
    if not configuracao:
        return "Entidade não encontrada", 404
    banco = conectar_banco()
    registro = banco.execute(f"SELECT * FROM {configuracao['tabela']} WHERE id = ?", (id,)).fetchone()
    if registro is None:
        return "Registro não encontrado", 404
    if request.method == "POST":
        try:
            dados = ler_formulario(configuracao, edicao=True)
            atribuicoes = ", ".join(f"{nome} = ?" for nome in dados)
            banco.execute(f"UPDATE {configuracao['tabela']} SET {atribuicoes} WHERE id = ?", (*dados.values(), id))
            banco.commit()
            flash(f"{configuracao['singular'].capitalize()} atualizado com sucesso.", "sucesso")
            return redirect(url_for("listar", entidade=entidade))
        except (sqlite3.IntegrityError, ValueError):
            banco.rollback()
            flash("Não foi possível atualizar. Verifique os dados e tente novamente.", "erro")
    return render_template("formulario.html", titulo=f"Editar {configuracao['singular']}",
                           entidade=entidade, campos=montar_campos(configuracao, registro, edicao=True),
                           aviso=configuracao.get("aviso"))


@app.route("/<entidade>/<int:id>/excluir", methods=["GET", "POST"])
@login_obrigatorio
def excluir(entidade, id):
    configuracao = obter_configuracao(entidade)
    if not configuracao:
        return "Entidade não encontrada", 404
    banco = conectar_banco()
    registro = banco.execute(f"SELECT * FROM {configuracao['tabela']} WHERE id = ?", (id,)).fetchone()
    if registro is None:
        return "Registro não encontrado", 404
    if request.method == "POST":
        banco.execute(f"DELETE FROM {configuracao['tabela']} WHERE id = ?", (id,))
        banco.commit()
        flash(f"{configuracao['singular'].capitalize()} excluído com sucesso.", "sucesso")
        return redirect(url_for("listar", entidade=entidade))
    descricao = registro[configuracao["descricao"]]
    if entidade in ("compras", "favoritos"):
        descricao = f"Registro #{registro['id']}"
    return render_template("confirmar_exclusao.html", titulo=f"Excluir {configuracao['singular']}",
                           entidade=entidade, descricao=descricao)


def consultar_relatorio():
    with conectar_banco() as banco:
        registros = banco.execute(
            """
            SELECT c.data, c.quantidade, c.valor_total, comprador.nome AS comprador,
                   vendedor.nome AS vendedor, a.titulo AS anuncio
            FROM compra c
            JOIN usuario comprador ON comprador.id = c.comprador_id
            JOIN anuncio a ON a.id = c.anuncio_id
            JOIN usuario vendedor ON vendedor.id = a.usuario_id
            ORDER BY c.data
            """
        ).fetchall()
    return [dict(registro) for registro in registros]


@app.route("/relatorios/compras")
@login_obrigatorio
def relatorio_compras():
    return render_template("relatorio.html", titulo="Relatório de compras", registros=consultar_relatorio())


@app.route("/relatorios/vendas")
@login_obrigatorio
def relatorio_vendas():
    return render_template("relatorio.html", titulo="Relatório de vendas", registros=consultar_relatorio())


with app.app_context():
    criar_banco()


if __name__ == "__main__":
    app.run(debug=True)
