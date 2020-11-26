from designer_cmd.utils import utils

import unittest
from unittest import mock


class TestPlatform(unittest.TestCase):

    def test_get_version_weight(self):

        platform = utils.PlatformVersion('8.3.14.1232')
        weight = platform.version_weight
        self.assertEqual(weight, 8003015232)

    def test_get_version_weight_eseption(self):
        with self.assertRaises(ValueError) as error:
            utils.PlatformVersion('8.3.14.123212')
        self.assertEqual(
            error.exception.args[0],
            'Ошибка вычисления веса версии, длинна октава не должна быть больше 4.',
            'Проверка на ошибочную версию не прошла.'
        )

    @mock.patch('os.listdir')
    def test_get_platform_path_exeption(self, os_listdir):

        check_version = utils.PlatformVersion('8.3.14.1232')
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
        max_version = utils.PlatformVersion('8.3.17.1212')
        os_listdir.return_value = [
            '8.3.11.1232',
            '8.3.12.1132',
            '8.3.14.1231',
            '8.2.14.1232',
            '8.3.15.1232',
            max_version.version
        ]
        check_version = utils.PlatformVersion('8.2.14.1232')
        with mock.patch('os.getenv') as os_getenv:
            os_getenv.return_value = pref_path
            platform_path = utils.get_platform_path(check_version)
            self.assertEqual(
                platform_path,
                f'{pref_path}\\1cv8\\{check_version}\\bin\\1cv8.exe',
                'Не прошла проверка не получение версии'
            )

            platform_path = utils.get_platform_path(utils.PlatformVersion(''))
            self.assertEqual(
                platform_path,
                f'{pref_path}\\1cv8\\{max_version}\\bin\\1cv8.exe',
                'Не прошла проверка на получение последней версии'
            )

    def test_platform_eq_operators(self):

        vresion_max = utils.PlatformVersion('')
        versuon_1 = utils.PlatformVersion('8.3.14.1522')
        version_2 = utils.PlatformVersion('8.3.14.1422')
        versuon_3 = utils.PlatformVersion('8.3.14.1522')

        self.assertGreater(vresion_max, versuon_1, 'Проверка на сравление с максимальной версией не прошла.')
        self.assertGreater(vresion_max, version_2, 'Проверка на сравление с максимальной версией не прошла.')
        self.assertGreater(versuon_1, version_2, 'Проверка на сравление версий не прошла.')
        self.assertEqual(versuon_1, versuon_3, 'Проверка на равенство не прошла')
        self.assertNotEqual(versuon_1, version_2, 'Провенка на неравенство не прошла.')


class TestUtils(unittest.TestCase):

    def setUp(self):
        pass

    def test_execute_command(self):
        result = utils.execute_command('dir', [])
        self.assertEqual(result[0], 0, 'Не удалось выполнить команду систему!')

        with self.assertRaises(FileNotFoundError) as error:
            utils.execute_command('dir111', [])
        self.assertEqual(
            error.exception.args[0],
            2,
            'Проверка на ошибочную команду провалилась!'
        )

    def test_timout_exception(self):
        result = utils.execute_command('cmd.exe', ['/c', 'pause 10'], 1)
        self.assertTrue(result[0] == 1, 'Ошибка по таймауту не произошла')

    def tearDown(self):
        pass
