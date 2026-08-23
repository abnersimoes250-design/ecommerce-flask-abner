# Implantação no PythonAnywhere

Substitua `SEU_USUARIO` pelo nome de usuário criado no PythonAnywhere.

## 1. Enviar o código ao GitHub

No terminal do VS Code:

```bash
git add .
git commit -m "Finalizar projeto com login Bootstrap e deploy"
git push origin main
```

## 2. Criar a conta

1. Acesse https://www.pythonanywhere.com.
2. Clique em **Pricing & signup**.
3. Escolha a conta gratuita **Create a Beginner account**.
4. Preencha o nome de usuário, e-mail e senha.
5. Entre na conta.

## 3. Baixar o projeto

1. Abra **Consoles**.
2. Clique em **Bash**.
3. Execute:

```bash
git clone https://github.com/abnersimoes250-design/ecommerce-flask-abner.git
cd ecommerce-flask-abner
```

## 4. Criar o ambiente virtual

Na mesma tela Bash, execute:

```bash
mkvirtualenv --python=/usr/bin/python3.13 ecommerce-venv
pip install -r requirements.txt
```

## 5. Criar a aplicação Web

1. Abra a guia **Web**.
2. Clique em **Add a new web app**.
3. Avance em **Next**.
4. Escolha **Manual configuration**.
5. Selecione a mesma versão do Python usada no ambiente virtual.

## 6. Configurar o ambiente virtual

Na seção **Virtualenv**, informe:

```text
/home/SEU_USUARIO/.virtualenvs/ecommerce-venv
```

## 7. Configurar o arquivo WSGI

Abra o arquivo WSGI indicado na guia Web, apague o conteúdo e coloque:

```python
import os
import sys

path = "/home/SEU_USUARIO/ecommerce-flask-abner"
if path not in sys.path:
    sys.path.insert(0, path)

os.environ["SECRET_KEY"] = "troque-por-uma-chave-secreta"

from app import app as application
```

Troque `SEU_USUARIO`, salve o arquivo e volte para a guia **Web**.

## 8. Configurar os arquivos estáticos

Na seção **Static files**, cadastre:

```text
URL: /static/
Directory: /home/SEU_USUARIO/ecommerce-flask-abner/static
```

## 9. Publicar e testar

1. Clique no botão verde **Reload**.
2. Abra `https://SEU_USUARIO.pythonanywhere.com`.
3. Clique em **Criar conta**.
4. Cadastre um usuário e faça o login.
5. Teste o menu, os CRUDs, os relatórios e o botão **Sair**.

Quando houver atualização no GitHub, abra o Bash e execute:

```bash
cd ~/ecommerce-flask-abner
git pull origin main
workon ecommerce-venv
pip install -r requirements.txt
```

Depois clique novamente em **Reload** na guia Web.
