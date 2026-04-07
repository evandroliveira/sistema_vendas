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
3. Ajuste a conexao com o banco em config.py.

Exemplo de configuracao:

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'sistema_vendas'
}
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
- templates/: paginas HTML da aplicacao.

## Observacoes

- O repositorio nao inclui o script SQL de criacao do banco.
- A exportacao para Excel depende do pacote openpyxl.
- As operacoes de venda assumem que existem registros de cliente, usuario, caixa e produto no banco.
