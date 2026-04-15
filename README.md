# Sistema de Vendas

Aplicacao web em Flask com persistencia em MySQL/MariaDB para controle basico de clientes, produtos, vendas, estoque e relatorios.

## Funcionalidades

- Dashboard com total de clientes, quantidade de vendas, valor vendido e media por venda.
- Cadastro, listagem, edicao e exclusao de clientes.
- Cadastro, listagem, edicao e exclusao de produtos.
- Cadastro e edicao de vendas com controle de estoque.
- Relatorio de vendas com filtros por data, status, cliente, usuario e produto.
- Exportacao do relatorio de vendas em PDF e Excel.
- Tela de controle de estoque com destaque para itens abaixo do minimo.
- Interface web em Flask e menu de linha de comando em main.py.

## Requisitos

- Python 3.12 ou superior.
- MySQL ou MariaDB em execucao.
- Banco de dados sistema_vendas criado e com as tabelas esperadas pela aplicacao.

## Dependencias Python

Instale os pacotes abaixo no ambiente virtual:

```bash
pip install flask mysql-connector-python pandas reportlab openpyxl
```

## Configuracao

1. Crie e ative um ambiente virtual.
2. Instale as dependencias Python.
3. Ajuste as variaveis em config.py ou defina valores por ambiente.

Exemplo de configuracao:

```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '',
    'database': 'sistema_vendas'
}

APP_SECRET_KEY = 'troque-esta-chave-em-producao'

Variaveis opcionais suportadas:

- DB_HOST
- DB_PORT
- DB_USER
- DB_PASSWORD
- DB_NAME
- DB_TIMEOUT
- APP_SECRET_KEY
- FLASK_DEBUG
```

## Como executar

### Interface web

```bash
python app.py
```

Se estiver usando o workspace no VS Code, tambem existe a task Executar sistema Flask.

### Menu em linha de comando

```bash
python main.py
```

## Estrutura principal

- app.py: rotas Flask e regras da interface web.
- db.py: acesso ao banco e operacoes de negocio.
- config.py: configuracao do banco de dados.
- main.py: menu de linha de comando.
- static/css/app.css: tema visual compartilhado pela interface web.
- templates/: paginas HTML da aplicacao.

## Observacoes

- O repositorio nao inclui o script SQL de criacao do banco.
- A exportacao para Excel depende do pacote openpyxl.
- As operacoes de venda assumem que existem registros de cliente, usuario, caixa e produto no banco.
- A interface web foi centralizada em um layout base para reduzir duplicacao entre templates.
