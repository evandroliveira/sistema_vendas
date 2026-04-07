from flask import Flask, render_template, request, redirect, url_for, send_file
from db import listar_clientes, cadastrar_cliente, listar_produtos, cadastrar_produto
from db import listar_vendas, cadastrar_venda, listar_usuarios, listar_caixas, get_cliente
from db import cadastrar_item_venda, atualizar_estoque, cadastrar_movimentacao, repor_estoque, get_itens_venda
from db import get_produto, editar_cliente, excluir_cliente, editar_produto, excluir_produto, get_venda, editar_venda, excluir_venda
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io
from urllib.parse import urlencode

app = Flask(__name__)


def normalizar_venda(venda):
    venda_normalizada = dict(venda)
    data_venda = venda_normalizada.get('data_venda')

    if hasattr(data_venda, 'strftime'):
        venda_normalizada['data_venda'] = data_venda.strftime('%Y-%m-%d %H:%M:%S')
    elif data_venda is None:
        venda_normalizada['data_venda'] = ''
    else:
        venda_normalizada['data_venda'] = str(data_venda)

    for campo in ('total_bruto', 'desconto', 'total_liquido'):
        valor = venda_normalizada.get(campo)
        venda_normalizada[campo] = float(valor) if valor is not None else 0.0

    return venda_normalizada


def obter_filtros_relatorio_vendas():
    return {
        'data_ini': request.args.get('data_ini', '').strip(),
        'data_fim': request.args.get('data_fim', '').strip(),
        'status': request.args.get('status', '').strip(),
        'cliente_id': request.args.get('cliente_id', '').strip(),
        'usuario_id': request.args.get('usuario_id', '').strip(),
        'produto_id': request.args.get('produto_id', '').strip(),
    }


def listar_vendas_filtradas(filtros):
    vendas = [normalizar_venda(venda) for venda in listar_vendas()]

    if filtros['data_ini']:
        vendas = [venda for venda in vendas if venda.get('data_venda') and venda['data_venda'][:10] >= filtros['data_ini']]
    if filtros['data_fim']:
        vendas = [venda for venda in vendas if venda.get('data_venda') and venda['data_venda'][:10] <= filtros['data_fim']]
    if filtros['status']:
        vendas = [venda for venda in vendas if venda.get('status') == filtros['status']]
    if filtros['cliente_id']:
        vendas = [venda for venda in vendas if str(venda.get('cliente_id')) == filtros['cliente_id']]
    if filtros['usuario_id']:
        vendas = [venda for venda in vendas if str(venda.get('usuario_id')) == filtros['usuario_id']]
    if filtros['produto_id']:
        produto_id = filtros['produto_id']
        vendas = [
            venda for venda in vendas
            if any(str(item.get('produto_id')) == produto_id for item in get_itens_venda(venda['id']))
        ]

    return vendas


def montar_contexto_relatorio_vendas():
    filtros = obter_filtros_relatorio_vendas()
    contexto = {
        'clientes': listar_clientes(),
        'usuarios': listar_usuarios(),
        'produtos': listar_produtos(),
        'vendas': listar_vendas_filtradas(filtros),
        'query_string': urlencode({chave: valor for chave, valor in filtros.items() if valor}),
    }
    contexto.update(filtros)
    return contexto

@app.route('/relatorio/vendas/export/pdf')
def relatorio_vendas_export_pdf():
    vendas = montar_contexto_relatorio_vendas()['vendas']

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    height = A4[1]
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "Relatório de Vendas")
    p.setFont("Helvetica", 10)
    y = height - 80
    p.drawString(50, y, "ID")
    p.drawString(100, y, "Cliente")
    p.drawString(250, y, "Data")
    p.drawString(350, y, "Total Líquido")
    p.drawString(450, y, "Status")
    y -= 20
    for v in vendas:
        if y < 50:
            p.showPage()
            y = height - 50
        p.drawString(50, y, str(v.get('id', '')))
        p.drawString(100, y, str(v.get('cliente_nome', v.get('cliente_id', ''))))
        p.drawString(250, y, str(v.get('data_venda', '')))
        p.drawString(350, y, str(v.get('total_liquido', '')))
        p.drawString(450, y, str(v.get('status', '')))
        y -= 18
    p.save()
    buffer.seek(0)
    return send_file(buffer, download_name='relatorio_vendas.pdf', as_attachment=True, mimetype='application/pdf')

@app.route('/relatorio/vendas/export/excel')
def relatorio_vendas_export_excel():
    vendas = montar_contexto_relatorio_vendas()['vendas']
    df = pd.DataFrame(vendas)
    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, download_name='relatorio_vendas.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/relatorio/vendas')
