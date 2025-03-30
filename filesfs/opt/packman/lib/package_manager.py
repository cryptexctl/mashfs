#!/usr/bin/env python3
import os
import sys
import yaml
import json
import shutil
import subprocess
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
import time
import random
from tqdm import tqdm

class PackageManager:
    def __init__(self, root_dir=None):
        self.root = root_dir if root_dir else Path(os.environ.get('MASHFS_ROOT', 'filesfs')).absolute()
        self.config_dir = self.root / 'opt' / 'packman'
        self.config_file = self.config_dir / 'config.yml'
        self.repos_dir = self.config_dir / 'repos'
        self.packages_dir = self.config_dir / 'packages'
        self.cached_dir = self.config_dir / 'cached'
        self.enabled_dir = self.config_dir / 'enabled'
        self.disabled_dir = self.config_dir / 'disabled'
        self.bin_dir = self.root / 'bin'
        
        self.config = self._load_config()
        self.repos = self._load_repos()
        
        for dir_path in [self.repos_dir, self.packages_dir, self.cached_dir, 
                        self.enabled_dir, self.disabled_dir, self.bin_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> Dict:
        if self.config_file.exists():
            with open(self.config_file) as f:
                return yaml.safe_load(f)
        return {}

    def _save_config(self) -> None:
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config, f)

    def _load_repos(self) -> Dict:
        repos = {}
        if self.repos_dir.exists():
            for repo_file in self.repos_dir.glob('*.yml'):
                with open(repo_file) as f:
                    repos[repo_file.stem] = yaml.safe_load(f)
        return repos

    def _get_package_info(self, package_name: str) -> Optional[Dict]:
        package_dir = self.packages_dir / package_name
        info_file = package_dir / 'info.json'
        
        if info_file.exists():
            with open(info_file) as f:
                return json.load(f)
                
        for repo_name, repo in self.repos.items():
            if package_name in repo.get('packages', {}):
                return repo['packages'][package_name]
        return None

    def _install_pip_dependencies(self, package_path):
        pip_deps_file = package_path / 'pip_dependencies'
        if pip_deps_file.exists():
            with open(pip_deps_file) as f:
                for dep in f.read().splitlines():
                    if dep.strip():
                        os.system(f"pip install {dep}")

    def _link_binaries(self, package_name: str) -> None:
        package_dir = self.packages_dir / package_name
        bin_dir = package_dir / 'bin'
        
        if bin_dir.exists() and bin_dir.is_dir():
            for bin_file in bin_dir.iterdir():
                if bin_file.is_file():
                    target_path = self.bin_dir / bin_file.name
                    if target_path.exists():
                        target_path.unlink()
                    target_path.symlink_to(bin_file)
                    os.chmod(bin_file, 0o755)  # Make executable
                    print(f"Linked binary: {bin_file.name}")

    def _run_script(self, package_name: str, script_type: str) -> None:
        package_dir = self.packages_dir / package_name
        script_file = package_dir / f'{script_type}.sh'
        
        if script_file.exists():
            print(f"Running {script_type} script for {package_name}...")
            subprocess.run(['bash', str(script_file)], check=True)

    def _simulate_installation(self, package_name: str) -> None:
        steps = [
            "Checking dependencies...",
            "Downloading package...",
            "Verifying package integrity...",
            "Extracting files...",
            "Installing components...",
            "Configuring package...",
            "Cleaning up..."
        ]
        
        for step in tqdm(steps, desc=f"Installing {package_name}"):
            time.sleep(random.uniform(0.5, 1.0))

    def add(self, package_name: str) -> int:
        package_info = self._get_package_info(package_name)
        if not package_info:
            print(f"Package {package_name} not found in any repository")
            return 1
            
        if 'dependencies' in package_info:
            for dep in package_info['dependencies']:
                if not (self.enabled_dir / dep).exists():
                    print(f"Installing dependency: {dep}")
                    self.add(dep)
                    
        self._simulate_installation(package_name)
        
        package_dir = self.packages_dir / package_name
        if package_dir.exists():
            shutil.copytree(package_dir, self.cached_dir / package_name, dirs_exist_ok=True)
            
        enabled_path = self.enabled_dir / package_name
        if not enabled_path.exists():
            if (self.cached_dir / package_name).exists():
                shutil.copytree(self.cached_dir / package_name, enabled_path, dirs_exist_ok=True)
            else:
                shutil.copytree(package_dir, enabled_path, dirs_exist_ok=True)
                
        self._install_pip_dependencies(package_dir)
        self._link_binaries(package_name)
        self._run_script(package_name, 'install')
        
        print(f"Package {package_name} added and enabled successfully")
        return 0

    def remove(self, package_name: str) -> int:
        removed = False
        for dir_path in [self.cached_dir, self.enabled_dir, self.disabled_dir]:
            package_path = dir_path / package_name
            if package_path.exists():
                shutil.rmtree(package_path)
                removed = True
                
        package_dir = self.packages_dir / package_name
        if package_dir.exists():
            bin_dir = package_dir / 'bin'
            if bin_dir.exists() and bin_dir.is_dir():
                for bin_file in bin_dir.iterdir():
                    if bin_file.is_file():
                        target_path = self.bin_dir / bin_file.name
                        if target_path.exists() and target_path.is_symlink():
                            target_path.unlink()
                            print(f"Removed binary: {bin_file.name}")
        
        if removed:
            print(f"Package {package_name} removed successfully")
            return 0
        else:
            print(f"Package {package_name} not found")
            return 1

    def install(self, package_name: str) -> int:
        package_dir = self.packages_dir / package_name
        if not package_dir.exists():
            print(f"Package {package_name} not found")
            return 1
            
        self._simulate_installation(package_name)
        
        shutil.copytree(package_dir, self.cached_dir / package_name, dirs_exist_ok=True)
        self._install_pip_dependencies(package_dir)
        self._link_binaries(package_name)
        self._run_script(package_name, 'install')
        
        print(f"Package {package_name} installed successfully")
        return 0

    def disable(self, package_name: str) -> int:
        enabled_path = self.enabled_dir / package_name
        disabled_path = self.disabled_dir / package_name
        
        if enabled_path.exists():
            if disabled_path.exists():
                shutil.rmtree(disabled_path)
            shutil.move(enabled_path, disabled_path)
            
            package_dir = self.packages_dir / package_name
            if package_dir.exists():
                bin_dir = package_dir / 'bin'
                if bin_dir.exists() and bin_dir.is_dir():
                    for bin_file in bin_dir.iterdir():
                        if bin_file.is_file():
                            target_path = self.bin_dir / bin_file.name
                            if target_path.exists() and target_path.is_symlink():
                                target_path.unlink()
                                print(f"Removed binary: {bin_file.name}")
            
            print(f"Package {package_name} disabled")
            return 0
        else:
            print(f"Package {package_name} is not enabled")
            return 1

    def enable(self, package_name: str) -> int:
        enabled_path = self.enabled_dir / package_name
        disabled_path = self.disabled_dir / package_name
        package_dir = self.packages_dir / package_name
        
        if disabled_path.exists():
            if enabled_path.exists():
                shutil.rmtree(enabled_path)
            shutil.move(disabled_path, enabled_path)
            
            if package_dir.exists():
                self._link_binaries(package_name)
                
            print(f"Package {package_name} enabled")
            return 0
        elif package_dir.exists():
            if enabled_path.exists():
                shutil.rmtree(enabled_path)
            shutil.copytree(package_dir, enabled_path)
            
            self._link_binaries(package_name)
            print(f"Package {package_name} enabled")
            return 0
        else:
            print(f"Package {package_name} is not disabled or does not exist")
            return 1

    def doctor(self, fix=False):
        print(f"Запуск диагностики пакетов...")
        issues_found = False
        packages_to_fix = []
        
        enabled_packages = [p.name for p in self.enabled_dir.iterdir() if p.is_dir()]
        
        for package_name in enabled_packages:
            print(f"Проверка пакета: {package_name}")
            package_path = self.enabled_dir / package_name
            
            info_path = package_path / 'info.json'
            if not info_path.exists():
                issues_found = True
                print(f"  ОШИБКА: Файл info.json отсутствует для пакета {package_name}")
                continue
                
            try:
                with open(info_path) as f:
                    info = json.load(f)
            except json.JSONDecodeError:
                issues_found = True
                print(f"  ОШИБКА: Файл info.json поврежден для пакета {package_name}")
                continue
            
            missing_deps = []
            if 'dependencies' in info:
                for dep in info['dependencies']:
                    if not (self.enabled_dir / dep).exists():
                        issues_found = True
                        missing_deps.append(dep)
                        print(f"  ОШИБКА: Зависимость '{dep}' отсутствует для пакета {package_name}")
            
            pip_deps_file = package_path / 'pip_dependencies'
            missing_pip_deps = []
            if pip_deps_file.exists():
                with open(pip_deps_file) as f:
                    for dep in f.read().splitlines():
                        if dep.strip():
                            try:
                                __import__(dep.split('==')[0].split('>')[0].split('<')[0].strip())
                            except ImportError:
                                issues_found = True
                                missing_pip_deps.append(dep)
                                print(f"  ОШИБКА: Python-зависимость '{dep}' отсутствует для пакета {package_name}")
            
            bin_dir = package_path / 'bin'
            if bin_dir.exists():
                for script in bin_dir.iterdir():
                    if not os.access(script, os.X_OK) and script.is_file():
                        issues_found = True
                        print(f"  ПРЕДУПРЕЖДЕНИЕ: Скрипт '{script.name}' не является исполняемым")
                        if fix:
                            os.chmod(script, 0o755)
                            print(f"  ИСПРАВЛЕНО: Права доступа для '{script.name}' установлены на 755")
            
            if missing_deps or missing_pip_deps:
                packages_to_fix.append({
                    'name': package_name,
                    'missing_deps': missing_deps,
                    'missing_pip_deps': missing_pip_deps
                })
        
        if not issues_found:
            print("Диагностика завершена. Проблем не обнаружено!")
            return True
        
        if fix and packages_to_fix:
            print("\nИсправление проблем...")
            for package_info in packages_to_fix:
                package_name = package_info['name']
                print(f"Исправление проблем пакета {package_name}...")
                
                for dep in package_info['missing_deps']:
                    print(f"  Установка зависимости: {dep}")
                    self.install(dep)
                
                for dep in package_info['missing_pip_deps']:
                    print(f"  Установка Python-зависимости: {dep}")
                    os.system(f"pip install {dep}")
                
                print(f"Исправление пакета {package_name} завершено")
            
            print("\nВсе проблемы исправлены!")
            return True
        elif fix:
            print("\nНет проблем, требующих исправления.")
            return True
        else:
            print("\nДиагностика завершена с ошибками. Запустите 'packman doctor --fix' для исправления проблем.")
            return False 