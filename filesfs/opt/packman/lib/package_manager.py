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
                
        self._install_pip_dependencies(package_name)
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
        self._install_pip_dependencies(package_name)
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