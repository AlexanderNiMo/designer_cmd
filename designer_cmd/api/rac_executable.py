import logging
from designer_cmd.utils import PlatformVersion, get_rac_path, execute_command
from typing import List, Dict, Optional
from abc import ABC


logger = logging.getLogger(__name__)


class RacConnection:

    def __init__(self, user: str = '',
                 password: str = '',
                 server: str = '',
                 port: int = 1545):
        self.server = server
        self.port = port
        self.user = user
        self.password = password

    def get_connection_string(self):
        return f'{self.server}:{self.port}'

    def get_credentials(self):
        cred = []
        if self.user:
            cred.append(f'--infobase-user={self.user}')
        if self.password:
            cred.append(f'--infobase-pwd={self.password}')

        return cred


def parse_result(result_str: str) -> List[Dict[str, str]]:
    result = []

    try:
        b_data = result_str.encode('cp866')
        result_str = b_data.decode('utf-8')
    except UnicodeEncodeError:
        pass

    data = result_str.split('\n')
    cur_result = {}
    for el in data:
        if el == '':
            if cur_result:
                result.append(cur_result)
            cur_result = {}
            continue

        key_val = el.split(':')
        if len(key_val) < 2:
            raise ValueError('Ошибка разбора результата ответа')
        key = key_val[0].strip()
        val = ':'.join(key_val[1:]).strip()
        cur_result[key] = val
    if cur_result:
        result.append(cur_result)
    return result


def required_cluster_id(func):

    def warper(self: "ABCRacMod", *args, **kwargs):
        if self.executor.custer_id is None:
            self.executor.set_cluster_id()
        return func(self, *args, **kwargs)

    return warper


def required_base_id(func):

    def warper(self: "ABCRacMod", *args, **kwargs):
        if self.executor.base_id is None:
            raise AttributeError('base_id not set')
        return func(self, *args, **kwargs)

    return warper


class Rac:

    def __init__(self, platform_version: str, connection: RacConnection):
        self.platform_version: PlatformVersion = PlatformVersion(platform_version)
        self.connection = connection
        self.executable_path = get_rac_path(self.platform_version)

        self._cluster_id = None
        self._base_id = None

        self.infobase = InfobaseMod(self)
        self.cluster = ClusterMod(self)
        self.sessions = SessionMod(self)

    def add_cluster_id(self, params: list, cluster_id: Optional[str] = None):
        if not cluster_id:
            cluster_id = self._cluster_id
        if not cluster_id:
            raise ValueError('Cluster_id не установлен!')
        params.append(f'--cluster={cluster_id}')

    def add_base_id(self, params: list, base_id: Optional[str] = None):
        if not base_id:
            base_id = self._base_id
        if not base_id:
            raise ValueError('base_id не установлен!')
        params.append(f'--infobase={base_id}')

    @property
    def custer_id(self):
        return self._cluster_id

    def set_cluster_id(self, cluster_id: str = None):
        if not cluster_id:
            cluster_data = self.cluster.get_cluster_data()
            cluster_id = cluster_data.get('cluster')
        self._cluster_id = cluster_id

    @property
    def base_id(self) -> str:
        return self._base_id

    @base_id.setter
    def base_id(self, value: str):
        self._base_id = value

    def execute_command(self, mode: str, command_params: list) -> List[Dict[str, str]]:
        params = [self.connection.get_connection_string(), mode]

        params += self.connection.get_credentials()

        params += command_params

        str_command = ' '.join(params)

        logger.debug(f'Выполняю команду {self.executable_path} {str_command}')

        result = execute_command(self.executable_path, params, 10)

        if result[0] == 0:
            result_data = parse_result(result[1])
        else:
            raise SyntaxError(f'Не удалось выполнить команду! подробно: {result[1]}')
        return result_data

    def disconnect_users(self, base_ref: str):
        base_data = self.infobase.get_base_by_ref(base_ref)
        base_id = base_data.get('infobase')
        self.base_id = base_id

        session_list = self.sessions.get_session_list()
        for session in session_list:
            self.sessions.terminate_session(session.get('session'))


class ABCRacMod(ABC):

    def __init__(self, executor: Rac, mod: str):
        self.executor = executor
        self.mod = mod

    def execute_command(self, command_params: list) -> List[Dict[str, str]]:
        return self.executor.execute_command(self.mod, command_params)


