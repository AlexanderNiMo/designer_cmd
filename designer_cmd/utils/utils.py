import logging
import sys
import os.path as path
import os
import subprocess
from functools import total_ordering
import shutil

logger = logging.getLogger(__file__)


@total_ordering
class PlatformVersion:

    def __init__(self, version: str):
        self.version: str = version
        if self.version != '':
            version_weight = self.__get_version_weight()
        else:
            version_weight = 9999999999
        self.__version_weight: int = version_weight

    @property
    def version_weight(self) -> int:
        return self.__version_weight

    def __get_version_weight(self) -> int:
        """
        Вычисляет вес версии, для сравнения версий
        Подразумевается, что версии, для которых будет вычисляться октавы имеют одинаковые длины октавово
        и их длина не больше 4

        :param element:
        :return:
        """
        octs_first = self.version.split('.')

        while len(octs_first) < 4:
            octs_first.append('0')

        if len(octs_first) > 4:
            raise ValueError(f'Версия платформы имеет 4 октава, передано значение {octs_first}')

        octs_first.reverse()
        koef = 1000
        summ = 0
        for i, val in enumerate(octs_first):
            if len(val) > 4:
                logger.error(f'Длина октава {val} в версии {self.version} больше 4, вычисление веса не поддерживается.')
                raise ValueError('Ошибка вычисления веса версии, длинна октава не должна быть больше 4.')
            summ += int(val) * koef ** i
        return summ

    def __str__(self):
        return self.version

    def __repr__(self):
        return self.version

    def _is_valid_operand(self, other):
        return hasattr(other, "version_weight")

    def __eq__(self, other):
        if not self._is_valid_operand(other):
            return NotImplemented
        return self.version_weight == other.version_weight

    def __lt__(self, other):
        if not self._is_valid_operand(other):
            return NotImplemented
        return self.version_weight < other.version_weight


def windows_platform() -> bool:
    return 'win' in sys.platform


def get_platform_path(version: PlatformVersion) -> str:
    """
    Вычисляет путь к исполняемому файлу платформы

    :param version: Версия платформы.
    :return:
    """

    if windows_platform():
        platform_path = __get_platform_path_windows(version)
    else:
        platform_path = __get_platform_path_linux(version)

    return platform_path


def __get_version_path(dir_1c, version: PlatformVersion) -> str:
    bin_path = 'bin\\1cv8.exe'
    exept_dir = ['common', 'conf']

    versions = [PlatformVersion(dir_name) for dir_name in os.listdir(dir_1c) if dir_name not in exept_dir]

    if len(versions) == 0:
        return ''

    if version.version == '':
        # Получим максимальную версию
        return path.join(dir_1c, sorted(versions, key=lambda v: v.version_weight, reverse=True)[0].version, bin_path)
    elif version in versions:
        return path.join(dir_1c, version.version, bin_path)
    else:
        return ''


def __get_platform_path_windows(version: PlatformVersion) -> str:
    version_path = __get_version_path(path.join(os.getenv('ProgramW6432'), '1cv8'), version)

    if version_path == '':
        version_path = __get_version_path(path.join(os.getenv('ProgramFiles'), '1cv8'), version)

    if version_path == '':
        if version == '':
            logger.critical('Не обнаружена установленная 1с. Выполнение невозможно.')
            raise EnvironmentError('Не обнаружена установленная 1с.')
        else:
            logger.critical(f'Не обнаружена установленная версия 1с номер версии:{version}. Выполнение невозможно.')
            raise EnvironmentError(f'Не обнаружена версия {version} 1с.')

    return version_path


def __get_platform_path_linux(version: PlatformVersion) -> str:
    platform_path = ''

    return platform_path


def execute_command(command: str, params: list, timeout: int = None) -> tuple:
    """
    Выполняет команду в системе.

    :param command: Команда
    :param params: Параметры команды
    :param timeout: Лимит времени на выполнение команды, после выхода за пределы будет возбуждено исключение.
    :return:
    """
    if windows_platform():
        result = __execute_windows_command(command, params, timeout)
    else:
        result = __execute_linux_command(command, params, timeout)
    return result


def __execute_windows_command(command: str, params: list, timeout: int) -> tuple:
    """
    Выполняет команду системы в windows

    :param command:
    :return:
    """
    try:
        process = subprocess.run(
            args=[command] + params,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True,
            encoding=encoding(),
            timeout=timeout
        )
        if process.returncode == 0:
            msg = process.stdout
        else:
            msg = process.stderr
        return process.returncode, msg.strip()
    except subprocess.TimeoutExpired:
        return 1, 'Выполнение процесса вышло за рамки отведенного времени.'
    except subprocess.CalledProcessError as e:
        return 1, f'Ошибка выполнения команды {e}'


def encoding() -> str:
    """
    Определяет кодировку в контексте системы.
        Спасибо (@vbondarevsky)
    :return:
    """
    if windows_platform():
        import ctypes
        return f"cp{ctypes.windll.kernel32.GetOEMCP()}"
    else:
        return (sys.stdout.encoding if sys.stdout.isatty() else
                sys.stderr.encoding if sys.stderr.isatty() else
                sys.getfilesystemencoding() or "utf-8")


def __execute_linux_command(command: str, params: list, timeout: int) -> str:
    """
    Выполняет команду системы в linux

    :param command:
    :return:
    """
    raise NotImplementedError('Не реализовано!')
    pass


def xml_conf_version_file_exists(dir_path: str):
    version_file_name = "ConfigDumpInfo.xml"
    test_path = os.path.join(dir_path, version_file_name)
    return os.path.exists(test_path)


def clear_folder(dir_path):
    if path.exists(dir_path):
        filelist = [f for f in os.listdir(dir_path)]
        for file_name in filelist:
            if '.gitkeep' in file_name:
                continue
            file_path = path.join(dir_path, file_name)
            if path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)