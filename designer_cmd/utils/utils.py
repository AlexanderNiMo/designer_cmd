import logging
import sys
import os.path as path
import os
import subprocess

logger = logging.getLogger(__file__)


def windows_platform() -> bool:
    return 'win' in sys.platform


def get_platform_path(version: str = '') -> str:
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


def __get_version_path(dir_1c, version) -> str:
    bin_path = 'bin\\1cv8.exe'
    exept_dir = ['common', 'conf']

    versions = [dir_name for dir_name in os.listdir(dir_1c) if dir_name not in exept_dir]

    if len(versions) == 0:
        return ''

    if version == '':
        # Получим максимальную версию
        return path.join(dir_1c, sorted(versions, key=get_version_weight, reverse=True)[0], bin_path)
    elif version in versions:
        return path.join(dir_1c, version, bin_path)
    else:
        return ''


def get_version_weight(element: str) -> int:
    """
    Вычисляет вес версии, для сравнения версий
    Подразумевается, что версии, для которых будет вычисляться октавы имеют одинаковые длины октавово
    и их длина не больше 4

    :param element:
    :return:
    """
    octs_first = element.split('.')
    octs_first.reverse()
    koef = 1000
    summ = 0
    for i, val in enumerate(octs_first):
        if len(val) > 4:
            logger.error(f'Длина октава {val} в версии {element} больше 4, вычисление веса не поддерживается.')
            raise ValueError('Ошибка вычисления веса версии, длинна октава не должна быть больше 4.')
        summ += int(val) * koef ** i
    return summ


def __get_platform_path_windows(version: str) -> str:
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


def __get_platform_path_linux(version: str) -> str:
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
