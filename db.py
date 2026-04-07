# Funções para itens da venda
def cadastrar_item_venda(venda_id, produto_id, quantidade, preco_unitario):
    db = Database()
    sql = '''INSERT INTO item_venda (venda_id, produto_id, quantidade, preco_unitario)
             VALUES (%s, %s, %s, %s)'''
    db.execute(sql, (venda_id, produto_id, quantidade, preco_unitario))
    db.close()

def atualizar_estoque(produto_id, quantidade):
    db = Database()
    sql = 'UPDATE produto SET estoque_atual = estoque_atual - %s WHERE id = %s AND estoque_atual >= %s'
    linhas_afetadas = db.execute(sql, (quantidade, produto_id, quantidade))
    db.close()
    if not linhas_afetadas:
        raise ValueError('Estoque insuficiente para concluir a operacao.')

def repor_estoque(produto_id, quantidade):
    db = Database()
    sql = 'UPDATE produto SET estoque_atual = estoque_atual + %s WHERE id = %s'
    db.execute(sql, (quantidade, produto_id))
    db.close()

def get_itens_venda(venda_id):
    db = Database()
    itens = db.query(
        '''
        SELECT iv.*, p.nome AS produto_nome
        FROM item_venda iv
        INNER JOIN produto p ON p.id = iv.produto_id
        WHERE iv.venda_id = %s
        ORDER BY iv.id
        ''',
        (venda_id,)
    )
    db.close()
    return itens
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
        return self.cursor.rowcount

    def close(self):
        self.cursor.close()
        self.conn.close()

# Funções de exemplo
# Buscar cliente por ID
def get_cliente(cliente_id):
    db = Database()
    cliente = db.query('SELECT * FROM cliente WHERE id=%s', (cliente_id,))
    db.close()
    return cliente[0] if cliente else None

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

# Função para editar cliente
def editar_cliente(id, nome, cpf_cnpj, telefone, email):
    db = Database()
    sql = 'UPDATE cliente SET nome=%s, cpf_cnpj=%s, telefone=%s, email=%s WHERE id=%s'
    db.execute(sql, (nome, cpf_cnpj, telefone, email, id))
    db.close()

# Função para excluir cliente
def excluir_cliente(id):
    db = Database()
    sql = 'DELETE FROM cliente WHERE id=%s'
    db.execute(sql, (id,))
    db.close()

# Funções para produtos
# Função para buscar produto por ID
def get_produto(id):
    db = Database()
    produto = db.query('SELECT * FROM produto WHERE id=%s', (id,))
    db.close()
    return produto[0] if produto else None

def listar_produtos():
    db = Database()
    produtos = db.query('SELECT * FROM produto')
    db.close()
    return produtos

# Função para editar produto
def editar_produto(id, nome, codigo_barras, categoria_id, preco_custo, preco_venda, estoque_atual, estoque_minimo):
    db = Database()
    sql = '''UPDATE produto SET nome=%s, codigo_barras=%s, categoria_id=%s, preco_custo=%s, preco_venda=%s, estoque_atual=%s, estoque_minimo=%s WHERE id=%s'''
    db.execute(sql, (nome, codigo_barras, categoria_id, preco_custo, preco_venda, estoque_atual, estoque_minimo, id))
    db.close()

# Função para excluir produto
def excluir_produto(id):
    db = Database()
    sql = 'DELETE FROM produto WHERE id=%s'
    db.execute(sql, (id,))
    db.close()

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
# Excluir venda por ID
def excluir_venda(venda_id):
    venda = get_venda(venda_id)
    itens_venda = get_itens_venda(venda_id)

    if venda and venda.get('status') == 'FINALIZADA':
        for item in itens_venda:
            repor_estoque(item['produto_id'], item['quantidade'])
            cadastrar_movimentacao(item['produto_id'], 'ENTRADA', item['quantidade'], f'Exclusao da venda {venda_id}')

    db = Database()
    db.execute('DELETE FROM item_venda WHERE venda_id=%s', (venda_id,))
    db.execute('DELETE FROM venda WHERE id=%s', (venda_id,))
    db.close()
# Editar venda por ID
def editar_venda(venda_id, cliente_id=None, usuario_id=None, caixa_id=None, total_bruto=None, desconto=None, total_liquido=None, status=None):
    db = Database()
    campos = []
    valores = []
    if cliente_id is not None:
        campos.append('cliente_id=%s')
        valores.append(cliente_id)
    if usuario_id is not None:
        campos.append('usuario_id=%s')
        valores.append(usuario_id)
    if caixa_id is not None:
        campos.append('caixa_id=%s')
        valores.append(caixa_id)
    if total_bruto is not None:
        campos.append('total_bruto=%s')
        valores.append(total_bruto)
    if desconto is not None:
        campos.append('desconto=%s')
        valores.append(desconto)
    if total_liquido is not None:
        campos.append('total_liquido=%s')
        valores.append(total_liquido)
    if status is not None:
        campos.append('status=%s')
        valores.append(status)
    if campos:
        sql = f"UPDATE venda SET {', '.join(campos)} WHERE id=%s"
        valores.append(venda_id)
        db.execute(sql, tuple(valores))
    db.close()
def listar_vendas():
    db = Database()
    vendas = db.query('''
        SELECT v.*, c.nome AS cliente_nome, u.nome AS usuario_nome
        FROM venda v
        INNER JOIN cliente c ON v.cliente_id = c.id
        INNER JOIN usuario u ON v.usuario_id = u.id
    ''')
    db.close()
    return vendas

# Buscar venda por ID
def get_venda(venda_id):
    db = Database()
    venda = db.query('SELECT * FROM venda WHERE id = %s', (venda_id,))
    db.close()
    return venda[0] if venda else None

def cadastrar_venda(cliente_id, usuario_id, caixa_id, total_bruto, desconto, total_liquido, status='FINALIZADA'):
    db = Database()
    sql = '''INSERT INTO venda (cliente_id, usuario_id, caixa_id, total_bruto, desconto, total_liquido, status)
             VALUES (%s, %s, %s, %s, %s, %s, %s)'''
    db.execute(sql, (cliente_id, usuario_id, caixa_id, total_bruto, desconto, total_liquido, status))
    venda_id = db.query('SELECT LAST_INSERT_ID() as id')[0]['id']
    db.close()
    return venda_id

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
