from designer_cmd.utils import get_platform_path, execute_command
import os
import logging
import tempfile

logger = logging.getLogger(__file__)


class Connection:
    """
    Описывает соединение с базой
    """
    def __init__(self, user: str= '',
                 password: str = '',
                 file_path: str = '',
                 server_path: str = '',
                 server_base_ref: str = '',
                 ib_name: str = ''):

        if file_path == '' and (server_path == '' or server_base_ref == '') and ib_name == '':
            raise AttributeError('Для соедеинения не определен путь к базе!')

        self.user = user
        self.password = password

        self.ib_name = ib_name

        self.file_path = os.path.abspath(file_path) if file_path != '' else ''
        self.server_path = server_path
        self.server_base_ref = server_base_ref

    def get_connection_params(self) -> list:
        """
        Возвращает строковое представление параметров для подключения по текущему описанию соединения

        :return: str : Текстовые параметры для командной строки
        """
        params = []
        if self.file_path != '':
            params += [f'/F {self.file_path}']
        elif self.ib_name != '':
            params += [f'/IBName {self.ib_name}']
        else:
            params += [f'/S {self.server_path}\\{self.server_base_ref}']

        if self.user != '':
            params.append(f'/N {self.user}')
            params.append(f'/P {self.password}')

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


class Designer:

    def __init__(self, platform_version: str, connection: Connection):

        self.platform_version = platform_version
        self.connection = connection
        self.platform_path = get_platform_path(self.platform_version)

    def __execute_command(self, command_params: list, connection_params_required: bool = True):
        params = []
        params += command_params
        if connection_params_required:
            params += self.connection.get_connection_params()
        params += ['/DisableStartupDialogs /DisableStartupMessages']

        debug_file_name = self.add_debug_params(params)

        str_command = ' '.join(params)
        logger.debug(f'Выполняю команду {self.platform_path} {str_command}')
        result = execute_command(self.platform_path, params)

        if result[0] != 0:
            logger.error(f'При выполнении команды произошла ошибка: {open(debug_file_name).read()}')
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
        params = [f'CREATEINFOBASE', f'{self.connection.get_connection_string()}']
        self.__execute_command(params, False)

    def updete_db_config(self, dynamic: bool = False, warnings_as_errors: bool = False):
        """
        Обновляет конфигурацию db. (соответствует команде /UpdateDBCfg)

        :return:
        """
        logger.info(f'Обновляю конфигурацию БД по соединению {self.connection}')
        params = [f'DESIGNER', f'/UpdateDBCfg']
        self.__execute_command(params)

    def load_db_from_file(self, file_path: str) -> None:
        """
        Загрузка базы из файла dt (соответствует команде /RestoreIB)

        :param file_path: str - Путь к файлу базы (dt.)
        :return:
        """
        raise NotImplementedError

    def dump_db_to_file(self, file_path: str) -> None:
        """
        Выгрузка базы в файл (соответствует команде /DumpIB)

        :param file_path: str - Путь к файлу для выгрзки базы (dt.)
        :return:
        """
        raise NotImplementedError

    def load_config_from_files(self, catalog_path: str) -> None:
        """
        Загружает конфигурацию из файлов (соответствует команде /LoadConfigFromFiles)

        :param catalog_path: str - путь к каталогу из которого необходимо произвести загрузку.
        :return:
        """
        full_catalog_path = os.path.abspath(catalog_path)
        logger.info(f'Загружаю конфигурацию из файлов {full_catalog_path} конфигурацию БД по соединению {self.connection}')
        params = [f'DESIGNER', f'/LoadConfigFromFiles {full_catalog_path}']
        self.__execute_command(params)

    def dump_config_to_files(self, catalog_path: str) -> None:
        """
        Выгружает конфигурацию в файлы (соответствует команде /DumpConfigToFiles)

        :param catalog_path: Каталог в который будет выгружен файл
        :return:
        """
        full_catalog_path = os.path.abspath(catalog_path)
        logger.info(
            f'Выгружаю конфигурацию в файлы {full_catalog_path} по соединению {self.connection}')
        params = [f'DESIGNER', f'/DumpConfigToFiles {full_catalog_path}']
        self.__execute_command(params)

    def load_config_from_file(self, file_path: str) -> None:
        """
        Загружает конфигурацию в базу из файла cf (соответствует команде /LoadCfg)

        :param file_path:
        :return:
        """
        full_file_path = os.path.abspath(file_path)
        logger.info(
            f'Загружаю конфигурацию из файла {full_file_path} в конфигурацию БД по соединению {self.connection}')
        params = [f'DESIGNER', f'/LoadCfg {full_file_path}']
        self.__execute_command(params)

    def dump_config_to_file(self, file_path: str) -> None:
        """
        Выполнить сохранение конфигурации в файл cf (соответствует команде /DumpCfg)
        :param file_path:
        :return:
        """
        full_file_path = os.path.abspath(file_path)
        logger.info(
            f'Сохраняю конфигурацию в файл {full_file_path} из конфигурации БД по соединению {self.connection}')
        params = [f'DESIGNER', f'/DumpCfg {full_file_path}']
        self.__execute_command(params)

    def merge_config_with_file(self, cf_file_path: str, settings_path: str) -> None:
        """
        Выполнить объединение текущей конфигурации с файлом (с использованием файла настроек).
        (соответствует команде /MergeCfg)

        :param cf_file_path: str : Путь к файлу cf для объединения с текущей конфой
        :param settings_path: str : Путь к файлу настроек объединения
        :return:
        """
        raise NotImplementedError

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
            'DESIGNER',
            '/CompareCfg',
            '-FirstConfigurationType',
            'MainConfiguration',
            '-SecondConfigurationType',
            'File',
            '-SecondFile',
            f'{full_cf_file_path}',
            '–ReportType',
            'txt',
            '-ReportFormat',
            'Full',
            '-ReportFile',
            f'{full_report_path}'
      ]
        self.__execute_command(params)
