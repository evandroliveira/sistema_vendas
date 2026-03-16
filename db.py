# db.py
import mysql.connector
from config import DB_CONFIG

class Database:
    def __init__(self):
        self.conn = mysql.connector.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor(dictionary=True)

    def query(self, sql, params=None):
        self.cursor.execute(sql, params or ())
        return self.cursor.fetchall()

    def execute(self, sql, params=None):
        self.cursor.execute(sql, params or ())
        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()

# Funções de exemplo

def listar_clientes():
    db = Database()
    clientes = db.query('SELECT * FROM cliente')
    db.close()
    return clientes

def cadastrar_cliente(nome, cpf_cnpj, telefone, email):
    db = Database()
    sql = 'INSERT INTO cliente (nome, cpf_cnpj, telefone, email) VALUES (%s, %s, %s, %s)'
    db.execute(sql, (nome, cpf_cnpj, telefone, email))
    db.close()

# Funções para produtos
def listar_produtos():
    db = Database()
    produtos = db.query('SELECT * FROM produto')
    db.close()
    return produtos

def cadastrar_produto(nome, codigo_barras, categoria_id, preco_custo, preco_venda, estoque_atual, estoque_minimo, ativo=1):
    db = Database()
    sql = '''INSERT INTO produto (nome, codigo_barras, categoria_id, preco_custo, preco_venda, estoque_atual, estoque_minimo, ativo)
             VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'''
    db.execute(sql, (nome, codigo_barras, categoria_id, preco_custo, preco_venda, estoque_atual, estoque_minimo, ativo))
    db.close()

# Funções para categorias
def listar_categorias():
    db = Database()
    categorias = db.query('SELECT * FROM categoria')
    db.close()
    return categorias

def cadastrar_categoria(nome, ativo=1):
    db = Database()
    sql = 'INSERT INTO categoria (nome, ativo) VALUES (%s, %s)'
    db.execute(sql, (nome, ativo))
    db.close()

# Funções para usuários
def listar_usuarios():
    db = Database()
    usuarios = db.query('SELECT * FROM usuario')
    db.close()
    return usuarios

def cadastrar_usuario(nome, email, senha, perfil_id, ativo=1):
    db = Database()
    sql = 'INSERT INTO usuario (nome, email, senha, perfil_id, ativo) VALUES (%s, %s, %s, %s, %s)'
    db.execute(sql, (nome, email, senha, perfil_id, ativo))
    db.close()

# Funções para vendas
def listar_vendas():
    db = Database()
    vendas = db.query('SELECT * FROM venda')
    db.close()
    return vendas

def cadastrar_venda(cliente_id, usuario_id, caixa_id, total_bruto, desconto, total_liquido, status='FINALIZADA'):
    db = Database()
    sql = '''INSERT INTO venda (cliente_id, usuario_id, caixa_id, total_bruto, desconto, total_liquido, status)
             VALUES (%s, %s, %s, %s, %s, %s, %s)'''
    db.execute(sql, (cliente_id, usuario_id, caixa_id, total_bruto, desconto, total_liquido, status))
    db.close()

# Funções para movimentação de estoque
def listar_movimentacoes():
    db = Database()
    movs = db.query('SELECT * FROM movimentacao_estoque')
    db.close()
    return movs

def cadastrar_movimentacao(produto_id, tipo, quantidade, referencia=None):
    db = Database()
    sql = '''INSERT INTO movimentacao_estoque (produto_id, tipo, quantidade, referencia)
             VALUES (%s, %s, %s, %s)'''
    db.execute(sql, (produto_id, tipo, quantidade, referencia))
    db.close()

# Funções para caixa
def listar_caixas():
    db = Database()
    caixas = db.query('SELECT * FROM caixa')
    db.close()
    return caixas

def abrir_caixa(usuario_id, valor_inicial):
    db = Database()
    sql = '''INSERT INTO caixa (usuario_id, valor_inicial, status) VALUES (%s, %s, 'ABERTO')'''
    db.execute(sql, (usuario_id, valor_inicial))
    db.close()

def fechar_caixa(caixa_id, valor_final):
    db = Database()
    sql = '''UPDATE caixa SET valor_final=%s, data_fechamento=NOW(), status='FECHADO' WHERE id=%s'''
    db.execute(sql, (valor_final, caixa_id))
    db.close()
