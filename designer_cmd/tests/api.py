from designer_cmd.api import Connection, Designer, RepositoryConnection, convert_cf_to_xml
import unittest
import os.path as path
import os
from designer_cmd.utils.utils import clear_folder


class TestConnection(unittest.TestCase):

    def setUp(self):
        pass

    def test_init_base_path(self):
        with self.assertRaises(AttributeError) as cm:
            con = Connection(user='user')
        the_exception = cm.exception
        self.assertEqual(
            the_exception.args[0],
            'Для соедеинения не определен путь к базе!',
            'Полученно неожиданное исключение'
        )

    def test_get_connection_params_file(self):

        loc_path = 'path'

        con = Connection(user='user', password='pass', file_path=loc_path)
        self.assertEqual(
            con.get_connection_params(),
            [f'/F', f'{path.abspath(loc_path)}', '/N', f'user', '/P', f'pass'],
            'Не верно определена строка подключени для файловой базы'
        )

    def test_get_connection_params_server(self):

        con = Connection(user='user', password='pass', server_path='192.168.1.1', server_base_ref='test')
        self.assertEqual(
            con.get_connection_params(),
            ['/S', '192.168.1.1\\test', '/N', 'user', '/P', 'pass'],
            'Не верно определена строка подключени для серверной базы'
        )

    def test_get_connection_string_file(self):

        loc_path = 'path'

        con = Connection(user='user', password='pass', file_path=loc_path)
        self.assertEqual(
            con.get_connection_string(),
            f'Usr=user Pwd=pass File={path.abspath(loc_path)}',
            'Не верно определена строка подключени для файловой базы'
        )


