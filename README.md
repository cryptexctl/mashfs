# MashFS - Простой Shell

Что-то вроде фс на питоне

![MashFS Demo](assets-gh/demo.gif)

## Структура проекта

- `chrootmash.py` - основной файл шелла (новая версия)
- `filesfs/` - виртуальная файловая система
- `filesfs/bin/mash` - скрипт запуска шелла

## Запуск

```bash
# Из корня проекта
python3 chrootmash.py

# Или через скрипт
cd filesfs && ./bin/mash
```

### Пароли по умолчанию
```
root:toor
mash:mashka
arbung:kadzimoment
```

## Пакетный менеджер

- `packman add <package>` - добавить и включить пакет
- `packman remove <package>` - полностью удалить пакет
- `packman install <package>` - установить пакет
- `packman enable <package>` - включить пакет
- `packman disable <package>` - отключить пакет
- `packman list` - показать список всех пакетов
- `packman info <package>` - информация о пакете

## Управление системой MashFS

Для обновления и управления системой используйте команду `mashsys`:

```bash
# Проверить текущую версию и статус
mashsys version
mashsys status

# Обновиться до последней версии
mashsys upgrade

# Переключиться на другую ветку
mashsys switch beta

# Откатиться к предыдущей версии
mashsys rollback

# Показать список доступных веток и релизов
mashsys list branches
mashsys list releases

# Показать справку
mashsys help
```

### Обновление системы

Команда `mashsys upgrade` автоматически:
1. Создает резервную копию текущей системы
2. Загружает последнюю версию из GitHub репозитория
3. Обновляет файлы, сохраняя пользовательские настройки
4. Обновляет права доступа файлов

Репозиторий GitHub: [https://github.com/cryptexctl/mashfs/tree/main](https://github.com/cryptexctl/mashfs/tree/main)
