import configparser
from datetime import datetime, timedelta, timezone
import subprocess

import pytest

from autosuspend.checks import ConfigurationError, TemporaryCheckError
from autosuspend.checks.wakeup import (WakeupCommand,
                                       WakeupFile,
                                       WakeupXPath,
                                       WakeupXPathDelta)


class TestWakeupFile(object):

    def test_create(self):
        parser = configparser.ConfigParser()
        parser.read_string('''[section]
                              path = /tmp/test''')
        check = WakeupFile.create('name', parser['section'])
        assert check._path == '/tmp/test'

    def test_create_no_path(self):
        parser = configparser.ConfigParser()
        parser.read_string('''[section]''')
        with pytest.raises(ConfigurationError):
            WakeupFile.create('name', parser['section'])

    def test_smoke(self, tmpdir):
        file = tmpdir.join('file')
        file.write('42\n\n')
        assert WakeupFile('name', str(file)).check(
            datetime.now(timezone.utc)) == datetime.fromtimestamp(
                42, timezone.utc)

    def test_no_file(self, tmpdir):
        assert WakeupFile('name', str(tmpdir.join('narf'))).check(
            datetime.now(timezone.utc)) is None

    def test_invalid_number(self, tmpdir):
        file = tmpdir.join('filexxx')
        file.write('nonumber\n\n')
        with pytest.raises(TemporaryCheckError):
            WakeupFile('name', str(file)).check(
                datetime.now(timezone.utc))


class TestWakeupCommand(object):

    def test_smoke(self):
        check = WakeupCommand('test', 'echo 1234')
        assert check.check(
            datetime.now(timezone.utc)) == datetime.fromtimestamp(
                1234, timezone.utc)

    def test_no_output(self):
        check = WakeupCommand('test', 'echo')
        assert check.check(datetime.now(timezone.utc)) is None

    def test_not_parseable(self):
        check = WakeupCommand('test', 'echo asdfasdf')
        with pytest.raises(TemporaryCheckError):
            check.check(datetime.now(timezone.utc))

    def test_multiple_lines(self, mocker):
        mock = mocker.patch('subprocess.check_output')
        mock.return_value = '1234\nignore\n'
        check = WakeupCommand('test', 'echo bla')
        assert check.check(
            datetime.now(timezone.utc)) == datetime.fromtimestamp(
                1234, timezone.utc)

    def test_multiple_lines_but_empty(self, mocker):
        mock = mocker.patch('subprocess.check_output')
        mock.return_value = '   \nignore\n'
        check = WakeupCommand('test', 'echo bla')
        assert check.check(datetime.now(timezone.utc)) is None

    def test_process_error(self, mocker):
        mock = mocker.patch('subprocess.check_output')
        mock.side_effect = subprocess.CalledProcessError(2, 'foo bar')
        check = WakeupCommand('test', 'echo bla')
        with pytest.raises(TemporaryCheckError):
            check.check(datetime.now(timezone.utc))


class TestWakeupXPath(object):

    def test_matching(self, mocker):
        mock_reply = mocker.MagicMock()
        content_property = mocker.PropertyMock()
        type(mock_reply).content = content_property
        content_property.return_value = '<a value="42.3"></a>'
        mock_method = mocker.patch('requests.get', return_value=mock_reply)

        url = 'nourl'
        assert WakeupXPath(
            'foo', '/a/@value', url, 5).check(
                datetime.now(timezone.utc)) == datetime.fromtimestamp(
                    42.3, timezone.utc)

        mock_method.assert_called_once_with(url, timeout=5)
        content_property.assert_called_once_with()

    def test_not_matching(self, mocker):
        mock_reply = mocker.MagicMock()
        content_property = mocker.PropertyMock()
        type(mock_reply).content = content_property
        content_property.return_value = "<a></a>"
        mocker.patch('requests.get', return_value=mock_reply)

        assert WakeupXPath('foo', '/b', 'nourl', 5).check(
            datetime.now(timezone.utc)) is None

    def test_not_a_string(self, mocker):
        mock_reply = mocker.MagicMock()
        content_property = mocker.PropertyMock()
        type(mock_reply).content = content_property
        content_property.return_value = "<a></a>"
        mocker.patch('requests.get', return_value=mock_reply)

        with pytest.raises(TemporaryCheckError):
            WakeupXPath('foo', '/a', 'nourl', 5).check(
                datetime.now(timezone.utc))

    def test_not_a_number(self, mocker):
        mock_reply = mocker.MagicMock()
        content_property = mocker.PropertyMock()
        type(mock_reply).content = content_property
        content_property.return_value = '<a value="narf"></a>'
        mocker.patch('requests.get', return_value=mock_reply)

        with pytest.raises(TemporaryCheckError):
            WakeupXPath('foo', '/a/@value', 'nourl', 5).check(
                datetime.now(timezone.utc))

    def test_multiple_min(self, mocker):
        mock_reply = mocker.MagicMock()
        content_property = mocker.PropertyMock()
        type(mock_reply).content = content_property
        content_property.return_value = '''<root>
    <a value="40"></a>
    <a value="10"></a>
    <a value="20"></a>
</root>
'''
        mocker.patch('requests.get', return_value=mock_reply)

        assert WakeupXPath(
            'foo', '//a/@value', 'nourl', 5).check(
                datetime.now(timezone.utc)) == datetime.fromtimestamp(
                    10, timezone.utc)


class TestWakeupXPathDelta(object):

    @pytest.mark.parametrize("unit,factor", [
        ('microseconds', 0.000001),
        ('milliseconds', 0.001),
        ('seconds', 1),
        ('minutes', 60),
        ('hours', 60 * 60),
        ('days', 60 * 60 * 24),
        ('weeks', 60 * 60 * 24 * 7),
    ])
    def test_smoke(self, mocker, unit, factor):
        mock_reply = mocker.MagicMock()
        content_property = mocker.PropertyMock()
        type(mock_reply).content = content_property
        content_property.return_value = '<a value="42"></a>'
        mocker.patch('requests.get', return_value=mock_reply)

        url = 'nourl'
        now = datetime.now(timezone.utc)
        result = WakeupXPathDelta(
            'foo', '/a/@value', url, 5, unit).check(now)
        assert result == now + timedelta(seconds=42) * factor

    def test_create(self):
        parser = configparser.ConfigParser()
        parser.read_string('''[section]
                           xpath=/valid
                           url=nourl
                           timeout=20
                           unit=weeks''')
        check = WakeupXPathDelta.create('name', parser['section'])
        assert check._unit == 'weeks'

    def test_init_wrong_unit(self):
        with pytest.raises(ValueError):
            WakeupXPathDelta('name', 'url', '/a', 5, 'unknownunit')
