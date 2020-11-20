from designer_cmd.utils import (get_platform_path, execute_command, xml_conf_version_file_exists,
                                PlatformVersion, clear_folder, windows_platform)
import os
import logging
import tempfile
from typing import Optional, Callable

logger = logging.getLogger(__file__)


class RepositoryConnection:

    def __init__(self, repository_path: str, user: str = '', password: str = ''):
        self.password = password
        self.user = user

        full_repo_path = repository_path
        if 'tcp' not in repository_path:
            full_repo_path = os.path.abspath(repository_path)

        self.repository_path = full_repo_path

    def get_connection_params(self) -> list:
        params = [f'/ConfigurationRepositoryF', f'{self.repository_path}']
        if self.user != '':
            params.append(f'/ConfigurationRepositoryN')
            params.append(f'{self.user}')
        if self.password != '':
            params.append(f'/ConfigurationRepositoryP')
            params.append(f'{self.password}')

        return params

    def __repr__(self):
        return f'path: {self.repository_path} user: {self.user}'


class Connection:
    """
    Описывает соединение с базой
    """
    def __init__(self, user: str= '',
                 password: str = '',
                 file_path: str = '',
                 server_path: str = '',
                 server_base_ref: str = '',
                 ib_name: str = '',
                 time_out: int = 3600):

        if file_path == '' and (server_path == '' or server_base_ref == '') and ib_name == '':
            raise AttributeError('Для соедеинения не определен путь к базе!')

        self.user = user
        self.password = password

        self.ib_name = ib_name

        self.file_path = os.path.abspath(file_path) if file_path != '' else ''
        self.server_path = server_path
        self.server_base_ref = server_base_ref

        self.__time_out = time_out

    @property
    def timeout(self):
        return self.__time_out

    @timeout.setter
    def timeout(self, value):
        self.__time_out = value

    def get_connection_params(self) -> list:
        """
        Возвращает строковое представление параметров для подключения по текущему описанию соединения

        :return: str : Текстовые параметры для командной строки
        """
        params = []
        if self.file_path != '':
            params += [f'/F', f'{self.file_path}']
        elif self.ib_name != '':
            params += [f'/IBName', f'{self.ib_name}']
        else:
            params += [f'/S', f'{self.server_path}\\{self.server_base_ref}']

        if self.user != '':
            params += [f'/N', f'{self.user}']
            params += [f'/P', f'{self.password}']

        return params

    def get_connection_string(self):
        if self.ib_name != '':
            raise ValueError('Не возможно сформировать строку подключения для базы из списка.')

        if self.file_path != '':
            if self.user == '':
                return f'File={self.file_path}'
            else:
                return f'Usr={self.user} Pwd={self.password} File={self.file_path}'
        else:
            raise NotImplementedError('Создание базы в серверном варианте не реализованно.')

    def __repr__(self):
        if self.file_path != '':
            connection_path = f'File: {self.file_path}'
        elif self.ib_name != '':
            connection_path = f'IBName: {self.ib_name}'
        else:
            connection_path = f'Server: {self.server_path} base_ref: {self.server_base_ref}'
        connection_path += f'user: {self.user}' if self.user != '' else ''
        return connection_path


def have_repo_connection(func):

    def warper(self, *args, **kwargs):
        if self.repo_connection is None:
            raise AttributeError('Не передано описание подключения к хранилищу!')
        return func(self, *args, **kwargs)

    return warper


