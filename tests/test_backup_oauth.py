#!/usr/bin/env python3
"""Custom OAuth credentials must reach rclone without entering public configuration."""
import importlib.machinery
import importlib.util
import os
import tempfile

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
loader = importlib.machinery.SourceFileLoader('backup_oauth', os.path.join(root, 'files', 'bin', 'bricohams-backup-remoto'))
module = importlib.util.module_from_spec(importlib.util.spec_from_loader('backup_oauth', loader))
loader.exec_module(module)

with tempfile.TemporaryDirectory() as tmp:
    module.DATOS = tmp
    module.ESTADO = os.path.join(tmp, 'estado.json')
    module.RCLONE_CONF = os.path.join(tmp, 'rclone.conf')
    for provider in ('gdrive', 'onedrive'):
        conf = {'protocolo': provider, 'ruta': 'copias', 'drive_id': 'drive-test', 'drive_type': 'business',
                'oauth_client_id': 'client-test'}
        secrets = {'token': '{"access_token":"test","refresh_token":"refresh"}',
                   'oauth_client_secret': 'secret-test'}
        with module.Rclone(conf, secrets):
            with open(module.RCLONE_CONF, encoding='utf-8') as f:
                text = f.read()
            assert 'client_id = client-test\n' in text
            assert 'client_secret = secret-test\n' in text
            assert os.stat(module.RCLONE_CONF).st_mode & 0o777 == 0o600
        with open(module.ESTADO, encoding='utf-8') as f:
            assert 'secret-test' not in f.read()
        with module.Rclone(conf, secrets):
            with open(module.RCLONE_CONF, 'a', encoding='utf-8') as f:
                f.write('# token renewed\n')
        with module.Rclone(conf, secrets):
            with open(module.RCLONE_CONF, encoding='utf-8') as f:
                assert '# token renewed' in f.read(), 'do not overwrite refreshed tokens'
        shared = dict(conf)
        shared.pop('oauth_client_id')
        with module.Rclone(shared, {'token': secrets['token']}):
            with open(module.RCLONE_CONF, encoding='utf-8') as f:
                assert 'client_secret' not in f.read(), 'changing client drops stale credentials'

print('OK backup OAuth credentials and token refresh preservation')
