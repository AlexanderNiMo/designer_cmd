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
        self.temp_path = path.abspath('test_data/temp')
        self.test_base_path = path.abspath('test_data/base')
        self.cf_path = 'test_data/Конфигурация БГУ 2.0.69.16012 200415.cf'

        self.conn = self.db_connection()
        self.designer = Designer('', self.conn)

        clear_folder(self.test_base_path)
        clear_folder(self.temp_path)

    def db_connection(self):
        return Connection(file_path=self.test_base_path)

    def prepare_base(self):
        self.designer.create_base()
        self.designer.load_config_from_file(self.cf_path)

    def test_load_create_db(self):
        self.designer.create_base()

    def test_load_conf_from_file(self):
        self.prepare_base()

    def test_update_cfg(self):
        self.prepare_base()
        self.designer.updete_db_config()

    def test_dump_conf_to_file(self):
        self.prepare_base()
        self.designer.dump_config_to_file(path.join(self.temp_path, '1Cv81.cf'))

    def test_dump_config_to_files(self):
        self.prepare_base()
        dir_xml_config_path = path.join(self.temp_path, 'xml_config')
        if not path.exists(dir_xml_config_path):
            os.mkdir(dir_xml_config_path)
        self.designer.dump_config_to_files(dir_xml_config_path)

    def tearDown(self):
        clear_folder(self.test_base_path)
        clear_folder(self.temp_path)
