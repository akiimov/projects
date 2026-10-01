Скрипт для извлечения характеристик ПК.
Я собирал следующие параметры:
- ОС: os (строка вида «система + версия», например Windows 11; собирается из platform.system() и platform.release()), architecture (из platform.machine())
- Характеристики процессора: cpu (название модели), logical_cores (число логических ядер, из os.cpu_count())
- Количество оперативной памяти: ram_gb
- Количество видеокарт и их параметры: gpu (список названий видеокарт)

Использованные библиотеки
json: сохранение характеристик в отдельный файл pc_specs.json (функция save_to_file)
os: получение числа логических ядер (os.cpu_count()) и размера памяти на macOS (os.sysconf)
platform: определение системы (Windows, Linux, Darwin), версии ОС и архитектуры
ctypes: вызов системных библиотек: kernel32.dll на Windows (GetPhysicallyInstalledSystemMemory) и libc на macOS (sysctlbyname)
winreg (только Windows): чтение названия процессора и видеокарт из реестра
