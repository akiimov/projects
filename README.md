Скрипт для извлечения характеристик ПК.
Я собирал следующие параметры:
- ОС (название, выпуск, версия, архитектура, имя компьютера) с помощью переменных os.name, os.release, os.version, os.architecture, os.computer_name
- Версию Python с помощью python.platform, python.version
- Характеристики процессора - hardware.cpu.model, hardware.cpu.physical_cores, hardware.cpu.logical_cores
- Количество оперативной памяти - hardware.ram_gb
- Количество видеокарт и их параметры - hardware.ram_gb
В ходе работы задействовал библиотеки json (вывод характеристик в отдельный файл), os(получение пути к файлу), platform(информация об ОС и железе), ctypes(чтобы вызвать системные библиотеки, такие как dll и util для поиска библиотеки по имени)

