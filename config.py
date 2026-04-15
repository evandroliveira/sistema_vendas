# config.py
import os


def _obter_flag_ambiente(nome_variavel, valor_padrao='0'):
    valor = os.getenv(nome_variavel, valor_padrao).strip().lower()
    return valor in {'1', 'true', 'yes', 'on'}


DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'sistema_vendas'),
    'connection_timeout': int(os.getenv('DB_TIMEOUT', '10')),
}

APP_SECRET_KEY = os.getenv('APP_SECRET_KEY', 'sistema-vendas-dev')
FLASK_DEBUG = _obter_flag_ambiente('FLASK_DEBUG', '1')
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
