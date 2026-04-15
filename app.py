# import pandas as pd
from flask import Flask, flash, render_template, request, redirect, url_for, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io
from urllib.parse import urlencode
import os

from config import APP_SECRET_KEY, FLASK_DEBUG, FLASK_HOST, FLASK_PORT
from db import listar_clientes, cadastrar_cliente, listar_produtos, cadastrar_produto
from db import listar_vendas, cadastrar_venda, listar_usuarios, listar_caixas, get_cliente, listar_categorias
from db import cadastrar_item_venda, atualizar_estoque, cadastrar_movimentacao, repor_estoque, get_itens_venda
from db import get_produto, editar_cliente, excluir_cliente, editar_produto, excluir_produto, get_venda, editar_venda, excluir_venda

app = Flask(__name__)
app.config['SECRET_KEY'] = APP_SECRET_KEY
app.config['TEMPLATES_AUTO_RELOAD'] = True


@app.template_filter('moeda')
def formatar_moeda(valor):
    try:
        numero = float(valor or 0)
    except (TypeError, ValueError):
        numero = 0.0

    texto = f'{numero:,.2f}'
    return f"R$ {texto.replace(',', 'X').replace('.', ',').replace('X', '.')}"


def resumir_vendas(vendas):
    total_registros = len(vendas)
    vendas_finalizadas = [venda for venda in vendas if venda.get('status') == 'FINALIZADA']
    faturamento_total = sum(float(venda.get('total_liquido') or 0) for venda in vendas_finalizadas)
    canceladas = sum(1 for venda in vendas if venda.get('status') == 'CANCELADA')
    finalizadas = len(vendas_finalizadas)

    return {
        'quantidade': total_registros,
        'canceladas': canceladas,
        'finalizadas': finalizadas,
        'faturamento_total': faturamento_total,
        'ticket_medio': faturamento_total / finalizadas if finalizadas else 0,
        'taxa_cancelamento': (canceladas / total_registros * 100) if total_registros else 0,
    }


def totalizar_itens_venda(itens_venda):
    return sum((item.get('quantidade') or 0) * float(item.get('preco_unitario') or 0) for item in itens_venda)


def enriquecer_venda(venda, itens_venda):
    venda_enriquecida = dict(venda)
    total_bruto_calculado = totalizar_itens_venda(itens_venda)
    desconto = float(venda_enriquecida.get('desconto') or 0)
    venda_enriquecida['total_bruto_calculado'] = total_bruto_calculado
    venda_enriquecida['total_liquido_calculado'] = max(total_bruto_calculado - desconto, 0)
    return venda_enriquecida