def relatorio_vendas():
    return render_template('relatorio_vendas.html', **montar_contexto_relatorio_vendas())

@app.route('/vendas/editar/<int:id>', methods=['GET', 'POST'])
def vendas_editar(id):
    venda = get_venda(id)
    if not venda:
        return redirect(url_for('vendas'))

    itens_venda = get_itens_venda(id)
    clientes = listar_clientes()
    produtos = listar_produtos()
    usuarios = listar_usuarios()
    caixas = listar_caixas()

    if request.method == 'POST':
        cliente_id = int(request.form['cliente_id'])
        usuario_id = int(request.form['usuario_id'])
        caixa_id = int(request.form['caixa_id'])
        total_bruto = float(request.form['total_bruto'])
        desconto = float(request.form.get('desconto') or 0)
        total_liquido = float(request.form['total_liquido'])
        status = request.form['status']

        if venda.get('status') != status:
            if status == 'CANCELADA' and venda.get('status') == 'FINALIZADA':
                for item in itens_venda:
                    repor_estoque(item['produto_id'], item['quantidade'])
                    cadastrar_movimentacao(item['produto_id'], 'ENTRADA', item['quantidade'], f'Cancelamento da venda {id}')

            if status == 'FINALIZADA' and venda.get('status') != 'FINALIZADA':
                itens_processados = []
                try:
                    for item in itens_venda:
                        atualizar_estoque(item['produto_id'], item['quantidade'])
                        cadastrar_movimentacao(item['produto_id'], 'SAIDA', item['quantidade'], f'Reativacao da venda {id}')
                        itens_processados.append(item)
                except ValueError as exc:
                    for item in itens_processados:
                        repor_estoque(item['produto_id'], item['quantidade'])
                        cadastrar_movimentacao(item['produto_id'], 'ENTRADA', item['quantidade'], f'Estorno da reativacao da venda {id}')
                    return render_template(
                        'vendas_editar.html',
                        venda=venda,
                        itens_venda=itens_venda,
                        clientes=clientes,
                        produtos=produtos,
                        usuarios=usuarios,
                        caixas=caixas,
                        erro=str(exc),
                    )

        venda.update(
            {
                'cliente_id': cliente_id,
                'usuario_id': usuario_id,
                'caixa_id': caixa_id,
                'total_bruto': total_bruto,
                'desconto': desconto,
                'total_liquido': total_liquido,
                'status': status,
            }
        )
        editar_venda(id, cliente_id, usuario_id, caixa_id, total_bruto, desconto, total_liquido, status)
        return redirect(url_for('vendas'))

    return render_template(
        'vendas_editar.html',
        venda=venda,
        itens_venda=itens_venda,
        clientes=clientes,
        produtos=produtos,
        usuarios=usuarios,
        caixas=caixas,
    )

@app.route('/vendas/excluir/<int:id>')
def vendas_excluir(id):
    excluir_venda(id)
    return redirect(url_for('vendas'))

@app.route('/vendas')
def vendas():
    lista = listar_vendas()
    return render_template('vendas.html', vendas=lista)

@app.route('/vendas/cadastrar', methods=['GET', 'POST'])
def vendas_cadastrar():
    clientes = listar_clientes()
    produtos = listar_produtos()
    usuarios = listar_usuarios()
    caixas = listar_caixas()

    if request.method == 'POST':
        cliente_id = int(request.form['cliente_id'])
        usuario_id = int(request.form['usuario_id'])
        caixa_id = int(request.form['caixa_id'])
        desconto = float(request.form.get('desconto') or 0)
        status = request.form['status']
        produtos_por_id = {int(produto['id']): produto for produto in produtos}
        itens_venda = []

        for produto_id_raw in request.form.getlist('produtos'):
            produto_id = int(produto_id_raw)
            produto = produtos_por_id.get(produto_id)
            quantidade_raw = (request.form.get(f'quantidade_{produto_id}') or '').strip()

            if not produto:
                continue

            if not quantidade_raw.isdigit() or int(quantidade_raw) <= 0:
                return render_template(
                    'vendas_cadastrar.html',
                    clientes=clientes,
                    produtos=produtos,
                    usuarios=usuarios,
                    caixas=caixas,
                    erro='Informe uma quantidade valida para cada produto selecionado.',
                )

            quantidade = int(quantidade_raw)
            estoque_atual = int(produto.get('estoque_atual') or 0)

            if quantidade > estoque_atual:
                return render_template(
                    'vendas_cadastrar.html',
                    clientes=clientes,
                    produtos=produtos,
                    usuarios=usuarios,
                    caixas=caixas,
                    erro=f'Estoque insuficiente para o produto {produto["nome"]}. Disponivel: {estoque_atual}.',
                )

            itens_venda.append(
                {
                    'produto_id': produto_id,
                    'nome': produto['nome'],
                    'quantidade': quantidade,
                    'preco_unitario': float(produto.get('preco_venda') or 0),
                }
            )

        if not itens_venda:
            return render_template(
                'vendas_cadastrar.html',
                clientes=clientes,
                produtos=produtos,
                usuarios=usuarios,
                caixas=caixas,
                erro='Selecione pelo menos um produto para registrar a venda.',
            )

        total_bruto = sum(item['quantidade'] * item['preco_unitario'] for item in itens_venda)
        total_liquido_calculado = max(total_bruto - desconto, 0)
        venda_id = cadastrar_venda(cliente_id, usuario_id, caixa_id, total_bruto, desconto, total_liquido_calculado, status)

        try:
            for item in itens_venda:
                if status == 'FINALIZADA':
                    atualizar_estoque(item['produto_id'], item['quantidade'])
                cadastrar_item_venda(venda_id, item['produto_id'], item['quantidade'], item['preco_unitario'])
                if status == 'FINALIZADA':
                    cadastrar_movimentacao(item['produto_id'], 'SAIDA', item['quantidade'], f'Venda {venda_id}')
        except ValueError as exc:
            excluir_venda(venda_id)
            return render_template(
                'vendas_cadastrar.html',
                clientes=clientes,
                produtos=listar_produtos(),
                usuarios=usuarios,
                caixas=caixas,
                erro=str(exc),
            )

        return redirect(url_for('vendas'))

    return render_template('vendas_cadastrar.html', clientes=clientes, produtos=produtos, usuarios=usuarios, caixas=caixas)

