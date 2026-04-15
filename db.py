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

    def query_one(self, sql, params=None):
        self.cursor.execute(sql, params or ())
        return self.cursor.fetchone()

    def execute(self, sql, params=None):
        try:
            self.cursor.execute(sql, params or ())
            self.conn.commit()
            return self.cursor.rowcount
        except Exception:
            self.conn.rollback()
            raise

    def insert(self, sql, params=None):
        try:
            self.cursor.execute(sql, params or ())
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception:
            self.conn.rollback()
            raise

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn and self.conn.is_connected():
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

# Funções de exemplo
# Buscar cliente por ID
def get_cliente(cliente_id):
    with Database() as db:
        return db.query_one('SELECT * FROM cliente WHERE id=%s', (cliente_id,))

def listar_clientes():
    with Database() as db:
        return db.query('SELECT * FROM cliente ORDER BY nome')


def cadastrar_cliente(nome, cpf_cnpj, telefone, email):
    with Database() as db:
        sql = 'INSERT INTO cliente (nome, cpf_cnpj, telefone, email) VALUES (%s, %s, %s, %s)'
        db.execute(sql, (nome, cpf_cnpj, telefone, email))

# Função para editar cliente
def editar_cliente(id, nome, cpf_cnpj, telefone, email):
    with Database() as db:
        sql = 'UPDATE cliente SET nome=%s, cpf_cnpj=%s, telefone=%s, email=%s WHERE id=%s'
        db.execute(sql, (nome, cpf_cnpj, telefone, email, id))

# Função para excluir cliente
def excluir_cliente(id):
    with Database() as db:
        sql = 'DELETE FROM cliente WHERE id=%s'
        db.execute(sql, (id,))

# Funções para produtos
# Função para buscar produto por ID
def get_produto(id):
    with Database() as db:
        return db.query_one(
            '''
            SELECT p.*, c.nome AS categoria_nome
            FROM produto p
            LEFT JOIN categoria c ON c.id = p.categoria_id
            WHERE p.id=%s
            ''',
            (id,)
        )

def listar_produtos():
    with Database() as db:
        return db.query(
            '''
            SELECT p.*, c.nome AS categoria_nome
            FROM produto p
            LEFT JOIN categoria c ON c.id = p.categoria_id
            ORDER BY p.nome
            '''
        )

# Função para editar produto
def editar_produto(id, nome, codigo_barras, categoria_id, preco_custo, preco_venda, estoque_atual, estoque_minimo, imagem=None):
    with Database() as db:
        sql = '''UPDATE produto SET nome=%s, codigo_barras=%s, categoria_id=%s, preco_custo=%s, preco_venda=%s, estoque_atual=%s, estoque_minimo=%s, imagem=%s WHERE id=%s'''
        db.execute(sql, (nome, codigo_barras, categoria_id, preco_custo, preco_venda, estoque_atual, estoque_minimo, imagem, id))

# Função para excluir produto
def excluir_produto(id):
    with Database() as db:
        sql = 'DELETE FROM produto WHERE id=%s'
        db.execute(sql, (id,))

def cadastrar_produto(nome, codigo_barras, categoria_id, preco_custo, preco_venda, estoque_atual, estoque_minimo, imagem=None, ativo=1):
    with Database() as db:
        sql = '''INSERT INTO produto (nome, codigo_barras, categoria_id, preco_custo, preco_venda, estoque_atual, estoque_minimo, imagem, ativo)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'''
        db.execute(sql, (nome, codigo_barras, categoria_id, preco_custo, preco_venda, estoque_atual, estoque_minimo, imagem, ativo))

# Funções para categorias
def listar_categorias():
    with Database() as db:
        return db.query('SELECT * FROM categoria ORDER BY nome')

def cadastrar_categoria(nome, ativo=1):
    with Database() as db:
        sql = 'INSERT INTO categoria (nome, ativo) VALUES (%s, %s)'
        db.execute(sql, (nome, ativo))

# Funções para usuários
def listar_usuarios():
    with Database() as db:
        return db.query('SELECT * FROM usuario ORDER BY nome')

def cadastrar_usuario(nome, email, senha, perfil_id, ativo=1):
    with Database() as db:
        sql = 'INSERT INTO usuario (nome, email, senha, perfil_id, ativo) VALUES (%s, %s, %s, %s, %s)'
        db.execute(sql, (nome, email, senha, perfil_id, ativo))

# Funções para vendas
# Excluir venda por ID
def excluir_venda(venda_id):
    venda = get_venda(venda_id)
    itens_venda = get_itens_venda(venda_id)

    if venda and venda.get('status') == 'FINALIZADA':
        for item in itens_venda:
            repor_estoque(item['produto_id'], item['quantidade'])
            cadastrar_movimentacao(item['produto_id'], 'ENTRADA', item['quantidade'], f'Exclusao da venda {venda_id}')

    with Database() as db:
        db.execute('DELETE FROM item_venda WHERE venda_id=%s', (venda_id,))
        db.execute('DELETE FROM venda WHERE id=%s', (venda_id,))
# Editar venda por ID
def editar_venda(venda_id, cliente_id=None, usuario_id=None, caixa_id=None, total_bruto=None, desconto=None, total_liquido=None, status=None):
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
        with Database() as db:
            sql = f"UPDATE venda SET {', '.join(campos)} WHERE id=%s"
            valores.append(venda_id)
            db.execute(sql, tuple(valores))

def listar_vendas():
    with Database() as db:
        return db.query('''
            SELECT v.*, c.nome AS cliente_nome, u.nome AS usuario_nome
            FROM venda v
            INNER JOIN cliente c ON v.cliente_id = c.id
            INNER JOIN usuario u ON v.usuario_id = u.id
            ORDER BY v.data_venda DESC, v.id DESC
        ''')

# Buscar venda por ID
def get_venda(venda_id):
    with Database() as db:
        return db.query_one('SELECT * FROM venda WHERE id = %s', (venda_id,))

def cadastrar_venda(cliente_id, usuario_id, caixa_id, total_bruto, desconto, total_liquido, status='FINALIZADA'):
    with Database() as db:
        sql = '''INSERT INTO venda (cliente_id, usuario_id, caixa_id, total_bruto, desconto, total_liquido, status)
                 VALUES (%s, %s, %s, %s, %s, %s, %s)'''
        return db.insert(sql, (cliente_id, usuario_id, caixa_id, total_bruto, desconto, total_liquido, status))

# Funções para movimentação de estoque
def listar_movimentacoes():
    with Database() as db:
        return db.query('SELECT * FROM movimentacao_estoque ORDER BY id DESC')

def cadastrar_movimentacao(produto_id, tipo, quantidade, referencia=None):
    with Database() as db:
        sql = '''INSERT INTO movimentacao_estoque (produto_id, tipo, quantidade, referencia)
                 VALUES (%s, %s, %s, %s)'''
        db.execute(sql, (produto_id, tipo, quantidade, referencia))

# Funções para caixa
def listar_caixas():
    with Database() as db:
        return db.query('SELECT * FROM caixa ORDER BY id DESC')

def abrir_caixa(usuario_id, valor_inicial):
    with Database() as db:
        sql = '''INSERT INTO caixa (usuario_id, valor_inicial, status) VALUES (%s, %s, 'ABERTO')'''
        db.execute(sql, (usuario_id, valor_inicial))

def fechar_caixa(caixa_id, valor_final):
    with Database() as db:
        sql = '''UPDATE caixa SET valor_final=%s, data_fechamento=NOW(), status='FECHADO' WHERE id=%s'''
        db.execute(sql, (valor_final, caixa_id))