def montar_contexto_form_venda():
    return {
        'clientes': listar_clientes(),
        'produtos': listar_produtos(),
        'usuarios': listar_usuarios(),
        'caixas': listar_caixas(),
    }


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
    vendas = listar_vendas_filtradas(filtros)
    contexto = {
        'clientes': listar_clientes(),
        'usuarios': listar_usuarios(),
        'produtos': listar_produtos(),
        'vendas': vendas,
        'resumo': resumir_vendas(vendas),
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
        p.drawString(350, y, formatar_moeda(v.get('total_liquido', 0)))
        p.drawString(450, y, str(v.get('status', '')))
        y -= 18
    p.save()
    buffer.seek(0)
    return send_file(buffer, download_name='relatorio_vendas.pdf', as_attachment=True, mimetype='application/pdf')

@app.route('/relatorio/vendas/export/excel')
def relatorio_vendas_export_excel():
    # Temporariamente desabilitado devido a problema com pandas
    return "Exportação para Excel temporariamente indisponível. Use PDF.", 503

@app.route('/relatorio/vendas')
def relatorio_vendas():
    return render_template('relatorio_vendas.html', **montar_contexto_relatorio_vendas())


@app.route('/categorias')
def categorias():
    lista = listar_categorias()
    return render_template('categorias.html', categorias=lista)

@app.route('/vendas/editar/<int:id>', methods=['GET', 'POST'])
def vendas_editar(id):
    venda = get_venda(id)
    if not venda:
        flash('Venda não encontrada.', 'warning')
        return redirect(url_for('vendas'))

    itens_venda = get_itens_venda(id)
    contexto_formulario = montar_contexto_form_venda()
    venda = enriquecer_venda(venda, itens_venda)

    if request.method == 'POST':
        cliente_id = int(request.form['cliente_id'])
        usuario_id = int(request.form['usuario_id'])
        caixa_id = int(request.form['caixa_id'])
        desconto = float(request.form.get('desconto') or 0)
        status = request.form['status']
        total_bruto = totalizar_itens_venda(itens_venda)
        total_liquido = max(total_bruto - desconto, 0)

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
                    venda.update(
                        {
                            'cliente_id': cliente_id,
                            'usuario_id': usuario_id,
                            'caixa_id': caixa_id,
                            'desconto': desconto,
                            'status': status,
                            'total_bruto_calculado': total_bruto,
                            'total_liquido_calculado': total_liquido,
                        }
                    )
                    return render_template(
                        'vendas_editar.html',
                        venda=venda,
                        itens_venda=itens_venda,
                        **contexto_formulario,
                        erro=str(exc),
                    )

        venda.update(
            {
                'cliente_id': cliente_id,
                'usuario_id': usuario_id,
                'caixa_id': caixa_id,
                'desconto': desconto,
                'status': status,
                'total_bruto_calculado': total_bruto,
                'total_liquido_calculado': total_liquido,
            }
        )
        editar_venda(id, cliente_id, usuario_id, caixa_id, total_bruto, desconto, total_liquido, status)
        flash('Venda atualizada com sucesso.', 'success')
        return redirect(url_for('vendas'))

    return render_template(
        'vendas_editar.html',
        venda=venda,
        itens_venda=itens_venda,
        **contexto_formulario,
    )

@app.route('/vendas/excluir/<int:id>')
def vendas_excluir(id):
    venda = get_venda(id)
    if not venda:
        flash('Venda não encontrada.', 'warning')
        return redirect(url_for('vendas'))

    excluir_venda(id)
    flash('Venda excluída com sucesso.', 'success')
    return redirect(url_for('vendas'))

@app.route('/vendas')
def vendas():
    lista = [normalizar_venda(venda) for venda in listar_vendas()]
    return render_template('vendas.html', vendas=lista, resumo=resumir_vendas(lista))

@app.route('/vendas/cadastrar', methods=['GET', 'POST'])
def vendas_cadastrar():
    contexto_formulario = montar_contexto_form_venda()
    clientes = contexto_formulario['clientes']
    produtos = contexto_formulario['produtos']
    usuarios = contexto_formulario['usuarios']
    caixas = contexto_formulario['caixas']

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
                    **contexto_formulario,
                    erro='Informe uma quantidade valida para cada produto selecionado.',
                )

            quantidade = int(quantidade_raw)
            estoque_atual = int(produto.get('estoque_atual') or 0)

            if quantidade > estoque_atual:
                return render_template(
                    'vendas_cadastrar.html',
                    **contexto_formulario,
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
                **contexto_formulario,
                erro='Selecione pelo menos um produto para registrar a venda.',
            )

        total_bruto = totalizar_itens_venda(itens_venda)
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
                **montar_contexto_form_venda(),
                erro=str(exc),
            )

        flash('Venda registrada com sucesso.', 'success')
        return redirect(url_for('vendas'))

    return render_template('vendas_cadastrar.html', **contexto_formulario)

