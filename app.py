from flask import Flask, render_template, request, redirect, url_for
from db import listar_clientes, cadastrar_cliente, listar_produtos, cadastrar_produto

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/clientes')
def clientes():
    lista = listar_clientes()
    return render_template('clientes.html', clientes=lista)

@app.route('/clientes/cadastrar', methods=['GET', 'POST'])
def clientes_cadastrar():
    if request.method == 'POST':
        nome = request.form['nome']
        cpf_cnpj = request.form['cpf_cnpj']
        telefone = request.form['telefone']
        email = request.form['email']
        cadastrar_cliente(nome, cpf_cnpj, telefone, email)
        return redirect(url_for('clientes'))
    return render_template('clientes_cadastrar.html')

@app.route('/produtos')
def produtos():
    lista = listar_produtos()
    return render_template('produtos.html', produtos=lista)

@app.route('/produtos/cadastrar', methods=['GET', 'POST'])
def produtos_cadastrar():
    if request.method == 'POST':
        nome = request.form['nome']
        codigo_barras = request.form['codigo_barras']
        categoria_id = request.form['categoria_id']
        preco_custo = request.form['preco_custo']
        preco_venda = request.form['preco_venda']
        estoque_atual = request.form['estoque_atual']
        estoque_minimo = request.form['estoque_minimo']
        cadastrar_produto(nome, codigo_barras, int(categoria_id), float(preco_custo), float(preco_venda), int(estoque_atual), int(estoque_minimo))
        return redirect(url_for('produtos'))
    return render_template('produtos_cadastrar.html')

if __name__ == '__main__':
    app.run(debug=True)
