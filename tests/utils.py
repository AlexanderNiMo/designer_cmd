from designer_cmd.utils import utils

import unittest
from unittest import mock


class TestUtils(unittest.TestCase):

    def setUp(self):
        pass

    def test_get_version_weight(self):
        weight = utils.get_version_weight('8.3.14.1232')
        self.assertEqual(weight, 8003015232)

    def test_get_version_weight_eseption(self):
        with self.assertRaises(ValueError) as error:
            utils.get_version_weight('8.3.14.123212')
        self.assertEqual(
            error.exception.args[0],
            'Ошибка вычисления веса версии, длинна октава не должна быть больше 4.',
            'Проверка на ошибочную версию не прошла.'
        )

    @mock.patch('os.listdir')
    def test_get_platform_path_exeption(self, os_listdir):

        check_version = '8.3.14.1232'
        os_listdir.return_value = [
            '8.3.11.1232',
            '8.3.12.1132',
            '8.3.14.1231',
            '8.2.14.1232',
            '8.3.15.1232',
        ]

        with self.assertRaises(EnvironmentError) as error:
            utils.get_platform_path(check_version)
        self.assertEqual(
            error.exception.args[0],
            f'Не обнаружена версия {check_version} 1с.',
            'Проверка на ошибку поиска не пройдена'
        )

    @mock.patch('os.listdir')
    def test_get_platform_path(self, os_listdir):
        pref_path = 'PATH'
        max_version = '8.3.17.1212'
        os_listdir.return_value = [
            '8.3.11.1232',
            '8.3.12.1132',
            '8.3.14.1231',
            '8.2.14.1232',
            '8.3.15.1232',
            max_version
        ]
        check_version = '8.2.14.1232'
        with mock.patch('os.getenv') as os_getenv:
            os_getenv.return_value = pref_path
            platform_path = utils.get_platform_path(check_version)
            self.assertEqual(
                platform_path,
                f'{pref_path}\\1cv8\\{check_version}',
                'Не прошла проверка не получение версии'
            )

            platform_path = utils.get_platform_path('')
            self.assertEqual(
                platform_path,
                f'{pref_path}\\1cv8\\{max_version}',
                'Не прошла проверка на получение последней версии'
            )

    def test_execute_command(self):
        result = utils.execute_command('dir', [])
        self.assertEqual(result[0], 0, 'Не удалось выполнить команду систему!')

        result = utils.execute_command('dir111', [])
        self.assertNotEqual(result[0], 0, 'Проверка на ошибочную команду провалилась!')

    def tearDown(self):
        pass
