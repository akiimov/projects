Скрипт для извлечения характеристик ПК.
Я собирал следующие параметры:
- ОС: platform.system() platform.release()), platform.machine()
- Характеристики процессора: cpu (название модели), logical_cores
- Количество оперативной памяти: ram_gb
- Количество видеокарт и их параметры: gpu (список названий видеокарт)

Использованные библиотеки
- json: сохранение характеристик в отдельный файл pc_specs.json (функция save_to_file)
- os: получение числа логических ядер (os.cpu_count()) и размера памяти на macOS (os.sysconf)
- platform: определение системы (Windows, Linux, Darwin), версии ОС и архитектуры
- ctypes: вызов системных библиотек: kernel32.dll на Windows (GetPhysicallyInstalledSystemMemory) и libc на macOS (sysctlbyname)
- winreg (только Windows): чтение названия процессора и видеокарт из реестра