class Designer:

    def __init__(self, platform_version: str, connection: Connection, repo_connection: RepositoryConnection = None):

        self.repo_connection = repo_connection
        self.platform_version: PlatformVersion = PlatformVersion(platform_version)
        self.connection = connection
        self.platform_path = get_platform_path(self.platform_version)

    def __execute_command(self, mode: str, command_params: list, connection_params_required: bool = True):
        params = [mode]
        if connection_params_required:
            params += self.connection.get_connection_params()
        params += command_params
        params += ['/DisableStartupDialogs /DisableStartupMessages']
        debug_file_name = self.add_debug_params(params)

        str_command = ' '.join(params)
        logger.debug(f'Выполняю команду {self.platform_path} {str_command}')

        result = execute_command(self.platform_path, params, self.connection.timeout)

        if result[0] != 0:
            encoding = 'utf-8'
            with open(debug_file_name, encoding=encoding) as f:
                logger.error(f'При выполнении команды произошла ошибка:\n'
                             f'{f.read()}\n'
                             f'{result[1]}')
            os.remove(debug_file_name)
            raise SyntaxError('Не удалось выполнить команду!')
        os.remove(debug_file_name)

    def add_debug_params(self, params) -> str:
        debug_file_name = tempfile.mkstemp('.log')
        params.append('/Out')
        params.append(debug_file_name[1])
        os.close(debug_file_name[0])
        return debug_file_name[1]

    def create_base(self):
        """
        Создает базу данных.
        Соответствует режиму CREATEINFOBASE <строка соединения>

        """
        logger.info(f'Создаю базу по соединению: {self.connection}')
        params = [f'{self.connection.get_connection_string()}']
        self.__execute_command('CREATEINFOBASE', params, False)

    def update_db_config(self, dynamic: bool = False, warnings_as_errors: bool = False, on_server: bool = False):
        """
        Обновляет конфигурацию db. (соответствует команде /UpdateDBCfg)

        :return:
        """
        logger.info(f'Обновляю конфигурацию БД по соединению {self.connection}')
        params = [f'/UpdateDBCfg']

        if dynamic:
            params.append('-Dynamic +')
        if warnings_as_errors:
            params.append('-WarningsAsErrors')
        if on_server:
            params.append('-Server')

        self.__execute_command(f'DESIGNER', params)

    def load_db_from_file(self, file_path: str) -> None:
        """
        Загрузка базы из файла dt (соответствует команде /RestoreIB)

        :param file_path: str - Путь к файлу базы (dt.)
        :return:
        """
        full_file_path = os.path.abspath(file_path)
        logger.info(f'Загружаю файл dt {full_file_path} в БД по соединению {self.connection}')
        params = ['/RestoreIB', f'{full_file_path}']
        self.__execute_command(f'DESIGNER', params)

    def dump_db_to_file(self, file_path: str) -> None:
        """
        Выгрузка базы в файл (соответствует команде /DumpIB)

        :param file_path: str - Путь к файлу для выгрзки базы (dt.)
        :return:
        """
        full_file_path = os.path.abspath(file_path)
        logger.info(f'Выгружаю файл dt по пути {full_file_path} из БД по соединению {self.connection}')
        params = ['/DumpIB', f'{full_file_path}']
        self.__execute_command(f'DESIGNER', params)

    def load_config_from_files(self, catalog_path: str, list_file: Optional[str] = None) -> None:
        """
        Загружает конфигурацию из файлов (соответствует команде /LoadConfigFromFiles)

        :param list_file: путь к файлу со списком файлов к загрузке
        :param catalog_path: str - путь к каталогу из которого необходимо произвести загрузку.
        :return:
        """
        full_catalog_path = os.path.abspath(catalog_path)
        logger.info(f'Загружаю конфигурацию из файлов {full_catalog_path} конфигурацию БД по соединению {self.connection}')
        params = [f'/LoadConfigFromFiles', f'{full_catalog_path}']

        if list_file is not None and os.path.exists(list_file):
            params.append(f'-listFile')
            params.append(f'{os.path.abspath(list_file)}')

        self.__execute_command(f'DESIGNER', params)

    def dump_config_to_files(self, catalog_path: str, update: bool = True) -> None:
        """
        Выгружает конфигурацию в файлы (соответствует команде /DumpConfigToFiles)

        :param update:
        :param catalog_path: Каталог в который будет выгружен файл
        :return:
        """
        full_catalog_path = os.path.abspath(catalog_path)
        logger.info(
            f'Выгружаю конфигурацию в файлы {full_catalog_path} по соединению {self.connection}')
        params = [f'/DumpConfigToFiles', f'{full_catalog_path}']

        increment_platform_version = PlatformVersion('8.3.10')

        if (update and xml_conf_version_file_exists(catalog_path)
                and self.platform_version >= increment_platform_version):
            params.append('-update')
            params.append('-force')

        self.__execute_command(f'DESIGNER', params)

    def load_config_from_file(self, file_path: str) -> None:
        """
        Загружает конфигурацию в базу из файла cf (соответствует команде /LoadCfg)

        :param file_path:
        :return:
        """
        full_file_path = os.path.abspath(file_path)
        logger.info(
            f'Загружаю конфигурацию из файла {full_file_path} в конфигурацию БД по соединению {self.connection}')
        params = [f'/LoadCfg', f'{full_file_path}']
        self.__execute_command(f'DESIGNER', params)

    def dump_config_to_file(self, file_path: str) -> None:
        """
        Выполнить сохранение конфигурации в файл cf (соответствует команде /DumpCfg)
        :param file_path:
        :return:
        """
        full_file_path = os.path.abspath(file_path)
        logger.info(
            f'Сохраняю конфигурацию в файл {full_file_path} из конфигурации БД по соединению {self.connection}')
        params = [f'/DumpCfg', f'{full_file_path}']
        self.__execute_command(f'DESIGNER', params)

    def dump_extension_to_file(self, file_path: str, extension_name: str):
        full_file_path = os.path.abspath(file_path)
        logger.info(
            f'Сохраняю расширения в файл {full_file_path} из конфигурации БД по соединению {self.connection}')
        params = [
            f'/DumpConfigToFiles', f'{full_file_path}',
            f'-Extension', f'{extension_name}',
            '-force'
        ]

        self.__execute_command(f'DESIGNER', params)

    def dump_extension_to_files(self, dir_path: str, extansion_name: str):
        full_dir_path = os.path.abspath(dir_path)
        logger.info(
            f'Сохраняю расширения в файл {full_dir_path} из конфигурации БД по соединению {self.connection}')
        params = [
            f'/DumpConfigToFiles', f'{full_dir_path}',
            f'-Extension', f'{extansion_name}'
        ]
        self.__execute_command(f'DESIGNER', params)

    def dump_extensions_to_files(self, dir_path):
        full_dir_path = os.path.abspath(dir_path)
        logger.info(
            f'Сохраняю расширения в файл {full_dir_path} из конфигурации БД по соединению {self.connection}')
        params = [
            f'/DumpConfigToFiles', f'{full_dir_path}',
            f'-AllExtensions',
        ]
        self.__execute_command(f'DESIGNER', params)

    def load_extension_from_file(self, extension_file_path: str, name: str):
        """
        Выполняет загрузку расширения из файла cfe в базу
        :param extension_file_path:
        :param name:
        """
        full_file_path = os.path.abspath(extension_file_path)
        logger.info(
            f'Загружаю расширения из файла {full_file_path} в конфигурацию БД по соединению {self.connection}')
        params = [
            f'/LoadCfg', f'{full_file_path}',
            f'-Extension', f'{name}'
        ]
        self.__execute_command(f'DESIGNER', params)

    def load_extension_from_files(self, extension_folder: str, name: str):
        """
        Выполняет загрузку расширения из каталога в базу
        :param extension_folder:
        :param name:
        """
        full_catalog_path = os.path.abspath(extension_folder)
        logger.info(
            f'Загружаю расширение c именем {name} из файлов {full_catalog_path} конфигурацию '
            f'БД по соединению {self.connection}')
        params = [
            f'/LoadConfigFromFiles', f'{full_catalog_path}',
            f'-Extension', f'{name}'
        ]

        self.__execute_command(f'DESIGNER', params)

    @have_repo_connection
    def create_repository(self):

        logger.info(
            f'Создание хранилища по подключению {self.repo_connection}'
            f'БД по соединению {self.connection}')

        params = self.repo_connection.get_connection_params()
        params.append(f'/ConfigurationRepositoryCreate')
        params.append('-AllowConfigurationChanges')
        params.append('-ChangesAllowedRule')
        params.append('ObjectIsEditableSupportEnabled')
        params.append('-ChangesNotRecommendedRule')
        params.append('ObjectIsEditableSupportEnabled')

        self.__execute_command(f'DESIGNER', params)

    @have_repo_connection
    def add_user_to_repository(self, user: str, password: str = '', rights: Optional[str] = None ):
        """
        Добавляет пользователя в хранилище (ConfigurationRepositoryAddUser)

        :type password: str
        :type user: str
        :type rights: str
        :param user: Пользователь хранилища
        :param password: Пароль к хранилищу
        :param rights: Роль пользователя возможные занчения:
            ReadOnly ‑ право на просмотр;
            LockObjects ‑ право на захват объектов;
            ManageConfigurationVersions ‑ право на изменение состава версий;
            Administration ‑ право на административные функции;
        """
        logger.info(
            f'добавлеине пользователя в хранилище {self.repo_connection}'
            f'из БД по соединению {self.connection}')

        params = self.repo_connection.get_connection_params()
        params.append(f'/ConfigurationRepositoryAddUser')
        params.extend([
            '-User', f'{user}',
            '-Pwd', f'{password}',
        ])
        if rights is None:
            rights = 'ReadOnly'

        params.extend([
            '-Rights', f'{rights}'
        ])

        self.__execute_command(f'DESIGNER', params)

    @have_repo_connection
    def unlock_objects_in_repository(self, objects_list: str):

        file_path = os.path.abspath(objects_list)
        logger.info(
            f'Отправляю объекты в хранилище {self.repo_connection} по списку объектов из файла {file_path}'
            f'БД по соединению {self.connection}')
        params = self.repo_connection.get_connection_params()
        params.extend([
            f'/ConfigurationRepositoryUnLock',
            f'-Objects', f'{file_path}'
        ])
        self.__execute_command(f'DESIGNER', params)

    @have_repo_connection
    def lock_objects_in_repository(self, objects: str, force: bool = False):

        file_path = os.path.abspath(objects)
        logger.info(
            f'Захватываю объекты в хранилище {self.repo_connection} по списку объектов из файла {file_path}'
            f'БД по соединению {self.connection}')
        params = self.repo_connection.get_connection_params()
        params.extend([
            f'/ConfigurationRepositoryLock',
            f'-Objects', f'{file_path}'
        ])
        if force:
            params.append('-revised')

        self.__execute_command(f'DESIGNER', params)

    @have_repo_connection
    def commit_config_to_repo(self, comment: str = '', objects: Optional[str] = None):
        """
        Выполняет отправку объектов в хранилище. операция /ConfigurationRepositoryCommit
        """

        logger.info(
            f'Отправка объектов в хранилище {self.repo_connection}'
            f'БД по соединению {self.connection}')

        params = self.repo_connection.get_connection_params()
        params.append(f'/ConfigurationRepositoryCommit')

        if objects is not None:
            params.extend([
                '-Objects', f'{objects}'
            ])
        params.extend([
            '-comment', f'{comment}'
        ])
        params.append('-force')

        self.__execute_command(f'DESIGNER', params)

    @have_repo_connection
    def dump_config_to_file_from_repo(self, file_path, version: Optional[str] = None):
        """
        Выполняет выгрузку конфигурации из хранилища /ConfigurationRepositoryDumpCfg
        """
        full_file_path = os.path.abspath(file_path)

        logger.info(
            f'Выгрузка cf из хранилища {self.repo_connection}'
            f'БД по соединению {self.connection}')

        params = self.repo_connection.get_connection_params()
        params.append(f'/ConfigurationRepositoryDumpCfg')
        params.append(f'{full_file_path}')

        cfg_version = -1
        if version is not None:
            cfg_version = version
        params.extend([
            '-v', f'{cfg_version}'
        ])

        self.__execute_command(f'DESIGNER', params)

    @have_repo_connection
    def update_conf_from_repo(self, version: Optional[int] = None):
        """
        Выполняет обновление конфигурации из хранилища /ConfigurationRepositoryUpdateCfg
        """
        logger.info(
            f'Обновление конфигурации БД из хранилища {self.repo_connection}'
            f'БД по соединению {self.connection}')

        params = self.repo_connection.get_connection_params()
        params.append(f'/ConfigurationRepositoryUpdateCfg')

        cfg_version = -1
        if version is not None:
            cfg_version = version
        params.extend([
            '-v', f'{cfg_version}'
        ])

        self.__execute_command(f'DESIGNER', params)

    @have_repo_connection
    def bind_cfg_to_repo(self):
        """
        Выполняет привязку базы к хранилищу /ConfigurationRepositoryBindCfg
        """
        logger.info(
            f'Привязка базы к хранилищу {self.repo_connection}'
            f'БД по соединению {self.connection}')

        params = self.repo_connection.get_connection_params()
        params.append(f'/ConfigurationRepositoryBindCfg')
        params.append('-forceBindAlreadyBindedUser')
        params.append('-forceReplaceCfg')

        self.__execute_command(f'DESIGNER', params)

    @have_repo_connection
    def get_repo_report(self,
                        report_file: str,
                        v_begin: Optional[int] = None,
                        v_end: Optional[int] = None,
                        group_by_obj: bool = False,
                        group_by_comment: bool = False):

        full_report_file = os.path.abspath(report_file)

        logger.info(
            f'Формирование отчета в файл {full_report_file} из хранилища {self.repo_connection}'
            f'БД по соединению {self.connection}')

        params = self.repo_connection.get_connection_params()
        params.append(f'/ConfigurationRepositoryReport')
        params.append(f'{full_report_file}')

        if v_begin is not None:
            params.extend([
                '-NBegin', f'{v_begin}'
            ])

        if v_begin is not None:
            params.extend([
                '-NEnd', f'{v_end}'
            ])

        if group_by_obj:
            params.append('-GroupByObject')

        if group_by_comment is not None:
            params.append('-GroupByComment')

        self.__execute_command(f'DESIGNER', params)

    def merge_config_with_file(self, cf_file_path: str, settings_path: str) -> None:
        """
        Выполнить объединение текущей конфигурации с файлом (с использованием файла настроек).
        (соответствует команде /MergeCfg)

        :param cf_file_path: str : Путь к файлу cf для объединения с текущей конфой
        :param settings_path: str : Путь к файлу настроек объединения
        :return:
        """
        full_cf_file_path = os.path.abspath(cf_file_path)
        full_path_settings_path = os.path.abspath(settings_path)
        logger.info(
            f'Объединение конфигурации по соединению {self.connection} с файлом {full_cf_file_path} '
            f'по настройкам из файла {full_path_settings_path}')
        params = [
            f'/MergeCfg', f'{full_cf_file_path}',
            f'-Settings', f'{full_path_settings_path}'
        ]
        self.__execute_command(f'DESIGNER', params)

    def compare_config_with_file(self, cf_file_path: str, report_path: str) -> None:
        """
        Выполнить сравнение двух конфигураций и сформировать файл с отчетом о сравнении.
        (соответствует команде /CompareCfg)
        :param cf_file_path: Путь к файлу cf, который необходимо сравнить с конфигурацией.
        :param: report_path: Путь к файлу, в который необходимо сохранить отчет.
        :return:
        """
        full_cf_file_path = os.path.abspath(cf_file_path)
        full_report_path = os.path.abspath(report_path)
        logger.info(
            f'Сравниваю конфигурацию по соединению {self.connection} с файлом {full_cf_file_path} '
            f'для сохранения отчета по пути {full_report_path} ')
        params = [
            '/CompareCfg',
            '-FirstConfigurationType',
            'MainConfiguration',
            '-SecondConfigurationType',
            'File',
            '-SecondFile',
            f'{full_cf_file_path}',
            '-IncludeChangedObjects',
            '-IncludeDeletedObjects',
            '-IncludeAddedObjects',
            '–ReportType',
            'txt',
            '-ReportFormat',
            'Full',
            '-ReportFile',
            f'{full_report_path}'
        ]
        self.__execute_command(f'DESIGNER', params)


