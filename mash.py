#!/usr/bin/env python3

import os
import sys
import time
from pathlib import Path

def main():
    print("\033[1;31m" + "=" * 80 + "\033[0m")
    print("\033[1;31mВНИМАНИЕ: Этот файл устарел и больше не поддерживается!\033[0m")
    print("\033[1;31m" + "=" * 80 + "\033[0m")
    print()
    print("\033[1;33mВместо этого используйте:\033[0m")
    print("  1. \033[1;36m./filesfs/bin/mash\033[0m - для запуска MashFS оболочки")
    print("  2. \033[1;36mpython3 chrootmash.py\033[0m - для прямого запуска")
    print()
    print("\033[1;31mПрограмма завершится через 5 секунд...\033[0m")
    
    for i in range(5, 0, -1):
        sys.stdout.write(f"\r\033[1;33mЗавершение через {i} сек...\033[0m")
        sys.stdout.flush()
        time.sleep(1)
        
    print("\r\033[1;31mЗавершение работы. Используйте chrootmash.py или bin/mash.\033[0m")
    sys.exit(1)

if __name__ == "__main__":
    main() 