class TestDesigner(unittest.TestCase):

    def setUp(self):
        test_data_dir = path.join(path.dirname(__file__), 'test_data')

        self.temp_path = path.join(test_data_dir, 'temp')
        self.test_base_path = path.join(test_data_dir, 'base')
        self.cf_path = path.join(test_data_dir, '1Cv8.cf')
        self.dt_path = path.join(test_data_dir, '1Cv8.dt')
        self.cf_increment_path = path.join(test_data_dir, '1Cv8_increment.cf')

        self.cfe_path1 = path.join(test_data_dir, 'test.cfe')
        self.cfe_path2 = path.join(test_data_dir, 'test2.cfe')

        self.repo_obj_list = path.join(test_data_dir, 'obj_list')
        self.repo_obj_list_all = path.join(test_data_dir, 'obj_list_all_objects')
        self.merge_settings = path.join(test_data_dir, 'MergeSettings.xml')

        self.conn = self.db_connection()
        self.designer = Designer('', self.conn)

        clear_folder(self.test_base_path)
        clear_folder(self.temp_path)

    def db_connection(self):
        return Connection(file_path=self.test_base_path)

    def prepare_base(self):
        self.designer.create_base()
        self.designer.load_config_from_file(self.cf_path)
        self.designer.update_db_config()

    def prepare_repo(self) -> str:
        self.designer.create_base()
        repo_path = path.join(self.temp_path, 'repo')
        if not path.exists(repo_path):
            os.mkdir(repo_path)
        clear_folder(repo_path)
        self.designer.repo_connection = RepositoryConnection(repo_path, 'user', 'password')
        self.designer.create_repository()

        return repo_path

    def test_load_create_db(self):
        self.designer.create_base()

    def test_load_conf_from_file(self):
        self.prepare_base()

    def test_update_cfg(self):
        self.designer.create_base()
        self.designer.load_config_from_file(self.cf_path)
        self.designer.update_db_config()

    def test_dump_conf_to_file(self):
        self.prepare_base()
        cf_file_path = path.join(self.temp_path, '1Cv81.cf')
        self.designer.dump_config_to_file(cf_file_path)

        self.assertTrue(os.path.exists(cf_file_path), 'Выгрузка кофигурации не создана!')

    def test_dump_config_to_files(self):
        self.prepare_base()
        dir_xml_config_path = path.join(self.temp_path, 'xml_config')
        if not path.exists(dir_xml_config_path):
            os.mkdir(dir_xml_config_path)
        self.designer.dump_config_to_files(dir_xml_config_path)

        self.assertTrue(
            os.path.exists(os.path.join(dir_xml_config_path, 'Catalogs\\Справочник1.xml')),
            'Не обнаружена выгрузка в xml'
        )

    def test_dump_config_to_file_increment(self):
        self.prepare_base()

        dir_xml_config_path = path.join(self.temp_path, 'xml_config')
        if not path.exists(dir_xml_config_path):
            os.mkdir(dir_xml_config_path)
        self.designer.dump_config_to_files(dir_xml_config_path)

        cur_catalog_file_time = os.path.getatime(os.path.join(dir_xml_config_path, 'Catalogs\\Справочник1.xml'))

        self.designer.load_config_from_file(self.cf_path)
        self.designer.update_db_config()
        self.designer.dump_config_to_files(dir_xml_config_path)

        self.assertTrue(
            os.path.exists(os.path.join(dir_xml_config_path, 'Catalogs\\Справочник2.xml')),
            'Выгрузка не была выполнена.'
        )

        self.assertEqual(
            cur_catalog_file_time,
            os.path.getatime(os.path.join(dir_xml_config_path, 'Catalogs\\Справочник1.xml')),
            'Выгрузка не была инкриментальной'
        )

    def test_dump_extension_to_file(self):
        self.designer.create_base()
        self.designer.load_db_from_file(self.dt_path)

        cf_file_path = path.join(self.temp_path, 'test_.cfe')
        self.designer.dump_extension_to_file(cf_file_path, 'test')

        self.assertTrue(
            os.path.exists(cf_file_path),
            'Не обнаружена выгрузка расширения'
        )

    def export_all_extension(self):
        cfe_dir_path = path.join(self.temp_path, 'cfe_dir')
        if not path.exists(cfe_dir_path):
            os.mkdir(cfe_dir_path)
        clear_folder(cfe_dir_path)

        self.designer.dump_extensions_to_files(cfe_dir_path)

        return cfe_dir_path

    def test_dump_extensions_to_files(self):
        self.designer.create_base()
        self.designer.load_db_from_file(self.dt_path)

        cfe_dir_path = self.export_all_extension()

        self.assertTrue(
            os.path.exists(os.path.join(cfe_dir_path, 'test')),
            'Выгрузка не сформирована.'
        )

        self.assertTrue(
            os.path.exists(os.path.join(cfe_dir_path, 'test2')),
            'Выгрузка не сформирована.'
        )

    def test_load_extension(self):
        self.prepare_base()
        self.designer.load_extension_from_file(self.cfe_path1, 'test')
        self.designer.load_extension_from_file(self.cfe_path2, 'test2')

        cfe_dir_path = self.export_all_extension()

        self.assertTrue(
            os.path.exists(os.path.join(cfe_dir_path, 'test')),
            'Отсутствует расширение test.'
        )

        self.assertTrue(
            os.path.exists(os.path.join(cfe_dir_path, 'test2')),
            'Отсутствует расширение test2.'
        )

    def test_load_extension_from_files(self):
        self.designer.create_base()
        self.designer.load_db_from_file(self.dt_path)

        cfe_dir_path = path.join(self.temp_path, 'cfe_dir', 'test')
        self.designer.dump_extension_to_files(cfe_dir_path, 'test')

        self.assertTrue(
            os.path.exists(cfe_dir_path),
            'Выгрузка не сформирована.'
        )

        self.designer.load_extension_from_files(cfe_dir_path, 'test')

    def test_add_repository(self):
        repo_path = self.prepare_repo()
        self.assertTrue(os.path.exists(os.path.join(repo_path, 'cache')), 'Хранилище не создано.')

    def test_add_user_to_repo(self):
        self.prepare_repo()
        self.designer.add_user_to_repository('user1', 'password1', rights='LockObjects')

    def test_lock_obj_in_repository(self):
        self.prepare_repo()
        self.designer.lock_objects_in_repository(self.repo_obj_list_all, True)

    def test_unlock_obj_in_repository(self):
        self.prepare_repo()
        self.designer.unlock_objects_in_repository(self.repo_obj_list_all)

    def test_commit_repo(self):

        comment = 'test_test_test_1_2_3_4_5'

        self.prepare_repo()
        self.designer.lock_objects_in_repository(self.repo_obj_list_all, True)
        self.designer.merge_config_with_file(self.cf_increment_path, self.merge_settings)
        self.designer.update_db_config()
        self.designer.commit_config_to_repo(comment, self.repo_obj_list_all)

        report_path = path.join(self.temp_path, 'repo_report.xml')
        self.designer.get_repo_report(report_path)

        with open(report_path, 'r', encoding='utf-8') as f:
            data = f.read()
            self.assertTrue(
                comment in data,
                'Commit не создан.'
            )

    def test_dump_config_from_repo(self):
        self.test_commit_repo()
        cf_file_path = path.join(self.temp_path, '1Cv81_repo.cf')
        self.designer.dump_config_to_file_from_repo(cf_file_path)
        self.assertTrue(os.path.exists(cf_file_path), 'Выгрузка кофигурации не создана!')

        dir_xml_config_path = path.join(self.temp_path, 'xml_config')
        if not path.exists(dir_xml_config_path):
            os.mkdir(dir_xml_config_path)

        convert_cf_to_xml(cf_file_path, '', dir_xml_config_path)

        self.assertTrue(
            os.path.exists(os.path.join(dir_xml_config_path, 'CommonModules\\ОбщийМодуль1.xml')),
            'Выгрузка из хранилища не выполнена.'
        )

    def test_get_repo_report(self):
        self.prepare_repo()

        report_path = path.join(self.temp_path, 'repo_report.xml')
        self.designer.get_repo_report(report_path)

        self.assertTrue(
            os.path.exists(report_path),
            'Отчет не сформирован.'
        )

        with open(report_path, 'r', encoding='utf-8') as f:
            data = f.read()
            self.assertTrue(
                'Создание хранилища конфигурации' in data,
                'В отчете нет необходимых данных'
            )

    def test_merge_cf(self):
        self.prepare_base()
        self.designer.merge_config_with_file(self.cf_increment_path, self.merge_settings)

        dir_xml_config_path = path.join(self.temp_path, 'xml_config')
        if not path.exists(dir_xml_config_path):
            os.mkdir(dir_xml_config_path)
        self.designer.dump_config_to_files(dir_xml_config_path)

        self.assertTrue(
            os.path.exists(os.path.join(dir_xml_config_path, 'CommonModules\\ОбщийМодуль1.xml')),
            'Объединение не выполнено.'
        )

    def test_compare_conf(self):
        self.prepare_base()
        report_path = os.path.join(self.temp_path, 'report.txt')
        self.designer.compare_config_with_file(self.cf_path, report_path)

        self.assertTrue(os.path.exists(report_path), 'Отчет о сравнении не создан!')

    def test_dump_db_to_file(self):
        self.prepare_base()
        new_dt_path = os.path.join(self.temp_path, '1c.dt')
        self.designer.dump_db_to_file(new_dt_path)

        self.assertTrue(os.path.exists(new_dt_path), 'Файл выгрузки не создан!')

    def test_load_db_from_file(self):
        self.designer.create_base()
        self.designer.load_db_from_file(self.dt_path)

        dir_xml_config_path = path.join(self.temp_path, 'xml_config')
        if not path.exists(dir_xml_config_path):
            os.mkdir(dir_xml_config_path)

        self.designer.dump_config_to_files(dir_xml_config_path)

        self.assertTrue(
            os.path.exists(os.path.join(dir_xml_config_path, 'Catalogs\\Справочник1.xml')),
            'Выгрузка не была выполнена.'
        )

    def tearDown(self):
        clear_folder(self.test_base_path)
        clear_folder(self.temp_path)