@app.route('/')
def index():
    clientes = listar_clientes()
    vendas = listar_vendas()
    total_clientes = len(clientes)
    total_vendas = len(vendas)
    valor_total_vendas = sum(float(v.get('total_liquido', 0) or 0) for v in vendas)
    media_vendas = valor_total_vendas / total_vendas if total_vendas else 0
    return render_template(
        'index.html',
        total_clientes=total_clientes,
        total_vendas=total_vendas,
        valor_total_vendas=valor_total_vendas,
        media_vendas=media_vendas,
    )

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

@app.route('/clientes/editar/<int:id>', methods=['GET', 'POST'])
def clientes_editar(id):
    cliente = get_cliente(id)
    if not cliente:
        return redirect(url_for('clientes'))
    if request.method == 'POST':
        nome = request.form['nome']
        cpf_cnpj = request.form['cpf_cnpj']
        telefone = request.form['telefone']
        email = request.form['email']
        editar_cliente(id, nome, cpf_cnpj, telefone, email)
        return redirect(url_for('clientes'))
    return render_template('clientes_editar.html', cliente=cliente)

@app.route('/clientes/excluir/<int:id>')
def clientes_excluir(id):
    excluir_cliente(id)
    return redirect(url_for('clientes'))

@app.route('/produtos/editar/<int:id>', methods=['GET', 'POST'])
def produtos_editar(id):
    produto = get_produto(id)
    if not produto:
        return redirect(url_for('produtos'))
    if request.method == 'POST':
        nome = request.form['nome']
        codigo_barras = request.form['codigo_barras']
        categoria_id = request.form['categoria_id']
        preco_custo = request.form['preco_custo']
        preco_venda = request.form['preco_venda']
        estoque_atual = request.form['estoque_atual']
        estoque_minimo = request.form['estoque_minimo']
        editar_produto(id, nome, codigo_barras, int(categoria_id), float(preco_custo), float(preco_venda), int(estoque_atual), int(estoque_minimo))
        return redirect(url_for('produtos'))
    return render_template('produtos_editar.html', produto=produto)

@app.route('/produtos/excluir/<int:id>')
def produtos_excluir(id):
    excluir_produto(id)
    return redirect(url_for('produtos'))

@app.route('/controle-estoque')
@app.route('/relatorio/estoque')
def controle_estoque():
    produtos = listar_produtos()
    for produto in produtos:
        estoque_atual = produto.get('estoque_atual') or 0
        estoque_minimo = produto.get('estoque_minimo') or 0
        produto['estoque_baixo'] = estoque_atual <= estoque_minimo

    produtos.sort(key=lambda produto: (not produto['estoque_baixo'], str(produto.get('nome', '')).lower()))
    total_abaixo = sum(1 for produto in produtos if produto['estoque_baixo'])
    total_normal = len(produtos) - total_abaixo
    return render_template(
        'relatorio_estoque.html',
        produtos=produtos,
        total_abaixo=total_abaixo,
        total_normal=total_normal,
    )

if __name__ == '__main__':
    app.run(debug=True)
