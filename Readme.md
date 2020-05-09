# Пакет для автоматизации взаимодействия с пакетным режимом 1С.

Формат команд поддерживается только > 8.3.12

# Установка:
    pip install designer_1c
    
# Пример использования:
    
    from Designer_cmd import Designer, Connection
    
    conn = Connection(user='User', password='Password', file_path='DB_Path')
    designer = Designer('8.3.12.1254', self.conn)
    
    designer.load_config_from_file('path_to_cf_file')