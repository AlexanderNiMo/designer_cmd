
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
        
- Проверка применения расширения\расширений

        self.designer.check_apply_extension('extension_name')
        # Выгрузка всех расширений
        self.designer.check_apply_extension()

- Удаление расширения\вех расширений из базы

        self.designer.delete_extension('extension_name')
        # Всех раширений:
        self.designer.delete_extension()
      
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
            
    - Привязка конфигурации к хранилищу
            
            designer.unbind_cfg_from_repo()

- Работа в режиме Enterprise
       
    from designer_cmd import api   
    conn = api.Connection(user='User', password='Password', file_path='DB_Path')
    ent = api.Enterprise('8.3.12.1254', self.conn)
           
    - Запуск обработки в базе:
             
            ent.run_app(
                ep_x_path=path_to_epf,
                c_string='params_to_c'
            ) 
                
    - Запуск в режиме ТестМенеджера
        
            ent.run_app(mode=ent.RunMode.MANAGER, wait=False) # Без ожидания 
            ent.run_app(mode=ent.RunMode.MANAGER) # Ожидать завершения
        
    - Запуск в режиме Тестклиента (При запуске производиться проверка доступности порта)
    
            ent.run_app(mode=ent.RunMode.CLIENT, port=1538, wait=False) # Без ожидания (порт по умолчанию 1538) 
            ent.run_app(wait=True) # Ожидать завершения
    
    - Запуск 
    
            ent.run_app() # Возможен запуск без ожидания.
     
    - Завершение всех запущенных клиентов по текущему соединению
    
            ent.kill_all_clients()  
     
        
- Работа с кластером через Rac:
        
        from designer_cmd import api

        conn = api.RacConnection(admin, passwd, server, port)
        r = api.Rac(v_8version, conn)
        # r.set_cluster_id(cluster_id) # Если есть несколько кластеров под управлением ras 
        r.set_cluster_id() # Установить id первого кластера в списке r.cluster.get_cluster_list()
        
    - Высокоуровневый api:
            
            r.disconnect_users(base_ref='base_name')
            
    - Режим cluster:
            
            cluster_list = r.cluster.get_cluster_list()
            
    - Режим infobase:
            
            base_data = r.infobase.get_base_by_ref(base_name)
            r.base_id = base_data.get('infobase')
            
            r.infobase.get_base_list()
            r.infobase.deny_sessions(permission_code='333')
            r.infobase.deny_scheduled_jobs()
      
      - Удаление базы:
            
            base_data = r.infobase.get_base_by_ref(base_name)
            r.base_id = base_data.get('infobase')
            
            r.infobase.drop_base()
      
      - Созданеие базы
            
            server_type = api.SqlServerType.MSSQL
            sql_conn = api.SqlServerConnection(host=host, user=user, password=password, type=server_type)
            
            new_base_id = self.mod.create_base(db_name, sql_conn)
          
    
    - Режим sessions:
            
            session_list = r.sessions.get_session_list()
            r.sessions.session_info(session_id)
            r.sessions.terminate_session(session_id)
            

         
         
                    
            
#Планируемая фукциональность:

- Работа в контексте linux
- Работа с git