@app.route('/')
def index():
    clientes = listar_clientes()
    produtos = listar_produtos()
    vendas = listar_vendas()
    vendas_normalizadas = [normalizar_venda(venda) for venda in vendas]
    resumo = resumir_vendas(vendas_normalizadas)

    produtos_estoque_baixo = []
    for produto in produtos:
        estoque_atual = int(produto.get('estoque_atual') or 0)
        estoque_minimo = int(produto.get('estoque_minimo') or 0)
        if estoque_atual <= estoque_minimo:
            produtos_estoque_baixo.append(produto)

    produtos_estoque_baixo.sort(key=lambda produto: (produto.get('estoque_atual') or 0, str(produto.get('nome', '')).lower()))
    vendas_recentes = sorted(vendas_normalizadas, key=lambda venda: venda.get('data_venda') or '', reverse=True)[:5]

    return render_template(
        'index.html',
        total_clientes=len(clientes),
        total_produtos=len(produtos),
        total_vendas=resumo['quantidade'],
        valor_total_vendas=resumo['faturamento_total'],
        media_vendas=resumo['ticket_medio'],
        vendas_canceladas=resumo['canceladas'],
        taxa_cancelamento=resumo['taxa_cancelamento'],
        estoque_critico=len(produtos_estoque_baixo),
        vendas_recentes=vendas_recentes,
        produtos_estoque_baixo=produtos_estoque_baixo[:5],
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
        flash('Cliente cadastrado com sucesso.', 'success')
        return redirect(url_for('clientes'))
    return render_template('clientes_cadastrar.html')

@app.route('/produtos')
def produtos():
    lista = listar_produtos()
    total_estoque_baixo = sum(1 for produto in lista if (produto.get('estoque_atual') or 0) <= (produto.get('estoque_minimo') or 0))
    return render_template('produtos.html', produtos=lista, total_estoque_baixo=total_estoque_baixo)

@app.route('/produtos/cadastrar', methods=['GET', 'POST'])
def produtos_cadastrar():
    categorias = listar_categorias()

    if request.method == 'POST':
        if not categorias:
            return render_template(
                'produtos_cadastrar.html',
                categorias=categorias,
                erro='Cadastre ao menos uma categoria no banco para criar produtos.',
            )

        nome = request.form['nome']
        codigo_barras = request.form['codigo_barras']
        categoria_id = request.form['categoria_id']
        preco_custo = request.form['preco_custo']
        preco_venda = request.form['preco_venda']
        estoque_atual = request.form['estoque_atual']
        estoque_minimo = request.form['estoque_minimo']

        imagem_filename = None
        if 'imagem' in request.files:
            file = request.files['imagem']
            if file and file.filename:
                # Criar diretório se não existir
                upload_dir = os.path.join(app.root_path, 'static', 'images')
                os.makedirs(upload_dir, exist_ok=True)
                # Salvar arquivo
                filename = f"produto_{len(listar_produtos()) + 1}_{file.filename}"
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                imagem_filename = filename

        cadastrar_produto(nome, codigo_barras, int(categoria_id), float(preco_custo), float(preco_venda), int(estoque_atual), int(estoque_minimo), imagem_filename)
        flash('Produto cadastrado com sucesso.', 'success')
        return redirect(url_for('produtos'))
    return render_template('produtos_cadastrar.html', categorias=categorias)

@app.route('/clientes/editar/<int:id>', methods=['GET', 'POST'])
def clientes_editar(id):
    cliente = get_cliente(id)
    if not cliente:
        flash('Cliente não encontrado.', 'warning')
        return redirect(url_for('clientes'))
    if request.method == 'POST':
        nome = request.form['nome']
        cpf_cnpj = request.form['cpf_cnpj']
        telefone = request.form['telefone']
        email = request.form['email']
        editar_cliente(id, nome, cpf_cnpj, telefone, email)
        flash('Cliente atualizado com sucesso.', 'success')
        return redirect(url_for('clientes'))
    return render_template('clientes_editar.html', cliente=cliente)

@app.route('/clientes/excluir/<int:id>')
def clientes_excluir(id):
    cliente = get_cliente(id)
    if not cliente:
        flash('Cliente não encontrado.', 'warning')
        return redirect(url_for('clientes'))

    excluir_cliente(id)
    flash('Cliente excluído com sucesso.', 'success')
    return redirect(url_for('clientes'))

@app.route('/produtos/editar/<int:id>', methods=['GET', 'POST'])
def produtos_editar(id):
    produto = get_produto(id)
    categorias = listar_categorias()

    if not produto:
        flash('Produto não encontrado.', 'warning')
        return redirect(url_for('produtos'))
    if request.method == 'POST':
        if not categorias:
            return render_template(
                'produtos_editar.html',
                produto=produto,
                categorias=categorias,
                erro='Cadastre ao menos uma categoria no banco para editar produtos.',
            )

        nome = request.form['nome']
        codigo_barras = request.form['codigo_barras']
        categoria_id = request.form['categoria_id']
        preco_custo = request.form['preco_custo']
        preco_venda = request.form['preco_venda']
        estoque_atual = request.form['estoque_atual']
        estoque_minimo = request.form['estoque_minimo']

        imagem_filename = produto.get('imagem')  # Manter imagem existente se não for alterada
        if 'imagem' in request.files:
            file = request.files['imagem']
            if file and file.filename:
                # Criar diretório se não existir
                upload_dir = os.path.join(app.root_path, 'static', 'images')
                os.makedirs(upload_dir, exist_ok=True)
                # Salvar arquivo
                filename = f"produto_{id}_{file.filename}"
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                imagem_filename = filename

        editar_produto(id, nome, codigo_barras, int(categoria_id), float(preco_custo), float(preco_venda), int(estoque_atual), int(estoque_minimo), imagem_filename)
        flash('Produto atualizado com sucesso.', 'success')
        return redirect(url_for('produtos'))
    return render_template('produtos_editar.html', produto=produto, categorias=categorias)

@app.route('/produtos/excluir/<int:id>')
def produtos_excluir(id):
    produto = get_produto(id)
    if not produto:
        flash('Produto não encontrado.', 'warning')
        return redirect(url_for('produtos'))

    excluir_produto(id)
    flash('Produto excluído com sucesso.', 'success')
    return redirect(url_for('produtos'))

@app.route('/controle-estoque')
@app.route('/relatorio/estoque')
def controle_estoque():
    produtos = listar_produtos()
    valor_em_estoque = 0
    for produto in produtos:
        estoque_atual = produto.get('estoque_atual') or 0
        estoque_minimo = produto.get('estoque_minimo') or 0
        produto['estoque_baixo'] = estoque_atual <= estoque_minimo
        valor_em_estoque += float(produto.get('preco_venda') or 0) * int(estoque_atual)

    produtos.sort(key=lambda produto: (not produto['estoque_baixo'], str(produto.get('nome', '')).lower()))
    total_abaixo = sum(1 for produto in produtos if produto['estoque_baixo'])
    total_normal = len(produtos) - total_abaixo
    return render_template(
        'relatorio_estoque.html',
        produtos=produtos,
        total_abaixo=total_abaixo,
        total_normal=total_normal,
        valor_em_estoque=valor_em_estoque,
    )

if __name__ == '__main__':
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
