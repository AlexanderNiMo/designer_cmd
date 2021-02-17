import logging
import sys
import os.path as path
import os
import subprocess
from functools import total_ordering
import shutil
from ctypes import windll
from typing import List
import signal
import dataclasses


logger = logging.getLogger(__name__)


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


@dataclasses.dataclass
class Process:
    cmd: str
    pid: int

    def kill(self):
        kill_process(self.pid)


def kill_process(pid: int):
    if windows_platform():
        __kill_process_windows(pid)
    else:
        __kill_process_linux(pid)


def __kill_process_windows(pid: int):
    os.kill(pid, signal.SIGBREAK)


def __kill_process_linux(pid: int):
    raise NotImplementedError


def windows_platform() -> bool:
    return 'win' in sys.platform


def get_1c_exe_path(version: PlatformVersion) -> str:
    """
    Вычисляет путь к исполняемому файлу платформы

    :param version: Версия платформы.
    :return:
    """

    if windows_platform():
        platform_path = __get_1c_executable_path_windows(version, path.join('bin', '1cv8.exe'))
    else:
        platform_path = __get_1c_executable_path_linux(version, '')

    return platform_path


def get_rac_path(version: PlatformVersion) -> str:
    """
    Вычисляет путь к исполняемому файлу rac

    :param version: Версия платформы.
    :return:
    """

    if windows_platform():
        rac_path = __get_1c_executable_path_windows(version, path.join('bin', 'rac.exe'))
    else:
        rac_path = __get_1c_executable_path_linux(version, '')

    return rac_path


def __get_1c_executable_path_windows(version: PlatformVersion, bin_path: str) -> str:
    version_path = __get_version_path(path.join(os.getenv('ProgramW6432'), '1cv8'), version, bin_path)

    if version_path == '':
        version_path = __get_version_path(path.join(os.getenv('ProgramFiles'), '1cv8'), version, bin_path)

    if version_path == '':
        if version == '':
            logger.critical('Не обнаружена установленная 1с. Выполнение невозможно.')
            raise EnvironmentError('Не обнаружена установленная 1с.')
        else:
            logger.critical(f'Не обнаружена установленная версия 1с номер версии:{version}. Выполнение невозможно.')
            raise EnvironmentError(f'Не обнаружена версия {version} 1с.')

    return version_path


def __get_1c_executable_path_linux(version: PlatformVersion, bin_path: str) -> str:
    platform_path = ''

    return platform_path


def __get_version_path(dir_1c, version: PlatformVersion, bin_path) -> str:
    versions = [PlatformVersion(dir_name) for dir_name in os.listdir(dir_1c) if __is_platform_dir(dir_name)]

    if len(versions) == 0:
        return ''

    if version.version == '':
        # Получим максимальную версию
        return path.join(dir_1c, sorted(versions, key=lambda v: v.version_weight, reverse=True)[0].version, bin_path)
    elif version in versions:
        return path.join(dir_1c, version.version, bin_path)
    else:
        return ''


def __is_platform_dir(dir_name: str) -> bool:
    exept_dir = ['common', 'conf']
    if dir_name in exept_dir:
        return False

    octs_first = dir_name.split('.')

    if len(octs_first) > 4:
        return False

    for oct in octs_first:
        if not oct.isnumeric():
            return False
        if len(oct) > 4:
            return False

    return True


def execute_command(command: str, params: list, timeout: int = None, wait: bool = True) -> tuple:
    """
    Выполняет команду в системе.

    :param command: Команда
    :param params: Параметры команды
    :param timeout: Лимит времени на выполнение команды, после выхода за пределы будет возбуждено исключение.
    :return:
    """
    if windows_platform():
        result = __execute_windows_command(command, params, timeout, wait)
    else:
        result = __execute_linux_command(command, params, timeout, wait)
    return result


def __execute_windows_command(command: str, params: list, timeout: int, wait: bool = True) -> tuple:
    if wait:
        return __execute_windows_command_wait(command, params, timeout)
    else:
        return __execute_windows_command_no_wait(command, params)


def __execute_windows_command_wait(command: str, params: list, timeout: int) -> tuple:
    """
        Выполняет команду системы в windows с ожиданием выполнения

        :param command:
        :return:
        """
    prev_codepage = windll.kernel32.GetConsoleOutputCP()
    windll.kernel32.SetConsoleOutputCP(65001)
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
    finally:
        windll.kernel32.SetConsoleOutputCP(prev_codepage)


def __execute_windows_command_no_wait(command: str, params: list) -> tuple:
    """
        Выполняет команду системы в windows без ожидания выполнения

        :param command:
        :return:
        """
    prev_codepage = windll.kernel32.GetConsoleOutputCP()
    windll.kernel32.SetConsoleOutputCP(65001)

    try:
        process = subprocess.Popen(
            args=[command] + params,
            encoding=encoding(),
            close_fds=True
        )
        return 0, ''
    except subprocess.CalledProcessError as e:
        return 1, f'Ошибка выполнения команды {e}'
    finally:
        windll.kernel32.SetConsoleOutputCP(prev_codepage)


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


def __execute_linux_command(command: str, params: list, timeout: int, wait: bool = True) -> str:
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


def port_in_use(port):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def get_1c_processes() -> List[Process]:
    result = None
    if windows_platform():
        result = _get_1c_processes_windows()
    else:
        result = _get_1c_processes_linux()
    return result


def _get_1c_processes_windows() -> List[Process]:
    result = subprocess.run(
        [
            'wmic', 'process', 'where',
            "description='1cv8.exe' OR description='1cv8c.exe'",
            'list', 'full', '/format'
        ],
        stdout=subprocess.PIPE
    )
    return parse_wmic_data(result.stdout.decode('cp866'))


def parse_wmic_data(data: str) -> List[Process]:
    lines = data.split('\r\r\n')
    procs = []
    proc = {}
    for line in lines:
        if line == '':
            if proc:
                p = Process(cmd=proc.get('CommandLine'), pid=int(proc.get('ProcessId')))
                procs.append(p)
                proc = {}
            continue
        line_data = line.split('=')
        proc[line_data[0]] = line_data[1]
    return procs


def _get_1c_processes_linux() -> List[Process]:
    raise NotImplementedError