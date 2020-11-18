from designer_cmd.api import Connection, Designer
import unittest
import os.path as path
import os
import shutil


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
            [f'/F {path.abspath(loc_path)}', '/N user', '/P pass'],
            'Не верно определена строка подключени для файловой базы'
        )

    def test_get_connection_params_server(self):

        con = Connection(user='user', password='pass', server_path='192.168.1.1', server_base_ref='test')
        self.assertEqual(
            con.get_connection_params(),
            ['/S 192.168.1.1\\test', '/N user', '/P pass'],
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


class TestDesigner(unittest.TestCase):

    def setUp(self):
        test_data_dir = path.join(path.dirname(__file__), 'test_data')

        self.temp_path = path.join(test_data_dir, 'temp')
        self.test_base_path = path.join(test_data_dir, 'base')
        self.cf_path = path.join(test_data_dir, '1Cv8.cf')
        self.dt_path = path.join(test_data_dir, '1Cv8.dt')
        self.cf_increment_path = path.join(test_data_dir, '1Cv8_increment.cf')

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

    def tearDown(self):
        clear_folder(self.test_base_path)
        clear_folder(self.temp_path)
