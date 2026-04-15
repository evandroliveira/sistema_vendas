from db import Database

# Adicionar coluna imagem à tabela produto
db = Database()
try:
    db.cursor.execute("ALTER TABLE produto ADD COLUMN imagem VARCHAR(255)")
    db.conn.commit()
    print("Coluna 'imagem' adicionada com sucesso à tabela produto.")
except Exception as e:
    print(f"Erro ao adicionar coluna: {e}")
finally:
    db.close()