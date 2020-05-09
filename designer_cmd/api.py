from designer_cmd.utils import get_platform_path, execute_command
import os
import logging

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


class Designer:

    def __init__(self, platform_version: str, connection):

        self.platform_version = platform_version
        self.connection = connection
        self.platform_path = get_platform_path(self.platform_version)

    def __execute_command(self, command_params: list, connection_params_required: bool = True):
        params = []
        params += command_params
        if connection_params_required:
            params += self.connection.get_connection_params()
        params += ['/DisableStartupDialogs /DisableStartupMessages']
        str_command = ' '.join(params)
        logger.debug(f'Выполня команду {str_command}')
        result = execute_command(self.platform_path, params)

        if result[0] != 0:
            raise SyntaxError('Не удалось выполнить команду!')

    def create_base(self):
        """
        Создает базу данных.
        Соответствует режиму CREATEINFOBASE <строка соединения>

        """
        params = [f'CREATEINFOBASE', f'{self.connection.get_connection_string()}']
        self.__execute_command(params, False)

    def updete_db_config(self, dynamic: bool = False, warnings_as_errors: bool = False):
        """
        Обновляет конфигурацию db. (соответствует команде /UpdateDBCfg)

        :return:
        """
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
        params = [f'DESIGNER', f'/LoadConfigFromFiles {os.path.abspath(catalog_path)}']
        self.__execute_command(params)

    def dump_config_to_files(self, catalog_path: str) -> None:
        """
        Выгружает конфигурацию в файлы (соответствует команде /DumpConfigToFiles)

        :param catalog_path: Каталог в который будет выгружен файл
        :return:
        """
        params = [f'DESIGNER', f'/DumpConfigToFiles {os.path.abspath(catalog_path)}']
        self.__execute_command(params)

    def load_config_from_file(self, file_path: str) -> None:
        """
        Загружает конфигурацию в базу из файла cf (соответствует команде /LoadCfg)

        :param file_path:
        :return:
        """
        params = [f'DESIGNER', f'/LoadCfg {os.path.abspath(file_path)}']
        self.__execute_command(params)

    def dump_config_to_file(self, file_path: str) -> None:
        """
        Выполнить сохранение конфигурации в файл cf (соответствует команде /DumpCfg)
        :param file_path:
        :return:
        """
        params = [f'DESIGNER', f'/DumpCfg {os.path.abspath(file_path)}']
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

    def compare_configs_with_file(self, cf_file_path: str, report_path: str) -> None:
        """
        Выполнить сравнение двух конфигураций и сформировать файл с отчетом о сравнении.
        (соответствует команде /CompareCfg)
        :param cf_file_path: Путь к файлу cf, который необходимо сравнить с конфигурацией.
        :param: report_path: Путь к файлу, в который необходимо сохранить отчет.
        :return:
        """

        params = [
            f'/CompareCfg',
            f'–FirstConfigurationType MainConfiguration',
            f'-SecondConfigurationType {cf_file_path}',
            f'–ReportType Full',
            f'-ReportFormat txt',
            f'-ReportFile {report_path}'
      ]
        self.__execute_command(params)
