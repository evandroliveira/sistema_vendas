# main.py
from db import listar_clientes, cadastrar_cliente


def menu():
    while True:
        print("\n=== Sistema de Vendas ===")
        print("1. Listar clientes")
        print("2. Cadastrar cliente")
        print("3. Listar produtos")
        print("4. Cadastrar produto")
        print("5. Listar categorias")
        print("6. Cadastrar categoria")
        print("7. Listar usuários")
        print("8. Cadastrar usuário")
        print("9. Listar vendas")
        print("10. Cadastrar venda")
        print("11. Listar movimentações de estoque")
        print("12. Cadastrar movimentação de estoque")
        print("13. Listar caixas")
        print("14. Abrir caixa")
        print("15. Fechar caixa")
        print("0. Sair")
        opcao = input("Escolha uma opção: ")
        if opcao == "1":
            clientes = listar_clientes()
            for c in clientes:
                print(f"ID: {c['id']} | Nome: {c['nome']} | Email: {c['email']}")
        elif opcao == "2":
            nome = input("Nome: ")
            cpf_cnpj = input("CPF/CNPJ: ")
            telefone = input("Telefone: ")
            email = input("Email: ")
            cadastrar_cliente(nome, cpf_cnpj, telefone, email)
            print("Cliente cadastrado com sucesso!")
        elif opcao == "3":
            from db import listar_produtos
            produtos = listar_produtos()
            for p in produtos:
                print(f"ID: {p['id']} | Nome: {p['nome']} | Preço Venda: {p['preco_venda']} | Estoque: {p['estoque_atual']}")
        elif opcao == "4":
            from db import cadastrar_produto
            nome = input("Nome: ")
            codigo_barras = input("Código de Barras: ")
            categoria_id = input("ID da Categoria: ")
            preco_custo = input("Preço de Custo: ")
            preco_venda = input("Preço de Venda: ")
            estoque_atual = input("Estoque Atual: ")
            estoque_minimo = input("Estoque Mínimo: ")
            cadastrar_produto(nome, codigo_barras, int(categoria_id), float(preco_custo), float(preco_venda), int(estoque_atual), int(estoque_minimo))
            print("Produto cadastrado com sucesso!")
        elif opcao == "5":
            from db import listar_categorias
            categorias = listar_categorias()
            for cat in categorias:
                print(f"ID: {cat['id']} | Nome: {cat['nome']} | Ativo: {cat['ativo']}")
        elif opcao == "6":
            from db import cadastrar_categoria
            nome = input("Nome da Categoria: ")
            ativo = input("Ativo (1=Sim, 0=Não): ")
            cadastrar_categoria(nome, int(ativo))
            print("Categoria cadastrada com sucesso!")
        elif opcao == "7":
            from db import listar_usuarios
            usuarios = listar_usuarios()
            for u in usuarios:
                print(f"ID: {u['id']} | Nome: {u['nome']} | Email: {u['email']} | Perfil: {u['perfil_id']} | Ativo: {u['ativo']}")
        elif opcao == "8":
            from db import cadastrar_usuario
            nome = input("Nome: ")
            email = input("Email: ")
            senha = input("Senha: ")
            perfil_id = input("ID do Perfil: ")
            ativo = input("Ativo (1=Sim, 0=Não): ")
            cadastrar_usuario(nome, email, senha, int(perfil_id), int(ativo))
            print("Usuário cadastrado com sucesso!")
        elif opcao == "9":
            from db import listar_vendas
            vendas = listar_vendas()
            for v in vendas:
                print(f"ID: {v['id']} | Cliente: {v['cliente_id']} | Usuário: {v['usuario_id']} | Caixa: {v['caixa_id']} | Total Líquido: {v['total_liquido']} | Status: {v['status']}")
        elif opcao == "10":
            from db import cadastrar_venda
            cliente_id = input("ID do Cliente: ")
            usuario_id = input("ID do Usuário: ")
            caixa_id = input("ID do Caixa: ")
            total_bruto = input("Total Bruto: ")
            desconto = input("Desconto: ")
            total_liquido = input("Total Líquido: ")
            status = input("Status (FINALIZADA/CANCELADA): ")
            cadastrar_venda(int(cliente_id), int(usuario_id), int(caixa_id), float(total_bruto), float(desconto), float(total_liquido), status)
            print("Venda cadastrada com sucesso!")
        elif opcao == "11":
            from db import listar_movimentacoes
            movs = listar_movimentacoes()
            for m in movs:
                print(f"ID: {m['id']} | Produto: {m['produto_id']} | Tipo: {m['tipo']} | Quantidade: {m['quantidade']} | Referência: {m['referencia']}")
        elif opcao == "12":
            from db import cadastrar_movimentacao
            produto_id = input("ID do Produto: ")
            tipo = input("Tipo (ENTRADA/SAIDA/AJUSTE): ")
            quantidade = input("Quantidade: ")
            referencia = input("Referência: ")
            cadastrar_movimentacao(int(produto_id), tipo, int(quantidade), referencia)
            print("Movimentação cadastrada com sucesso!")
        elif opcao == "13":
            from db import listar_caixas
            caixas = listar_caixas()
            for c in caixas:
                print(f"ID: {c['id']} | Usuário: {c['usuario_id']} | Valor Inicial: {c['valor_inicial']} | Valor Final: {c['valor_final']} | Status: {c['status']}")
        elif opcao == "14":
            from db import abrir_caixa
            usuario_id = input("ID do Usuário: ")
            valor_inicial = input("Valor Inicial: ")
            abrir_caixa(int(usuario_id), float(valor_inicial))
            print("Caixa aberto com sucesso!")
        elif opcao == "15":
            from db import fechar_caixa
            caixa_id = input("ID do Caixa: ")
            valor_final = input("Valor Final: ")
            fechar_caixa(int(caixa_id), float(valor_final))
            print("Caixa fechado com sucesso!")
        elif opcao == "0":
            print("Saindo...")
            break
        else:
            print("Opção inválida!")

if __name__ == "__main__":
    menu()
