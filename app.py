from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/usuarios")
def usuarios():
    return render_template("pagina.html", titulo="Usuários", descricao="Cadastro e consulta dos usuários da plataforma.")


@app.route("/categorias")
def categorias():
    return render_template("pagina.html", titulo="Categorias", descricao="Organização dos anúncios por categoria.")


@app.route("/anuncios")
def anuncios():
    return render_template("pagina.html", titulo="Anúncios", descricao="Produtos anunciados pelos usuários.")


@app.route("/perguntas")
def perguntas():
    return render_template("pagina.html", titulo="Perguntas e Respostas", descricao="Perguntas feitas nos anúncios e respostas dadas pelos vendedores.")


@app.route("/compras")
def compras():
    return render_template("pagina.html", titulo="Compras", descricao="Compras realizadas diretamente em um anúncio, sem carrinho.")


@app.route("/favoritos")
def favoritos():
    return render_template("pagina.html", titulo="Favoritos", descricao="Lista de anúncios favoritos de cada usuário.")


@app.route("/relatorios/vendas")
def relatorio_vendas():
    return render_template("pagina.html", titulo="Relatório de Vendas", descricao="Consulta das vendas dos anúncios pertencentes ao usuário.")


@app.route("/relatorios/compras")
def relatorio_compras():
    return render_template("pagina.html", titulo="Relatório de Compras", descricao="Consulta das compras realizadas pelo usuário.")


if __name__ == "__main__":
    app.run(debug=True)
