
from database import DatabaseManager
import json
import random

def populate_database():
    """Заповнення бази даних демонстраційними даними"""
    print("=" * 50)
    print("ПОПОВНЕННЯ БАЗИ ДАНИХ ДЕМО-ДАНИМИ")
    print("=" * 50)
    
    db = DatabaseManager("adaptive_learning.db")
    
    # 1. Створюємо демо-користувача
    print("1. Створення демо-користувача...")
    user_id = db.create_user(
        username="nmt_student",
        email="student@nmt.demo",
        role="student"
    )
    print(f"   Створено користувача з ID: {user_id}")
    
    # 2. Створюємо демо-завдання
    print("\n2. Створення демо-завдань...")
    
    # Алгебра
    algebra_tasks = [
        {
            "topic": "algebra",
            "difficulty": "easy",
            "condition": "Розв'яжіть рівняння: 2x + 5 = 15",
            "question": "Знайдіть значення x",
            "answer": "5",
            "solution": ["2x = 15 - 5", "2x = 10", "x = 10 / 2", "x = 5"]
        },
        {
            "topic": "algebra",
            "difficulty": "medium",
            "condition": "Розв'яжіть систему рівнянь: x + y = 10, x - y = 2",
            "question": "Знайдіть x та y",
            "answer": "x=6, y=4",
            "solution": ["Додаємо рівняння: (x+y)+(x-y)=10+2", "2x = 12", "x = 6", "Підставляємо: 6 + y = 10", "y = 4"]
        }
    ]
    
    # Геометрія
    geometry_tasks = [
        {
            "topic": "geometry",
            "difficulty": "easy",
            "condition": "Трикутник має сторони 3 см, 4 см, 5 см",
            "question": "Чи є трикутник прямокутним?",
            "answer": "Так",
            "solution": ["3² + 4² = 9 + 16 = 25", "5² = 25", "3² + 4² = 5²", "Трикутник прямокутний за теоремою Піфагора"]
        },
        {
            "topic": "geometry",
            "difficulty": "medium",
            "condition": "Прямокутник має довжину 8 см та ширину 6 см",
            "question": "Знайдіть діагональ прямокутника",
            "answer": "10 см",
            "solution": ["d² = a² + b²", "d² = 8² + 6² = 64 + 36 = 100", "d = √100 = 10 см"]
        }
    ]
    
    # Функції
    functions_tasks = [
        {
            "topic": "functions",
            "difficulty": "easy",
            "condition": "Дано функцію f(x) = 2x + 3",
            "question": "Знайдіть f(4)",
            "answer": "11",
            "solution": ["f(4) = 2*4 + 3", "f(4) = 8 + 3", "f(4) = 11"]
        },
        {
            "topic": "functions",
            "difficulty": "medium",
            "condition": "Дано функцію f(x) = x² - 4x + 3",
            "question": "Знайдіть вершину параболи",
            "answer": "(2, -1)",
            "solution": ["x₀ = -b/(2a) = 4/(2*1) = 2", "y₀ = f(2) = 2² - 4*2 + 3 = 4 - 8 + 3 = -1", "Вершина: (2, -1)"]
        }
    ]
    
    all_tasks = algebra_tasks + geometry_tasks + functions_tasks
    
    task_ids = []
    for task in all_tasks:
        task_id = db.create_task(
            topic=task["topic"],
            difficulty=task["difficulty"],
            task_type="short_answer",
            condition=task["condition"],
            question=task["question"],
            correct_answer=task["answer"],
            solution_steps=task["solution"]
        )
        task_ids.append(task_id)
        print(f"   Створено задачу: {task['topic']} ({task['difficulty']})")
    
    print(f"   Всього створено задач: {len(task_ids)}")
    
    # 3. Створюємо демо-відповіді для історії
    print("\n3. Створення демо-відповідей...")
    
    # Симулюємо історію відповідей
    answer_history = [
        ("algebra", True, 45),
        ("algebra", False, 60),
        ("geometry", True, 30),
        ("geometry", True, 40),
        ("functions", False, 90),
        ("functions", False, 80),
    ]
    
    for i, (topic, is_correct, time_spent) in enumerate(answer_history):
        # Знаходимо задачу з відповідною темою
        topic_tasks = [t for t in all_tasks if t["topic"] == topic]
        if topic_tasks:
            task = topic_tasks[0]
            # Шукаємо ID задачі за умовою
            # У реальній системі тут був би пошук по БД
            
            # Для демо створюємо нову задачу або використовуємо існуючу
            response = task["answer"] if is_correct else "неправильна_відповідь"
            
            # Створюємо відповідь
            answer_id = db.create_answer(
                user_id=user_id,
                task_id=task_ids[i % len(task_ids)],  # Використовуємо наявні ID
                user_response=response,
                is_correct=is_correct,
                time_spent=time_spent
            )
            print(f"   Створено відповідь {i+1}: {topic} - {'✓' if is_correct else '✗'}")
    
    # 4. Показуємо статистику
    print("\n4. Статистика створених даних:")
    
    stats = db.get_user_statistics(user_id)
    print(f"   Кількість відповідей: {stats.get('total_answers', 0)}")
    print(f"   Правильних відповідей: {stats.get('correct_answers', 0)}")
    
    if stats.get('total_answers', 0) > 0:
        accuracy = stats['correct_answers'] / stats['total_answers']
        print(f"   Точність: {accuracy:.1%}")
    
    print("\n" + "=" * 50)
    print("ПОПОВНЕННЯ ЗАВЕРШЕНЕ!")
    print("=" * 50)
    
    return user_id

if __name__ == "__main__":
    user_id = populate_database()
    print(f"\nДемо-користувач готовий до роботи!")
    print(f"ID користувача для тестування: {user_id}")
