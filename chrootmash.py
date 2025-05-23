#!/usr/bin/env python3
import os
import sys
import readline
import getpass
import yaml
import time
import random
import signal
import subprocess
from pathlib import Path

class MashShell:
    def __init__(self):
        self.root = Path(os.environ.get('MASHFS_ROOT', 'filesfs')).absolute()
        self.cwd = Path(os.environ.get('MASHFS_CWD', 'home/mash'))
        self.user = os.environ.get('USER', 'mash')
        self.hostname = "hardmash"
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
            'hostname': self._hostname,
        }
        
        self.logos = [
            """
  __  __    _    ____  _   _ 
 |  \/  |  / \  / ___|| | | |
 | |\/| | / _ \ \___ \| |_| |
 | |  | |/ ___ \ ___) |  _  |
 |_|  |_/_/   \_\____/|_| |_|
                             
            """,
            """
 ███▄ ▄███▓ ▄▄▄       ██████  ██░ ██ 
▓██▒▀█▀ ██▒▒████▄   ▒██    ▒ ▓██░ ██▒
▓██    ▓██░▒██  ▀█▄ ░ ▓██▄   ▒██▀▀██░
▒██    ▒██ ░██▄▄▄▄██  ▒   ██▒░▓█ ░██ 
▒██▒   ░██▒ ▓█   ▓██▒▒██████▒▒░▓█▒░██▓
░ ▒░   ░  ░ ▒▒   ▓▒█░▒ ▒▓▒ ▒ ░ ▒ ░░▒░▒
░  ░      ░  ▒   ▒▒ ░░ ░▒  ░ ░ ▒ ░▒░ ░
░      ░     ░   ▒   ░  ░  ░   ░  ░░ ░
       ░         ░  ░      ░   ░  ░  ░
            """,
            """
░▒▓██████████████▓▒░ ░▒▓██████▓▒░ ░▒▓███████▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░░▒▓██████▓▒░░▒▓████████▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒░             
            """,
            """
   __  ______   ______ __
  /  |/  / _ | / __/ // /
 / /|_/ / __ |_\ \/ _  / 
/_/  /_/_/ |_/___/_//_/  
                         
            """,
            """
███    ███  █████  ███████ ██   ██ 
████  ████ ██   ██ ██      ██   ██ 
██ ████ ██ ███████ ███████ ███████ 
██  ██  ██ ██   ██      ██ ██   ██ 
██      ██ ██   ██ ███████ ██   ██ 
                                   
                 Машенька, привет!
            """
        ]
        
        self.quotes = [
            "Добро пожаловать в MashFS - самую удивительную файловую систему!",
            "MashFS - где каждая команда - это приключение!",
            "MashFS - понятная, быстрая, надежная!",
            "Вы готовы к магии MashFS?",
            "MashFS - создана с любовью к Unix!",
            "Машенька, привет!"
        ]
        
        self.passwd_db = {}
        self.users_db = {}
        self.shadow_file = self.root / 'etc' / 'shadow'
        self.users_file = self.root / 'etc' / 'passwd'
        self.sudo_users = ['root']
        
        self._setup_dirs()
        self._load_passwd()
        self._load_users()
        self._load_theme()
        
        signal.signal(signal.SIGINT, self._handle_sigint)
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        
        self.setup_readline()
        
    def setup_readline(self):
        readline.set_completer(self._completer)
        readline.parse_and_bind("tab: complete")
        
    def _completer(self, text, state):
        line = readline.get_line_buffer().strip()
        parts = line.split()
        
        if not parts:
            cmds = list(self.commands.keys()) + [x for x in os.listdir(self.root / 'bin') if os.access(self.root / 'bin' / x, os.X_OK)]
            if text:
                cmds = [cmd for cmd in cmds if cmd.startswith(text)]
            try:
                return cmds[state]
            except IndexError:
                return None
        
        if len(parts) == 1 and not line.endswith(' '):
            cmds = list(self.commands.keys()) + [x for x in os.listdir(self.root / 'bin') if os.access(self.root / 'bin' / x, os.X_OK)]
            if text:
                cmds = [cmd for cmd in cmds if cmd.startswith(text)]
            try:
                return cmds[state]
            except IndexError:
                return None
        
        path_to_complete = text
        if not path_to_complete:
            path_to_complete = '.'
            
        if path_to_complete.startswith('/'):
            full_path = self.root / path_to_complete[1:]
        else:
            full_path = self.root / self.cwd / path_to_complete
            
        try:
            dir_path = full_path.parent if full_path.name else full_path
            file_prefix = full_path.name
            
            if not dir_path.exists() or not dir_path.is_dir():
                return None
                
            files = os.listdir(dir_path)
            if file_prefix:
                files = [f for f in files if f.startswith(file_prefix)]
                
            if state < len(files):
                comp_file = files[state]
                if (dir_path / comp_file).is_dir():
                    if path_to_complete.endswith('/'):
                        return f"{path_to_complete}{comp_file}/"
                    elif path_to_complete == '.':
                        return f"{comp_file}/"
                    else:
                        return f"{path_to_complete.rsplit('/', 1)[0]}/{comp_file}/"
                else:
                    if path_to_complete.endswith('/'):
                        return f"{path_to_complete}{comp_file}"
                    elif path_to_complete == '.':
                        return comp_file
                    else:
                        if '/' in path_to_complete:
                            return f"{path_to_complete.rsplit('/', 1)[0]}/{comp_file}"
                        else:
                            return comp_file
            
        except Exception as e:
            pass
        
        return None
        
    def _setup_dirs(self):
        for d in [
            self.root / 'home' / self.user,
            self.root / 'etc',
            self.root / 'bin',
            self.root / 'usr' / 'bin',
            self.root / 'usr' / 'local' / 'bin',
            self.root / 'var' / 'log',
            self.root / 'opt',
        ]:
            d.mkdir(exist_ok=True, parents=True)
            
    def _load_passwd(self):
        if self.shadow_file.exists():
            with open(self.shadow_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        parts = line.strip().split(':')
                        if len(parts) >= 2:
                            self.passwd_db[parts[0]] = parts[1]
        else:
            with open(self.shadow_file, 'w') as f:
                f.write("root:toor\n")
                f.write("mash:mashka\n")
                f.write("arbung:kadzimoment\n")
            self.passwd_db['root'] = 'toor'
            self.passwd_db['mash'] = 'mashka'
            self.passwd_db['arbung'] = 'kadzimoment'
            
    def _load_users(self):
        if self.users_file.exists():
            with open(self.users_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        parts = line.strip().split(':')
                        if len(parts) >= 7:
                            self.users_db[parts[0]] = {
                                'uid': parts[2],
                                'gid': parts[3],
                                'name': parts[4],
                                'home': parts[5],
                                'shell': parts[6]
                            }
        else:
            with open(self.users_file, 'w') as f:
                f.write("root:x:0:0:Root:/home/root:/bin/mash\n")
                f.write("mash:x:1000:1000:Mash User:/home/mash:/bin/mash\n")
                f.write("arbung:x:1001:1001:ARBUNG:/home/arbung:/bin/mash\n")
            self.users_db['root'] = {'uid': '0', 'gid': '0', 'name': 'Root', 'home': '/home/root', 'shell': '/bin/mash'}
            self.users_db['mash'] = {'uid': '1000', 'gid': '1000', 'name': 'Mash User', 'home': '/home/mash', 'shell': '/bin/mash'}
            self.users_db['arbung'] = {'uid': '1001', 'gid': '1001', 'name': 'ARBUNG', 'home': '/home/arbung', 'shell': '/bin/mash'}
            
    def _load_theme(self):
        self.theme_file = self.root / 'etc' / 'theme.yml'
        if not self.theme_file.exists():
            self.theme = {
                'prompt': "\033[1;32m%s\033[0m@\033[1;34m%s\033[0m:\033[1;36m%s\033[0m$ ",
                'error': "\033[1;31m%s\033[0m",
                'success': "\033[1;32m%s\033[0m",
                'info': "\033[1;36m%s\033[0m",
                'warning': "\033[1;33m%s\033[0m"
            }
            with open(self.theme_file, 'w') as f:
                yaml.dump({
                    'name': 'default',
                    'description': 'Default MashFS theme',
                    'colors': self.theme
                }, f)
        else:
            try:
                with open(self.theme_file, 'r') as f:
                    theme_data = yaml.safe_load(f)
                self.theme = theme_data.get('colors', {})
                
                for key, value in self.theme.items():
                    self.theme[key] = value.replace('\\033', '\x1b')
                    
            except Exception as e:
                print(f"Error loading theme: {e}")
                self.theme = {
                    'prompt': "\033[1;32m%s\033[0m@\033[1;34m%s\033[0m:\033[1;36m%s\033[0m$ ",
                    'error': "\033[1;31m%s\033[0m",
                    'success': "\033[1;32m%s\033[0m",
                    'info': "\033[1;36m%s\033[0m",
                    'warning': "\033[1;33m%s\033[0m"
                }
                
    def error(self, msg):
        return self.theme.get('error', '%s') % msg
        
    def success(self, msg):
        return self.theme.get('success', '%s') % msg
        
    def info(self, msg):
        return self.theme.get('info', '%s') % msg
        
    def warning(self, msg):
        return self.theme.get('warning', '%s') % msg
            
    def _handle_sigint(self, signum, frame):
        print("\nUse 'exit' to quit")
        
    def _handle_sigterm(self, signum, frame):
        print("\nShell terminated")
        sys.exit(0)
        
    def _get_prompt(self):
        pwd = str(self.cwd)
        return self.theme.get('prompt', '%s@%s:%s$ ') % (self.user, self.hostname, pwd)
        
    def _cd(self, args):
        if not args:
            home_dir = Path(f"home/{self.user}")
            if (self.root / home_dir).exists():
                self.cwd = home_dir
            return
            
        path = args[0]
        
        if path == "-":
            print(self.error("cd: OLDPWD not set"))
            return
            
        new_path = self.cwd
        if path.startswith('/'):
            new_path = Path(path[1:])
        else:
            for part in path.split('/'):
                if part == '':
                    continue
                elif part == '.':
                    continue
                elif part == '..':
                    if new_path != Path('.'):
                        new_path = new_path.parent
                else:
                    new_path = new_path / part
        
        new_path_abs = self.root / new_path
        
        if not new_path_abs.exists():
            print(self.error(f"cd: {path}: No such file or directory"))
        elif not new_path_abs.is_dir():
            print(self.error(f"cd: {path}: Not a directory"))
        elif not os.access(new_path_abs, os.R_OK):
            print(self.error(f"cd: {path}: Permission denied"))
        else:
            if not str(new_path_abs).startswith(str(self.root)):
                print(self.error(f"cd: {path}: Access denied (cannot leave MashFS root)"))
            else:
                self.cwd = new_path
                os.environ['MASHFS_CWD'] = str(self.cwd)
        
    def _ls(self, args):
        path = "."
        if args:
            path = args[0]
            
        target_path = self.cwd
        if path.startswith('/'):
            target_path = Path(path[1:])
        else:
            target_path = self.cwd / path
            
        full_path = self.root / target_path
        
        if not full_path.exists():
            print(self.error(f"ls: {path}: No such file or directory"))
        elif not full_path.is_dir():
            print(target_path.name)
        else:
            try:
                for item in sorted(os.listdir(full_path)):
                    if (full_path / item).is_dir():
                        print(f"{self.info(item)}/")
                    else:
                        if os.access(full_path / item, os.X_OK):
                            print(f"{self.success(item)}*")
                        else:
                            print(item)
            except PermissionError:
                print(self.error(f"ls: {path}: Permission denied"))
                
    def _pwd(self, args):
        print(f"/{self.cwd}")
        
    def _clear(self, args):
        os.system('clear')
        
    def _help(self, args):
        print("Available commands:")
        for cmd in sorted(self.commands.keys()):
            print(f"  {cmd}")
            
        print("\nExternal commands:")
        bin_path = self.root / 'bin'
        if bin_path.exists() and bin_path.is_dir():
            for cmd in sorted(os.listdir(bin_path)):
                if os.access(bin_path / cmd, os.X_OK):
                    print(f"  {cmd}")
                    
    def _exit(self, args):
        print("Goodbye! 👋")
        sys.exit(0)
        
    def _su(self, args):
        target_user = 'root'
        if args:
            target_user = args[0]
            
        if target_user not in self.passwd_db:
            print(self.error(f"su: user {target_user} does not exist"))
            return
            
        password = getpass.getpass()
        
        if self.passwd_db[target_user] != password:
            print(self.error("su: Authentication failure"))
            return
            
        self.user = target_user
        
        if target_user in self.users_db:
            home_dir = self.users_db[target_user]['home']
            if home_dir.startswith('/'):
                home_dir = home_dir[1:]
            home_path = Path(home_dir)
            if (self.root / home_path).exists():
                self.cwd = home_path
                
        os.environ['USER'] = self.user
        
    def _sudo(self, args):
        if not args:
            print(self.error("sudo: no command specified"))
            return
            
        if self.user in self.sudo_users:
            cmd = args[0]
            cmd_args = args[1:]
            
            if cmd in self.commands:
                self.commands[cmd](cmd_args)
            else:
                self._run_external_command(cmd, cmd_args)
        else:
            password = getpass.getpass("[sudo] password for %s: " % self.user)
            
            if self.passwd_db.get(self.user) == password:
                cmd = args[0]
                cmd_args = args[1:]
                
                if cmd in self.commands:
                    self.commands[cmd](cmd_args)
                else:
                    self._run_external_command(cmd, cmd_args)
            else:
                print(self.error("sudo: Authentication failure"))
                
    def _whoami(self, args):
        print(self.user)
        
    def _id(self, args):
        target_user = self.user
        if args:
            target_user = args[0]
            
        if target_user not in self.users_db:
            print(self.error(f"id: {target_user}: no such user"))
            return
            
        user_info = self.users_db[target_user]
        uid = user_info['uid']
        gid = user_info['gid']
        print(f"uid={uid}({target_user}) gid={gid}({target_user})")
        
    def _useradd(self, args):
        if self.user != 'root':
            print(self.error("useradd: Permission denied (must be root)"))
            return
            
        if not args:
            print(self.error("useradd: Username required"))
            return
            
        username = args[0]
        
        if username in self.users_db:
            print(self.error(f"useradd: User {username} already exists"))
            return
            
        uid = max([int(u['uid']) for u in self.users_db.values()]) + 1
        home_dir = f"/home/{username}"
        
        self.users_db[username] = {
            'uid': str(uid),
            'gid': str(uid),
            'name': username.capitalize(),
            'home': home_dir,
            'shell': '/bin/mash'
        }
        
        with open(self.users_file, 'a') as f:
            f.write(f"{username}:x:{uid}:{uid}:{username.capitalize()}:{home_dir}:/bin/mash\n")
            
        password = getpass.getpass(f"New password for {username}: ")
        self.passwd_db[username] = password
        
        with open(self.shadow_file, 'a') as f:
            f.write(f"{username}:{password}\n")
            
        home_path = Path(home_dir[1:])
        (self.root / home_path).mkdir(exist_ok=True, parents=True)
        
        print(self.success(f"User {username} added successfully"))
        
    def _usermod(self, args):
        if self.user != 'root':
            print(self.error("usermod: Permission denied (must be root)"))
            return
            
        if not args or args[0] not in ['-aG', '-G', '-s', '-d']:
            print(self.error("usermod: Invalid option"))
            print("Usage: usermod -aG sudo USERNAME  (add to sudo group)")
            print("       usermod -s SHELL USERNAME  (change shell)")
            print("       usermod -d HOME USERNAME   (change home directory)")
            return
            
        option = args[0]
        
        if option == '-aG' and len(args) >= 3:
            group = args[1]
            username = args[2]
            
            if username not in self.users_db:
                print(self.error(f"usermod: User {username} does not exist"))
                return
                
            if group == 'sudo' and username not in self.sudo_users:
                self.sudo_users.append(username)
                print(self.success(f"User {username} added to sudo group"))
            else:
                print(self.error(f"usermod: Group {group} not supported"))
        else:
            print(self.error("usermod: Invalid arguments"))
            
    def _userdel(self, args):
        if self.user != 'root':
            print(self.error("userdel: Permission denied (must be root)"))
            return
            
        if not args:
            print(self.error("userdel: Username required"))
            return
            
        username = args[0]
        
        if username not in self.users_db:
            print(self.error(f"userdel: User {username} does not exist"))
            return
            
        del self.users_db[username]
        if username in self.passwd_db:
            del self.passwd_db[username]
            
        if username in self.sudo_users:
            self.sudo_users.remove(username)
            
        lines = []
        with open(self.users_file, 'r') as f:
            lines = [line for line in f if not line.startswith(f"{username}:")]
            
        with open(self.users_file, 'w') as f:
            f.writelines(lines)
            
        lines = []
        with open(self.shadow_file, 'r') as f:
            lines = [line for line in f if not line.startswith(f"{username}:")]
            
        with open(self.shadow_file, 'w') as f:
            f.writelines(lines)
            
        print(self.success(f"User {username} deleted successfully"))
        
    def _passwd(self, args):
        target_user = self.user
        if args:
            target_user = args[0]
            if self.user != 'root' and target_user != self.user:
                print(self.error("passwd: Permission denied (must be root to change other users' passwords)"))
                return
                
        if target_user not in self.passwd_db:
            print(self.error(f"passwd: User {target_user} does not exist"))
            return
            
        old_password = getpass.getpass("Current password: ")
        if old_password != self.passwd_db[target_user] and self.user != 'root':
            print(self.error("passwd: Authentication failure"))
            return
            
        new_password = getpass.getpass("New password: ")
        confirm_password = getpass.getpass("Confirm new password: ")
        
        if new_password != confirm_password:
            print(self.error("passwd: Passwords do not match"))
            return
            
        self.passwd_db[target_user] = new_password
        
        lines = []
        with open(self.shadow_file, 'r') as f:
            lines = []
            for line in f:
                if line.startswith(f"{target_user}:"):
                    lines.append(f"{target_user}:{new_password}\n")
                else:
                    lines.append(line)
                    
        with open(self.shadow_file, 'w') as f:
            f.writelines(lines)
            
        print(self.success(f"Password for {target_user} changed successfully"))
        
    def _hostname(self, args):
        if args:
            if self.user != 'root':
                print(self.error("hostname: Permission denied (must be root)"))
                return
                
            self.hostname = args[0]
        else:
            print(self.hostname)
            
    def _run_external_command(self, cmd, args):
        cmd_path = self.root / 'bin' / cmd
        if cmd_path.exists() and cmd_path.is_file() and os.access(cmd_path, os.X_OK):
            # Устанавливаем переменные окружения для команды
            env = os.environ.copy()
            env['MASHFS_ROOT'] = str(self.root)
            env['MASHFS_CWD'] = str(self.cwd)
            env['USER'] = self.user
            
            # Создаем строку команды
            cmd_list = [sys.executable, str(cmd_path)] + args
            
            # Запускаем команду с обновленной средой окружения
            try:
                subprocess.run(cmd_list, env=env)
            except Exception as e:
                print(self.error(f"Command failed: {e}"))
        else:
            print(self.error(f"Command not found: {cmd}"))
            
    def show_logo(self):
        logo = random.choice(self.logos)
        
        colors = [
            "\033[1;31m", 
            "\033[1;32m", 
            "\033[1;33m", 
            "\033[1;34m", 
            "\033[1;35m", 
            "\033[1;36m", 
        ]
        
        color = random.choice(colors)
        reset = "\033[0m"
        
        os.system('clear')
        for line in logo.split('\n'):
            print(f"{color}{line}{reset}")
            time.sleep(0.05)
        
        print(f"\n\033[1;36m{random.choice(self.quotes)}\033[0m\n")
        time.sleep(0.5)
        
    def run(self):
        readline.clear_history()
        os.environ['MASHFS_ROOT'] = str(self.root)
        os.environ['MASHFS_CWD'] = str(self.cwd)
        os.environ['USER'] = self.user
        
        self.show_logo()
        
        print(f"Welcome to MashFS Shell! 🚀 (Logged in as {self.user})")
        print("Type 'help' for available commands")
        print("Type 'exit' to quit")
        print("Use Tab for command and path completion")
        print(f"Current location: {self.cwd}")
        
        while True:
            try:
                readline.set_startup_hook(lambda: readline.insert_text(""))
                cmd_line = input(self._get_prompt())
                if not cmd_line:
                    continue
                    
                parts = cmd_line.split()
                cmd = parts[0]
                args = parts[1:]
                
                if cmd in self.commands:
                    self.commands[cmd](args)
                else:
                    self._run_external_command(cmd, args)
                    
            except EOFError:
                print("\nUse 'exit' to quit")
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except Exception as e:
                print(self.error(f"Error: {e}"))

def ensure_chroot_env():
    root_dir = Path(os.environ.get('MASHFS_ROOT', 'filesfs')).absolute()
    
    for d in [
        root_dir / 'home' / 'mash',
        root_dir / 'etc',
        root_dir / 'bin',
        root_dir / 'usr' / 'bin',
        root_dir / 'usr' / 'local' / 'bin',
        root_dir / 'var' / 'log',
        root_dir / 'opt',
    ]:
        d.mkdir(exist_ok=True, parents=True)
    
    bin_dir = root_dir / 'bin'
    if not (bin_dir / 'mash').exists():
        print(f"Предупреждение: Скрипт mash не найден в {bin_dir}")
    
    return root_dir

def main():
    root_dir = ensure_chroot_env()
    
    shell = MashShell()
    shell.run()

if __name__ == "__main__":
    main() 