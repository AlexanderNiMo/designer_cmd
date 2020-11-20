
[![image](https://img.shields.io/pypi/v/designer_cmd.svg)](https://pypi.org/project/designer_cmd)
[![image](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

# Пакет для автоматизации взаимодействия с пакетным режимом 1С.

Формат команд поддерживается только > 8.3.12

# Установка:
    pip install designer_cmd
    
# Пример использования:
    
    from designer_cmd import api
    
    conn = api.Connection(user='User', password='Password', file_path='DB_Path')
    designer = api.Designer('8.3.12.1254', self.conn)

    designer.load_config_from_file('path_to_cf_file')
    
    # Пример работы с хранилищем - создание хранилища 
    
    repo_conn = api.RepositoryConnection('REPO_PATH', 'user', 'password')
    designer.repo_connection = repo_conn
    
    designer.create_repository()
    
    
# Функциональность:

- Работа в контексте Windows.
- Выгрузка/Загрузка cf.
        
        designer.load_config_from_file('path_to_cf_file')
        designer.dump_config_to_file('path_to_cf_file')      
        
- Выгрузка/Загрузка в/из xml, поддерживается инкрементальный режим выгрузки

        designer.dump_config_to_files(dir_xml_config_path)
        designer.load_config_from_file(self.cf_path)
      
- Выгрузка/Загрузка расширений из xml.

        designer.load_extension_from_files('dir_with_xml_data', 'extension_name')
        designer.dump_extension_to_files('dir_with_xml_data', 'extension_name')       
        
        # Выгрузка всех расширений
        designer.dump_extensions_to_files(cfe_dir_path)
      
- Выгрузка/Загрузка расширений из файлов cfe
        
        designer.dump_extension_to_file('cfe_file', 'extension_name')
        designer.load_extension_from_file('cfe_file', 'extension_name')
        
        
- Выгрузка/Загрузка dt.

        designer.load_db_from_file('dt_path')
        designer.dump_db_to_file('dt_path')
        

- Сравнение конфигурации с файлом cf
        
        designer.compare_config_with_file('path_to_cf', 'report_path')
        
- Объединение конфигурации с файлом cf

        designer.merge_config_with_file('path_to_cf', 'path_to_merge_settings')      


- Обновление структуры конфигурации

        designer.update_db_config()
    
- Конвертация cf, cfe в xml.

        api.convert_cf_to_xml('path_to_cf') 
        api.convert_cfe_to_xml('path_to_cfe')      
        
- Работа с хранилищем
    - Определение параметров подключения: 
    
            # Перед вызовом функций хранилища, необходимо определить настройки подклчения
            
            repo_conn = api.RepositoryConnection('REPO_PATH', 'user', 'password')
            designer.repo_connection = repo_conn
    - Добавление пользователя хранилища
    
            designer.add_user_to_repository('user', 'password', )
            
    - Захват и освобождение объектов
            
            designer.lock_objects_in_repository("path_to_file_with_list_obj")      
            designer.unlock_objects_in_repository("path_to_file_with_list_obj") 
    - Помещение объектов в хранилище
    
            designer.commit_config_to_repo('comment', 'repo_obj_list')  
          
    - Обновление конфигурации базы из хранилища               
            
            designer.update_conf_from_repo()
        
    - Привязка конфигурации к хранилищу
            
            designer.bind_cfg_to_repo()

#Планируемая фукциональность:

- Работа в контексте linux
- Работа с git
