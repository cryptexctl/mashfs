#!/usr/bin/env python3
import os
import sys
import readline
import getpass
from pathlib import Path
from typing import Dict, List, Optional
import time
import random
from tqdm import tqdm

class MashShell:
    def __init__(self):
        self.root = Path(os.environ.get('MASHFS_ROOT', 'filesfs')).absolute()
        self.current_dir = Path(os.environ.get('MASHFS_CWD', str(self.root))).absolute()
        self.user = 'mash'
        self.hostname = 'hardmash'
        self.commands = {
            'cd': self._cd,
            'ls': self._ls,
            'pwd': self._pwd,
            'clear': self._clear,
            'help': self._help,
            'exit': self._exit,
            'su': self._su,
            'sudo': self._sudo,
            'whoami': self._whoami,
            'id': self._id,
            'useradd': self._useradd,
            'usermod': self._usermod,
            'userdel': self._userdel,
            'passwd': self._passwd,
            'hostname': self._hostname
        }
        self._setup_readline()
        self._load_config()
        self._load_theme()
        self._show_welcome()

    def _setup_readline(self):
        readline.parse_and_bind('tab: complete')
        readline.set_completer(self._completer)
        readline.set_startup_hook(lambda: readline.insert_text(''))
        readline.set_pre_input_hook(lambda: readline.clear_history())

    def _completer(self, text, state):
        if state == 0:
            if ' ' in text:
                cmd, partial = text.split(' ', 1)
                if cmd in self.commands:
                    return self._path_completer(partial)
            else:
                return self._command_completer(text)
        return None

    def _command_completer(self, text):
        return [cmd for cmd in self.commands.keys() if cmd.startswith(text)]

    def _path_completer(self, text):
        if text.startswith('/'):
            path = self.root / text[1:]
        else:
            path = self.current_dir / text
        try:
            if path.is_dir():
                return [str(path.relative_to(self.root))]
            parent = path.parent
            if parent.is_dir():
                return [str(p.relative_to(self.root)) for p in parent.glob(f'{path.name}*')]
        except Exception:
            pass
        return []

    def _load_config(self):
        config_file = self.root / 'etc' / 'config.yml'
        if config_file.exists():
            import yaml
            with open(config_file) as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {}

    def _load_theme(self):
        theme_file = self.root / 'etc' / 'theme.yml'
        if theme_file.exists():
            import yaml
            with open(theme_file) as f:
                self.theme = yaml.safe_load(f)
        else:
            self.theme = {
                'prompt': '\033[1;32m%s@%s\033[0m:\033[1;34m%s\033[0m$ ',
                'error': '\033[1;31m%s\033[0m',
                'success': '\033[1;32m%s\033[0m',
                'info': '\033[1;36m%s\033[0m'
            }

    def _show_welcome(self):
        print(self.theme['info'] % "Welcome to MashFS Shell! 🚀 (Logged in as %s)" % self.user)
        print(self.theme['info'] % "Type 'help' for available commands")
        print(self.theme['info'] % "Type 'exit' to quit")
        print(self.theme['info'] % "Use Tab for command and path completion")

    def _cd(self, args: List[str]) -> None:
        if not args:
            self.current_dir = self.root
            return
            
        target = args[0]
        if target.startswith('/'):
            new_path = self.root / target[1:]
        else:
            new_path = self.current_dir / target
            
        try:
            new_path = new_path.resolve()
            if not str(new_path).startswith(str(self.root)):
                print(self.theme['error'] % f"cd: access denied: {target}")
                return
                
            if not new_path.is_dir():
                print(self.theme['error'] % f"cd: not a directory: {target}")
                return
                
            self.current_dir = new_path
            os.environ['MASHFS_CWD'] = str(self.current_dir)
            print(self.theme['success'] % str(self.current_dir.relative_to(self.root)))
        except Exception as e:
            print(self.theme['error'] % f"cd: {e}")

    def _ls(self, args: List[str]) -> None:
        try:
            if args:
                target = args[0]
                if target.startswith('/'):
                    path = self.root / target[1:]
                else:
                    path = self.current_dir / target
            else:
                path = self.current_dir
                
            if not str(path.resolve()).startswith(str(self.root)):
                print(self.theme['error'] % f"ls: access denied: {args[0] if args else ''}")
                return
                
            if not path.is_dir():
                print(self.theme['error'] % f"ls: not a directory: {args[0] if args else ''}")
                return
                
            items = list(path.iterdir())
            items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for item in items:
                if item.is_dir():
                    print(self.theme['info'] % f"{item.name}/")
                else:
                    print(item.name)
        except Exception as e:
            print(self.theme['error'] % f"ls: {e}")

    def _pwd(self, args: List[str]) -> None:
        print(self.theme['success'] % str(self.current_dir.relative_to(self.root)))

    def _clear(self, args: List[str]) -> None:
        os.system('clear')

    def _help(self, args: List[str]) -> None:
        help_text = """
╭──────────────────────────────────────────────────────── MashFS Shell Help ────────────────────────────────────────────────────────╮
│                                                                                                                                   │
│ Available Commands:                                                                                                               │
│                                                                                                                                   │
│   cd      - Change directory                                                                                                      │
│   ls      - List directory contents                                                                                               │
│   pwd          - Show current directory                                                                                           │
│   clear        - Clear screen                                                                                                     │
│   help         - Show this help message                                                                                           │
│   exit         - Exit the shell                                                                                                   │
│   packman      - Package manager                                                                                                  │
│   omm          - Oh My Mash theme manager                                                                                         │
│   su     - Switch user                                                                                                            │
│   sudo cmd     - Run command as root                                                                                              │
│   whoami       - Show current user                                                                                                │
│   id           - Show user ID                                                                                                     │
│   useradd user - Add new user                                                                                                     │
│   usermod user - Modify user                                                                                                      │
│   userdel user - Delete user                                                                                                      │
│   passwd  - Change password                                                                                                       │
│   hostname  - Show/set hostname                                                                                                   │
│                                                                                                                                   │
│ Features:                                                                                                                         │
│   - Tab completion for commands and paths                                                                                         │
│   - Color-coded output                                                                                                            │
│   - Virtual filesystem                                                                                                            │
│   - Package management                                                                                                            │
│   - Theme customization                                                                                                           │
"""
        print(help_text)

    def _exit(self, args: List[str]) -> None:
        print(self.theme['info'] % "Goodbye! 👋")
        sys.exit(0)

    def _su(self, args: List[str]) -> None:
        if not args:
            print(self.theme['error'] % "Usage: su <username>")
            return
            
        username = args[0]
        try:
            password = getpass.getpass(f"Password for {username}: ")
            if self._authenticate(username, password):
                self.user = username
                print(self.theme['success'] % f"Switched to user: {username}")
            else:
                print(self.theme['error'] % "Authentication failed")
        except Exception as e:
            print(self.theme['error'] % f"su: {e}")

    def _sudo(self, args: List[str]) -> None:
        if not args:
            print(self.theme['error'] % "Usage: sudo <command>")
            return
            
        try:
            password = getpass.getpass("Password: ")
            if self._authenticate('root', password):
                cmd = ' '.join(args)
                os.system(f"sudo {cmd}")
            else:
                print(self.theme['error'] % "Authentication failed")
        except Exception as e:
            print(self.theme['error'] % f"sudo: {e}")

    def _whoami(self, args: List[str]) -> None:
        print(self.theme['success'] % self.user)

    def _id(self, args: List[str]) -> None:
        try:
            username = args[0] if args else self.user
            user_info = self._get_user_info(username)
            if user_info:
                print(self.theme['success'] % f"uid={user_info['uid']}({username}) gid={user_info['gid']}({username}) groups={user_info['gid']}({username})")
            else:
                print(self.theme['error'] % f"id: {username}: no such user")
        except Exception as e:
            print(self.theme['error'] % f"id: {e}")

    def _useradd(self, args: List[str]) -> None:
        if not args:
            print(self.theme['error'] % "Usage: useradd <username>")
            return
            
        username = args[0]
        try:
            if self._user_exists(username):
                print(self.theme['error'] % f"useradd: user {username} already exists")
                return
                
            self._add_user(username)
            print(self.theme['success'] % f"User {username} created successfully")
        except Exception as e:
            print(self.theme['error'] % f"useradd: {e}")

    def _usermod(self, args: List[str]) -> None:
        if len(args) < 2:
            print(self.theme['error'] % "Usage: usermod <username> <new_username>")
            return
            
        old_username, new_username = args[0], args[1]
        try:
            if not self._user_exists(old_username):
                print(self.theme['error'] % f"usermod: user {old_username} does not exist")
                return
                
            if self._user_exists(new_username):
                print(self.theme['error'] % f"usermod: user {new_username} already exists")
                return
                
            self._modify_user(old_username, new_username)
            print(self.theme['success'] % f"User {old_username} renamed to {new_username}")
        except Exception as e:
            print(self.theme['error'] % f"usermod: {e}")

    def _userdel(self, args: List[str]) -> None:
        if not args:
            print(self.theme['error'] % "Usage: userdel <username>")
            return
            
        username = args[0]
        try:
            if not self._user_exists(username):
                print(self.theme['error'] % f"userdel: user {username} does not exist")
                return
                
            self._delete_user(username)
            print(self.theme['success'] % f"User {username} deleted successfully")
        except Exception as e:
            print(self.theme['error'] % f"userdel: {e}")

    def _passwd(self, args: List[str]) -> None:
        username = args[0] if args else self.user
        try:
            if not self._user_exists(username):
                print(self.theme['error'] % f"passwd: user {username} does not exist")
                return
                
            current_password = getpass.getpass("Current password: ")
            if not self._authenticate(username, current_password):
                print(self.theme['error'] % "Current password incorrect")
                return
                
            new_password = getpass.getpass("New password: ")
            confirm_password = getpass.getpass("Retype new password: ")
            
            if new_password != confirm_password:
                print(self.theme['error'] % "passwd: password mismatch")
                return
                
            self._change_password(username, new_password)
            print(self.theme['success'] % "Password updated successfully")
        except Exception as e:
            print(self.theme['error'] % f"passwd: {e}")

    def _hostname(self, args: List[str]) -> None:
        if args:
            self.hostname = args[0]
            print(self.theme['success'] % f"Hostname set to: {self.hostname}")
        else:
            print(self.theme['success'] % self.hostname)

    def _authenticate(self, username: str, password: str) -> bool:
        try:
            shadow_file = self.root / 'etc' / 'shadow'
            if not shadow_file.exists():
                return False
                
            with open(shadow_file) as f:
                for line in f:
                    if line.startswith(f"{username}:"):
                        stored_hash = line.split(':')[1]
                        return self._verify_password(password, stored_hash)
            return False
        except Exception:
            return False

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        import hashlib
        salt = stored_hash.split('$')[2]
        hash_obj = hashlib.sha256()
        hash_obj.update((password + salt).encode())
        return hash_obj.hexdigest() == stored_hash.split('$')[3]

    def _get_user_info(self, username: str) -> Optional[Dict]:
        try:
            passwd_file = self.root / 'etc' / 'passwd'
            if not passwd_file.exists():
                return None
                
            with open(passwd_file) as f:
                for line in f:
                    if line.startswith(f"{username}:"):
                        parts = line.strip().split(':')
                        return {
                            'username': parts[0],
                            'uid': int(parts[2]),
                            'gid': int(parts[3])
                        }
            return None
        except Exception:
            return None

    def _user_exists(self, username: str) -> bool:
        return self._get_user_info(username) is not None

    def _add_user(self, username: str) -> None:
        import hashlib
        import random
        import string
        
        salt = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        hash_obj = hashlib.sha256()
        hash_obj.update((password + salt).encode())
        password_hash = f"$6${salt}${hash_obj.hexdigest()}"
        
        passwd_file = self.root / 'etc' / 'passwd'
        shadow_file = self.root / 'etc' / 'shadow'
        
        uid = 1000
        if passwd_file.exists():
            with open(passwd_file) as f:
                for line in f:
                    if line.strip():
                        uid = max(uid, int(line.split(':')[2]) + 1)
        
        with open(passwd_file, 'a') as f:
            f.write(f"{username}:x:{uid}:{uid}:{username}:/home/{username}:/bin/bash\n")
            
        with open(shadow_file, 'a') as f:
            f.write(f"{username}:{password_hash}:0:0:99999:7:::\n")
            
        home_dir = self.root / 'home' / username
        home_dir.mkdir(parents=True, exist_ok=True)
        
        print(self.theme['info'] % f"Default password for {username}: {password}")

    def _modify_user(self, old_username: str, new_username: str) -> None:
        passwd_file = self.root / 'etc' / 'passwd'
        shadow_file = self.root / 'etc' / 'shadow'
        
        with open(passwd_file, 'r') as f:
            lines = f.readlines()
            
        with open(passwd_file, 'w') as f:
            for line in lines:
                if line.startswith(f"{old_username}:"):
                    parts = line.split(':')
                    parts[0] = new_username
                    parts[4] = new_username
                    parts[5] = f"/home/{new_username}"
                    f.write(':'.join(parts))
                else:
                    f.write(line)
                    
        with open(shadow_file, 'r') as f:
            lines = f.readlines()
            
        with open(shadow_file, 'w') as f:
            for line in lines:
                if line.startswith(f"{old_username}:"):
                    f.write(f"{new_username}:{line[len(old_username)+1:]}")
                else:
                    f.write(line)
                    
        old_home = self.root / 'home' / old_username
        new_home = self.root / 'home' / new_username
        if old_home.exists():
            old_home.rename(new_home)

    def _delete_user(self, username: str) -> None:
        passwd_file = self.root / 'etc' / 'passwd'
        shadow_file = self.root / 'etc' / 'shadow'
        
        with open(passwd_file, 'r') as f:
            lines = f.readlines()
            
        with open(passwd_file, 'w') as f:
            for line in lines:
                if not line.startswith(f"{username}:"):
                    f.write(line)
                    
        with open(shadow_file, 'r') as f:
            lines = f.readlines()
            
        with open(shadow_file, 'w') as f:
            for line in lines:
                if not line.startswith(f"{username}:"):
                    f.write(line)
                    
        home_dir = self.root / 'home' / username
        if home_dir.exists():
            import shutil
            shutil.rmtree(home_dir)

    def _change_password(self, username: str, new_password: str) -> None:
        import hashlib
        import random
        import string
        
        salt = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        hash_obj = hashlib.sha256()
        hash_obj.update((new_password + salt).encode())
        password_hash = f"$6${salt}${hash_obj.hexdigest()}"
        
        shadow_file = self.root / 'etc' / 'shadow'
        with open(shadow_file, 'r') as f:
            lines = f.readlines()
            
        with open(shadow_file, 'w') as f:
            for line in lines:
                if line.startswith(f"{username}:"):
                    f.write(f"{username}:{password_hash}:0:0:99999:7:::\n")
                else:
                    f.write(line)

    def _run_external_command(self, cmd: str, args: List[str]) -> None:
        cmd_path = self.root / 'bin' / cmd
        if not cmd_path.exists() or not cmd_path.is_file() or not os.access(cmd_path, os.X_OK):
            print(self.theme['error'] % f"Command not found: {cmd}")
            return
            
        cmd_str = f"python3 {cmd_path} {' '.join(args)}"
        os.system(cmd_str)

    def run(self) -> None:
        while True:
            try:
                prompt = self.theme['prompt'] % (self.user, self.hostname, str(self.current_dir.relative_to(self.root)))
                readline.set_startup_hook(lambda: readline.insert_text(''))
                readline.set_pre_input_hook(lambda: readline.clear_history())
                cmd = input(prompt).strip()
                readline.set_startup_hook()
                readline.set_pre_input_hook(None)
                
                if not cmd:
                    continue
                    
                parts = cmd.split()
                command = parts[0]
                args = parts[1:]
                
                if command in self.commands:
                    self.commands[command](args)
                else:
                    self._run_external_command(command, args)
            except KeyboardInterrupt:
                print()
            except Exception as e:
                print(self.theme['error'] % f"Error: {e}")

if __name__ == "__main__":
    shell = MashShell()
    shell.run() 