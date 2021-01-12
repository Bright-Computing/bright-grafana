import os
import subprocess


class RSync:
    @classmethod
    def run(cls, hostname, username, password, source, target):
        env = os.environ.copy()
        ssh = f'ssh -o StrictHostKeyChecking=no -l {username}'
        if password is not None:
            env['SSHPASS'] = password
            ssh = f'sshpass -e {ssh}'
        if not os.path.exists(target):
            os.makedirs(target)
        cmd = ['rsync',
               '-a',
               '--stats',
               '--exclude=*.pyc',
               '--exclude=__pycache__',
               '--rsh="%s"' % ssh,
               f'{hostname}:{source.rstrip("/")}/',
               f'{target.rstrip("/")}/']
        cmd = ' '.join(cmd)
        print(f'*** run {cmd} ***')
        return subprocess.call(cmd, env=env, shell=True) == 0
