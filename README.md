# MashFS - Простой Shell

Что-то вроде фс на питоне

![MashFS Demo](https://asciinema.org/a/BgK8iO0YIxlYceF6edKe5aAsZ?t=7)

## Структура проекта

- `mash.py` - основной файл шелла
- `filesfs/` - виртуальная файловая система

### Основные команды в основном из линукса 

## Пакетый менджер

- `packman add <package>` - включает (и устанавливает если не было этого пакета) пакет в шелле
- `packman rm <packge>` - выключает пакет в шелле
- `packman remove <package>` - удаляет и его не включить
- `packman install <package>` - установить

## Запуск

```bash
python3 mash.py
```

### Пароли по умолчанию
```
mash:mash123
root:root123
