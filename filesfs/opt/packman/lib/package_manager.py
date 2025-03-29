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
    def __init__(self):
        self.root = Path(os.environ.get('MASHFS_ROOT', 'filesfs')).absolute()
        self.config_dir = self.root / 'opt' / 'packman'
        self.config_file = self.config_dir / 'config.yml'
        self.repos_dir = self.config_dir / 'repos'
        self.packages_dir = self.config_dir / 'packages'
        self.cached_dir = self.config_dir / 'cached'
        self.enabled_dir = self.root / 'opt' / 'enabled'
        self.disabled_dir = self.root / 'opt' / 'disabled'
        self.lib_dir = self.root / 'opt' / 'lib'
        
        self.config = self._load_config()
        self.repos = self._load_repos()
        
        for dir_path in [self.repos_dir, self.packages_dir, self.cached_dir, 
                        self.enabled_dir, self.disabled_dir, self.lib_dir]:
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
        for repo_name, repo in self.repos.items():
            if package_name in repo.get('packages', {}):
                return repo['packages'][package_name]
        return None

    def _install_pip_dependencies(self, package_name: str) -> None:
        package_dir = self.packages_dir / package_name
        deps_file = package_dir / 'pip_dependencies'
        
        if deps_file.exists():
            with open(deps_file) as f:
                deps = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                
            if deps:
                print(f"Installing Python dependencies for {package_name}...")
                for dep in deps:
                    subprocess.run([sys.executable, '-m', 'pip', 'install', dep], check=True)

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
            time.sleep(random.uniform(0.5, 1.5))

    def add(self, package_name: str) -> None:
        package_info = self._get_package_info(package_name)
        if not package_info:
            print(f"Package {package_name} not found in any repository")
            return
            
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
            shutil.copytree(self.cached_dir / package_name, enabled_path)
            
        self._install_pip_dependencies(package_name)
        self._run_script(package_name, 'install')

    def remove(self, package_name: str) -> None:
        for dir_path in [self.cached_dir, self.enabled_dir, self.disabled_dir]:
            package_path = dir_path / package_name
            if package_path.exists():
                shutil.rmtree(package_path)

    def install(self, package_name: str) -> None:
        self._simulate_installation(package_name)
        
        package_dir = self.packages_dir / package_name
        if package_dir.exists():
            shutil.copytree(package_dir, self.cached_dir / package_name, dirs_exist_ok=True)
            
        self._install_pip_dependencies(package_name)
        self._run_script(package_name, 'install')

    def disable(self, package_name: str) -> None:
        enabled_path = self.enabled_dir / package_name
        disabled_path = self.disabled_dir / package_name
        
        if enabled_path.exists():
            if disabled_path.exists():
                shutil.rmtree(disabled_path)
            shutil.move(enabled_path, disabled_path)
            print(f"Package {package_name} disabled")
        else:
            print(f"Package {package_name} is not enabled")

    def enable(self, package_name: str) -> None:
        enabled_path = self.enabled_dir / package_name
        disabled_path = self.disabled_dir / package_name
        
        if disabled_path.exists():
            if enabled_path.exists():
                shutil.rmtree(enabled_path)
            shutil.move(disabled_path, enabled_path)
            print(f"Package {package_name} enabled")
        else:
            print(f"Package {package_name} is not disabled") 