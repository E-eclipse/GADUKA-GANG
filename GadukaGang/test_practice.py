#!/usr/bin/env python
import sys
import json
from io import StringIO

def run_tests(solution_code, test_cases):
    """Запуск тестов для проверки решения"""
    import traceback
    
    results = {}
    
    # Добавляем стандартные импорты
    full_code = "import sys\nimport math\nimport random\n\n" + solution_code
    
    for i, test_case in enumerate(test_cases):
        # Инициализируем переменные
        input_data = ''
        expected_output = ''
        old_stdout = None
        
        try:
            # Подготавливаем входные данные
            input_data = test_case.get('input', '')
            expected_output = test_case.get('output', '')
            
            # Перенаправляем stdout для захвата вывода
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()
            
            # Выполняем код с входными данными
            if input_data:
                # Если есть входные данные, создаем функцию для их имитации
                exec(full_code + f"\n\n# Test input simulation\nimport sys\nsys.stdin = StringIO('''{input_data}''')\n\n# Execute main function if exists\nif 'main' in locals():\n    main()", {'StringIO': StringIO, '__name__': '__main__'})
            else:
                exec(full_code, {'__name__': '__main__'})
            
            # Восстанавливаем stdout
            sys.stdout = old_stdout
            
            # Получаем вывод
            actual_output = captured_output.getvalue().strip()
            expected_output = str(expected_output).strip()
            
            # Сравниваем результаты
            passed = actual_output == expected_output
            
            results[f'test_{i+1}'] = {
                'input': input_data,
                'expected': expected_output,
                'actual': actual_output,
                'passed': passed
            }
            
        except Exception as e:
            # Восстанавливаем stdout в случае ошибки
            if old_stdout is not None:
                sys.stdout = old_stdout
            
            results[f'test_{i+1}'] = {
                'input': input_data,
                'expected': expected_output,
                'actual': f"Error: {str(e)}",
                'passed': False,
                'error': traceback.format_exc()
            }
    
    return results

# Тестовый пример
if __name__ == "__main__":
    # Пример решения
    solution_code = """
def main():
    a = int(input())
    b = int(input())
    print(a + b)

if __name__ == "__main__":
    main()
"""
    
    # Тестовые случаи
    test_cases = [
        {
            'input': '2\n3',
            'output': '5'
        },
        {
            'input': '10\n20',
            'output': '30'
        }
    ]
    
    # Запускаем тесты
    results = run_tests(solution_code, test_cases)
    
    # Выводим результаты
    print(json.dumps(results, indent=2, ensure_ascii=False))