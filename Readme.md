# Пакет для автоматизации взаимодействия с пакетным режимом 1С.

Формат команд поддерживается только > 8.3.12

# Установка:
    pip install designer_cmd
    
# Пример использования:
    
    from designer_cmd import api
    
    conn = api.Connection(user='User', password='Password', file_path='DB_Path')
    designer = api.Designer('8.3.12.1254', self.conn)

    designer.load_config_from_file('path_to_cf_file')
    
# Функциональность:

-- Работа в контексте Windows:

- Выгрузка/Загрузка cf.
- Выгрузка/Загрузка dt.
- Выгрузка/Загрузка в/из xml
- Сравнение конфигурации с файлом cf
- Обновление структуры конфигурации

#Планируемая фукциональность:

- Работа в контексте linux
- Работа с хранилищем
- Работа с git