class InfobaseMod(ABCRacMod):

    def __init__(self, executor: Rac):
        super(InfobaseMod, self).__init__(executor, 'infobase')

    def execute_command(self, command_params: list,
                        base_id_required: bool = True,
                        cluster_id_required: bool = True) -> List[Dict[str, str]]:
        if base_id_required:
            self.executor.add_base_id(command_params)
        if cluster_id_required:
            self.executor.add_cluster_id(command_params)
        return super(InfobaseMod, self).execute_command(command_params)

    @required_cluster_id
    def get_base_list(self):
        logger.debug(f'Получаю список кластеров по соединению {self.executor.connection}')

        params = ['summary', 'list']

        return self.execute_command(params, base_id_required=False)

    @required_cluster_id
    def get_base_by_ref(self, base_ref: str) -> Dict[str, str]:
        logger.debug(f'Ищу базу по имени {base_ref} по соединению {self.executor.connection}')

        base_list = self.get_base_list()
        try:
            base_data = next(filter(lambda x: x.get('name') == base_ref, base_list))
        except StopIteration:
            raise ValueError(f'Нет базы с ref {base_ref}')
        return base_data

    @required_cluster_id
    @required_base_id
    def deny_sessions(self, permission_code: Optional[str] = None):
        logger.debug(f'Запрещаю соединение с базой {self.executor.base_id} по соединению {self.executor.connection}')

        params = ['update', '--sessions-deny=on']
        if permission_code:
            params.append(f'--permission-code={permission_code}')
        self.execute_command(params)

    @required_cluster_id
    @required_base_id
    def allow_sessions(self):
        logger.debug(f'Разрешаю соединение с базой {self.executor.base_id} по соединению {self.executor.connection}')

        params = ['update', '--sessions-deny=off']
        self.execute_command(params)

    @required_cluster_id
    @required_base_id
    def deny_scheduled_jobs(self):
        logger.debug(f'Запрещаю работу регл. задач в базе {self.executor.base_id} '
                     f'по соединению {self.executor.connection}')

        params = ['update', '--scheduled-jobs-deny=on']
        self.execute_command(params)

    @required_cluster_id
    @required_base_id
    def allow_scheduled_jobs(self):
        logger.debug(f'Разрешаю работу регл. задач в базе {self.executor.base_id} '
                     f'по соединению {self.executor.connection}')

        params = ['update', '--scheduled-jobs-deny=off']
        self.execute_command(params)


class ClusterMod(ABCRacMod):

    def __init__(self, executor: Rac):
        super(ClusterMod, self).__init__(executor=executor, mod='cluster')

    def execute_command(self, command_params: list, cluster_id_required: bool = True) -> List[Dict[str, str]]:
        if cluster_id_required:
            self.executor.add_cluster_id(command_params)
        return super(ClusterMod, self).execute_command(command_params)

    def get_cluster_list(self):
        logger.debug(f'Получаю список кластеров по соединению {self.executor.connection}')

        params = ['list']
        return self.execute_command(params, cluster_id_required=False)

    def get_cluster_data(self, cluster_id: str = None) -> dict:

        if cluster_id:
            params = ['info']
            self.executor.add_cluster_id(params, cluster_id)
            cluster_list = self.execute_command(params, cluster_id_required=False)
        else:
            cluster_list = self.get_cluster_list()

        if not cluster_list:
            raise ValueError(f'Не обнаруженно ни одного кластера!')

        return cluster_list[0]


class SessionMod(ABCRacMod):

    def __init__(self, executor: Rac):
        super(SessionMod, self).__init__(executor=executor, mod='session')

    def execute_command(self, command_params: list,
                        cluster_id_required: bool = True) -> List[Dict[str, str]]:
        if cluster_id_required:
            self.executor.add_cluster_id(command_params)
        return super(SessionMod, self).execute_command(command_params)

    @required_cluster_id
    def get_session_list(self, base_id: Optional[str] = None):
        logger.debug(f'Получаю список активных сессий в базе {base_id}')

        params = ['list']

        self.executor.add_base_id(params, base_id)

        return self.execute_command(params)

    @required_cluster_id
    def session_info(self, session_id: str):
        logger.debug(f'Получаю информацию о сессии {session_id}')

        params = ['info', f'--session={session_id}']

        return self.execute_command(params)

    @required_cluster_id
    def terminate_session(self, session_id: str, msg: Optional[str] = None):
        logger.debug(f'Удаление сеанса по id {session_id}')

        params = ['terminate', f'--session={session_id}']

        if msg:
            params.append(f'--error-message={msg}')

        return self.execute_command(params)
