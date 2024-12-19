import subprocess
import json


def read_config(config_file="config.json"):
    """Читает конфигурационный файл и возвращает данные"""
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"Ошибка: файл конфигурации '{config_file}' не найден.")
        return None
    except json.JSONDecodeError:
        print("Ошибка: не удалось распарсить конфигурационный файл.")
        return None


def get_dependencies(package_name, max_depth):
    """Получить зависимости текущего пакета с помощью npm list"""
    try:
        result = subprocess.run(
            ["npm", "list", "--depth", str(max_depth), "--json"],
            capture_output=True,
            text=True,
            check=True,
            shell=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении npm list: {e}")
        return {}
    except FileNotFoundError:
        print("npm не найден, убедитесь, что Node.js и npm установлены.")
        return {}


def extract_dependencies(dependencies):
    """Извлекает зависимости и формирует словарь с именами пакетов и их зависимостями"""
    deps = {}
    if "dependencies" in dependencies:
        for dep_name, dep_data in dependencies["dependencies"].items():
            deps[dep_name] = set()  # Инициализация для каждого пакета
            if "dependencies" in dep_data:
                # Рекурсивно обрабатываем зависимость
                sub_deps = extract_dependencies(dep_data)
                deps[dep_name].update(sub_deps)
    return deps


def generate_plantuml(dependencies):
    """Генерирует код PlantUML для визуализации графа зависимостей"""
    plantuml_code = "@startuml\n"
    if not dependencies:
        plantuml_code += "    // Нет зависимостей для отображения\n"
    else:
        for dep, sub_deps in dependencies.items():
            for sub_dep in sub_deps:
                # Используем кавычки для правильной обработки имен с "@"
                plantuml_code += f'    "{dep}" --> "{sub_dep}"\n'
    plantuml_code += "@enduml"
    return plantuml_code


def save_plantuml_to_file(plantuml_code, filename="dependencies.puml"):
    """Сохраняет код PlantUML в файл"""
    with open(filename, "w") as file:
        file.write(plantuml_code)
    print(f"Файл с кодом PlantUML сохранен как {filename}")


def generate_plantuml_image(
    plantuml_file="dependencies.puml", plantuml_jar_path="plantuml.jar"
):
    """Генерирует изображение из файла PlantUML через plantuml.jar"""
    # Выполняем команду для генерации изображения из .puml
    command = ["java", "-jar", plantuml_jar_path, plantuml_file]
    try:
        subprocess.run(
            command,
            capture_output=True,
            text=True,
            shell=True,
        )
        print(f"Изображение сохранено как {plantuml_file.replace('.puml', '.png')}")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при генерации изображения: {e}")


def main():
    # Чтение конфигурации
    config = read_config()

    if not config:
        return

    # Получаем зависимости для указанного пакета
    dependencies_data = get_dependencies(config["package_name"], config["max_depth"])

    if not dependencies_data:
        print("Не удалось получить данные о зависимостях.")
        return

    # Извлекаем зависимости
    dependencies = extract_dependencies(dependencies_data)

    # Генерируем код PlantUML для графа зависимостей
    plantuml_code = generate_plantuml(dependencies)

    # Сохраняем код PlantUML в файл
    save_plantuml_to_file(plantuml_code, config["output_file"])

    # Генерируем изображение из PlantUML файла через plantuml.jar
    generate_plantuml_image(config["output_file"], config["visualization_program_path"])


if __name__ == "__main__":
    main()