def convert_cf_to_xml(
        cf_file_path: str,
        platform_version: str = '',
        out_path: Optional[str] = None,
        temp_path: Optional[str] = None,
        clear_temp_folder: bool = True) -> str:

    def convert_function(designer, full_cf_path, out_path):
        designer.load_config_from_file(full_cf_path)
        designer.dump_config_to_files(out_path)

    return _convert_to_xml(cf_file_path, convert_function, platform_version, out_path, temp_path, clear_temp_folder)


def convert_cfe_to_xml(
        cf_file_path: str,
        platform_version: str = '',
        out_path: Optional[str] = None,
        temp_path: Optional[str] = None,
        clear_temp_folder: bool = True) -> str:

    def convert_function(designer, full_cf_path, out_path):
        designer.load_extension_from_file(full_cf_path)
        designer.dump_extensions_to_files(out_path)

    return _convert_to_xml(cf_file_path, convert_function, platform_version, out_path, temp_path, clear_temp_folder)


def _convert_to_xml(
        file_path: str,
        function: Callable[[Designer, str, str], None],
        platform_version: str = '',
        out_path: Optional[str] = None,
        temp_path: Optional[str] = None,
        clear_temp_folder: bool = True) -> str:

    full_cf_path = os.path.abspath(file_path)

    if out_path is None:
        out_path = os.path.join(
            os.path.basename(full_cf_path),
            'cf'
        )
    if not os.path.exists(out_path):
        os.mkdir(out_path)

    rm_dir = False
    if temp_path is None:
        temp_path = tempfile.mkdtemp()
        rm_dir = True
    _temp_path = os.path.join(temp_path, 'base')
    os.mkdir(_temp_path)

    connection = Connection('', '', _temp_path)
    designer = Designer(platform_version, connection)

    designer.create_base()

    function(designer, full_cf_path, out_path)

    if clear_temp_folder:
        if rm_dir:
            clear_folder(temp_path)
            os.rmdir(temp_path)
        else:
            clear_folder(temp_path)

    return out_path