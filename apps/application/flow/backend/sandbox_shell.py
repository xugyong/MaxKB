import getpass
import os

from deepagents.backends import LocalShellBackend
from deepagents.backends.protocol import ExecuteResponse

from maxkb.const import CONFIG

_enable_sandbox = bool(CONFIG.get('SANDBOX', 0))
_run_user = 'sandbox' if _enable_sandbox else getpass.getuser()
_sandbox_python_sys_path = CONFIG.get_sandbox_python_package_paths().split(',')


class SandboxShellBackend(LocalShellBackend):
    def __init__(self, root_dir: str, **kwargs):
        if 'env' not in kwargs and not kwargs.get('inherit_env', False):
            env = os.environ.copy()
            path = env.get('PATH', '/usr/bin:/bin')
            if _sandbox_python_sys_path not in path.split(os.pathsep):
                env['PATH'] = f"{_sandbox_python_sys_path}{os.pathsep}{path}"
            kwargs['env'] = env
        super().__init__(root_dir=root_dir, **kwargs)

    def execute(
            self,
            command: str,
            *,
            timeout: int | None = None,
    ) -> ExecuteResponse:
        if _enable_sandbox:
            # 用 runuser 在子进程里切换用户，父进程凭据保持不变，
            # 避免父进程 ruid/euid 不一致导致 execve 报 Permission denied
            command = f"runuser -u {_run_user} -- env -i LD_PRELOAD=/opt/maxkb-app/sandbox/lib/sandbox.so PATH=${{PATH}} {command}"
            # command = f"runuser -u {_run_user} -- env -i PATH=${{PATH}} {command}"

        # print(f"Executing command in sandbox: {command}")
        return super().execute(command=command, timeout=timeout)
