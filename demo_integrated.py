
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from database import DatabaseManager
from bayesian_network import SimpleBayesianNetwork
import json

class NMTBayesianDemo:
    def __init__(self, root):
        self.root = root
        self.root.title("Байєсова мережа для НМТ - Демо")
        self.root.geometry("900x700")
        
        # Ініціалізація
        self.db = DatabaseManager("adaptive_learning.db")
        self.bn = SimpleBayesianNetwork()
        
        # ID демо-користувача
        self.user_id = self.get_demo_user()
        
        # Завантаження або створення моделі
        self.load_or_create_model()
        
        # Налаштування GUI
        self.setup_ui()
        
        # Оновлення відображення
        self.update_display()
    
    def get_demo_user(self):
        """Отримання ID демо-користувача"""
        user = self.db.get_user_by_email("student@nmt.demo")
        if user:
            return user['id']
        else:
            messagebox.showwarning("Увага", 
                "Демо-користувач не знайдений.\n"
                "Запустіть populate_database.py для створення даних.")
            return None
    
    def load_or_create_model(self):
        """Завантаження або створення моделі"""
        if not self.user_id:
            return
        
        # Намагаємося завантажити модель з БД
        loaded = self.bn.load_from_database(self.db, self.user_id)
        
        if not loaded:
            # Якщо моделі немає, створюємо нову
            print("Створення нової Байєсової мережі...")
            self.bn.build_network()
            self.bn.save_to_database(self.db, self.user_id)
    
    def setup_ui(self):
        """Налаштування графічного інтерфейсу"""
        # Заголовок
        title = tk.Label(self.root, 
            text="🎓 Байєсова мережа для підготовки до НМТ",
            font=("Arial", 16, "bold"),
            fg="darkblue"
        )
        title.pack(pady=10)
        
        # Основний контейнер
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Ліва панель - стан знань
        left_panel = tk.LabelFrame(main_container, text="📊 Поточний стан знань", font=("Arial", 12, "bold"))
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.knowledge_text = scrolledtext.ScrolledText(left_panel, height=15, width=40)
        self.knowledge_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Права панель - управління
        right_panel = tk.LabelFrame(main_container, text="🎯 Управління", font=("Arial", 12, "bold"))
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Симуляція відповідей
        sim_frame = tk.Frame(right_panel)
        sim_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(sim_frame, text="Симуляція відповіді:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        # Вибір теми
        topic_frame = tk.Frame(right_panel)
        topic_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(topic_frame, text="Тема:").pack(side=tk.LEFT)
        
        self.topic_var = tk.StringVar(value="algebra")
        topics = [("Алгебра", "algebra"), ("Геометрія", "geometry"), ("Функції", "functions")]
        
        for text, value in topics:
            tk.Radiobutton(topic_frame, text=text, variable=self.topic_var, 
                          value=value).pack(side=tk.LEFT, padx=5)
        
        # Кнопки симуляції
        button_frame = tk.Frame(right_panel)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="✅ Правильна відповідь",
                 command=lambda: self.simulate_answer(True),
                 bg="lightgreen", width=20).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="❌ Неправильна відповідь",
                 command=lambda: self.simulate_answer(False),
                 bg="lightcoral", width=20).pack(side=tk.LEFT, padx=5)
        
        # Прогнозування
        predict_frame = tk.Frame(right_panel)
        predict_frame.pack(fill=tk.X, pady=20)
        
        tk.Button(predict_frame, text="🔮 Прогнозувати успішність",
                 command=self.predict_success,
                 bg="lightblue", width=25).pack()
        
        # Рекомендації
        tk.Button(predict_frame, text="💡 Отримати рекомендацію",
                 command=self.get_recommendation,
                 bg="gold", width=25).pack(pady=5)
        
        # Результати
        result_frame = tk.LabelFrame(right_panel, text="📝 Результати", font=("Arial", 10, "bold"))
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.result_text = tk.Text(result_frame, height=8, width=40)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Статистика
        stats_frame = tk.LabelFrame(self.root, text="📈 Статистика", font=("Arial", 12, "bold"))
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.stats_text = tk.Text(stats_frame, height=4, width=100)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Панель управління
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10)
        
        tk.Button(control_frame, text="🔄 Оновити",
                 command=self.update_display).pack(side=tk.LEFT, padx=5)
        
        tk.Button(control_frame, text="💾 Зберегти модель",
                 command=self.save_model).pack(side=tk.LEFT, padx=5)
        
        tk.Button(control_frame, text="📊 Граф мережі",
                 command=self.show_network_graph).pack(side=tk.LEFT, padx=5)
    
    def update_display(self):
        """Оновлення всіх відображень"""
        self.update_knowledge_display()
        self.update_statistics_display()
        self.result_text.delete(1.0, tk.END)
    
    def update_knowledge_display(self):
        """Оновлення відображення стану знань"""
        self.knowledge_text.delete(1.0, tk.END)
        
        if not self.bn.current_state:
            self.knowledge_text.insert(tk.END, "Модель не завантажена\n")
            return
        
        self.knowledge_text.insert(tk.END, "РІВНІ ЗНАНЬ:\n")
        self.knowledge_text.insert(tk.END, "="*30 + "\n\n")
        
        for topic, dist in self.bn.current_state.items():
            topic_name = {
                'Algebra': 'Алгебра',
                'Geometry': 'Геометрія',
                'Functions': 'Функції'
            }.get(topic, topic)
            
            low_prob = dist.get('Low', 0)
            high_prob = dist.get('High', 0)
            
            # Прогрес-бар для високого рівня
            progress = int(high_prob * 100)
            bar = "█" * (progress // 5) + "░" * (20 - progress // 5)
            
            self.knowledge_text.insert(tk.END, 
                f"{topic_name:10} {bar} {progress:3}%\n")
            self.knowledge_text.insert(tk.END,
                f"   Низький: {low_prob:.1%}, Високий: {high_prob:.1%}\n\n")
    
    def update_statistics_display(self):
        """Оновлення статистики"""
        self.stats_text.delete(1.0, tk.END)
        
        if not self.user_id:
            self.stats_text.insert(tk.END, "Користувач не знайдений\n")
            return
        
        stats = self.db.get_user_statistics(self.user_id)
        
        self.stats_text.insert(tk.END, "СТАТИСТИКА ВІДПОВІДЕЙ:\n")
        self.stats_text.insert(tk.END, "="*40 + "\n\n")
        
        total = stats.get('total_answers', 0)
        correct = stats.get('correct_answers', 0)
        
        self.stats_text.insert(tk.END, f"Всього відповідей: {total}\n")
        
        if total > 0:
            accuracy = correct / total
            self.stats_text.insert(tk.END, f"Правильних: {correct}\n")
            self.stats_text.insert(tk.END, f"Точність: {accuracy:.1%}\n")
        
        # Статистика по темах
        if 'by_topic' in stats:
            self.stats_text.insert(tk.END, "\nПО ТЕМАХ:\n")
            for topic_stat in stats['by_topic']:
                topic = topic_stat['topic']
                total_t = topic_stat['total']
                correct_t = topic_stat['correct']
                
                if total_t > 0:
                    accuracy_t = correct_t / total_t
                    topic_name = {
                        'algebra': 'Алгебра',
                        'geometry': 'Геометрія',
                        'functions': 'Функції'
                    }.get(topic, topic)
                    
                    self.stats_text.insert(tk.END, 
                        f"  {topic_name:10} {accuracy_t:.0%} ({correct_t}/{total_t})\n")
    
    def simulate_answer(self, is_correct):
        """Симуляція відповіді учня"""
        if not self.user_id:
            messagebox.showerror("Помилка", "Користувач не знайдений")
            return
        
        topic = self.topic_var.get()
        
        try:
            # Оновлюємо Байєсову мережу
            p = self.bn.update_from_answer(is_correct, topic)
            
            # Зберігаємо оновлену модель
            self.bn.save_to_database(self.db, self.user_id)
            
            # Створюємо запис у БД
            # Знаходимо задачу з відповідною темою
            tasks = self.db.get_tasks_by_topic(topic, limit=1)
            
            if tasks:
                task = tasks[0]
                # Створюємо відповідь
                response = "симульована_відповідь"
                if is_correct:
                    response = task['correct_answer']
                
                self.db.create_answer(
                    user_id=self.user_id,
                    task_id=task['id'],
                    user_response=response,
                    is_correct=is_correct,
                    time_spent=60  # фіксований час для демо
                )
            
            # Оновлюємо відображення
            self.update_display()
            
            status = "ПРАВИЛЬНА" if is_correct else "НЕПРАВИЛЬНА"
            messagebox.showinfo("Симуляція",
                f"ЗАДАЧА {str(tasks[0]['condition'])}\n"
                f"{str(tasks[0]['question'])}\n"            
                f"ВІДПОВІДЬ {str(tasks[0]['correct_answer'])}\n"
                f"Відповідь зареєстрована як {status}!\n"
                f"Тема: {topic}\n"
                f"Байєсова мережа оновлена.")
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка симуляції: {e}")
    
    def predict_success(self):
        """Прогнозування успішності"""
        self.result_text.delete(1.0, tk.END)
        
        if not self.bn.current_state:
            self.result_text.insert(tk.END, "Модель не завантажена\n")
            return
        
        self.result_text.insert(tk.END, "ПРОГНОЗ УСПІШНОСТІ:\n")
        self.result_text.insert(tk.END, "="*30 + "\n\n")
        
        # Прогноз для кожної теми
        topics = ['algebra', 'geometry', 'functions']
        topic_names = {
            'algebra': 'Алгебра',
            'geometry': 'Геометрія',
            'functions': 'Функції'
        }
        
        for topic in topics:
            success_prob = self.bn.predict_success(topic)
            progress = int(success_prob * 100)
            bar = "█" * (progress // 5) + "░" * (20 - progress // 5)
            
            self.result_text.insert(tk.END, 
                f"{topic_names[topic]:10} {bar} {progress:3}%\n")
            self.result_text.insert(tk.END,
                f"   Ймовірність успіху: {success_prob:.1%}\n\n")
        
        # Загальний прогноз
        avg_success = sum([self.bn.predict_success(t) for t in topics]) / 3
        
        self.result_text.insert(tk.END, "="*30 + "\n")
        self.result_text.insert(tk.END, f"\n📊 ЗАГАЛЬНИЙ ПРОГНОЗ: {avg_success:.1%}\n")
        
        # Інтерпретація
        if avg_success > 0.7:
            interpretation = "✅ Високий рівень готовності"
        elif avg_success > 0.5:
            interpretation = "🟡 Середній рівень"
        else:
            interpretation = "🔴 Низький рівень"
        
        self.result_text.insert(tk.END, f"\n{interpretation}\n")
    
    def get_recommendation(self):
        """Отримання рекомендації"""
        self.result_text.delete(1.0, tk.END)
        
        if not self.bn.current_state:
            self.result_text.insert(tk.END, "Модель не завантажена\n")
            return
        
        weakest = self.bn.get_weakest_topic()
        
        topic_names = {
            'algebra': 'Алгебра',
            'geometry': 'Геометрія',
            'functions': 'Функції'
        }
        
        weakest_name = topic_names.get(weakest, weakest)
        
        self.result_text.insert(tk.END, "💡 РЕКОМЕНДАЦІЯ СИСТЕМИ\n")
        self.result_text.insert(tk.END, "="*30 + "\n\n")
        
        self.result_text.insert(tk.END, f"Найслабша тема: {weakest_name}\n\n")
        
        # Конкретні рекомендації
        if weakest == 'algebra':
            self.result_text.insert(tk.END, "Рекомендовані вправи:\n")
            self.result_text.insert(tk.END, "• Розв'язування лінійних рівнянь\n")
            self.result_text.insert(tk.END, "• Робота з алгебраїчними виразами\n")
            self.result_text.insert(tk.END, "• Системи рівнянь\n")
        elif weakest == 'geometry':
            self.result_text.insert(tk.END, "Рекомендовані вправи:\n")
            self.result_text.insert(tk.END, "• Теорема Піфагора\n")
            self.result_text.insert(tk.END, "• Властивості трикутників\n")
            self.result_text.insert(tk.END, "• Обчислення площ та об'ємів\n")
        else:  # functions
            self.result_text.insert(tk.END, "Рекомендовані вправи:\n")
            self.result_text.insert(tk.END, "• Властивості функцій\n")
            self.result_text.insert(tk.END, "• Побудова графіків\n")
            self.result_text.insert(tk.END, "• Похідні функцій\n")
        
        self.result_text.insert(tk.END, "\n💡 Порада: Практикуйте цю тему 20 хвилин щодня")
    
    def save_model(self):
        """Збереження моделі в БД"""
        if not self.user_id:
            messagebox.showerror("Помилка", "Користувач не знайдений")
            return
        
        self.bn.save_to_database(self.db, self.user_id)
        messagebox.showinfo("Збереження", "Модель успішно збережена в базі даних")
    
    def show_network_graph(self):
        """Відображення графа мережі"""
        try:
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # Простий граф
            nodes = ['Algebra', 'Geometry', 'Functions', 'Result']
            edges = [('Algebra', 'Result'), ('Geometry', 'Result'), ('Functions', 'Result')]
            
            # Позиції
            pos = {
                'Algebra': (0, 1),
                'Geometry': (0, 0),
                'Functions': (0, -1),
                'Result': (2, 0)
            }
            
            # Малюємо ребра
            for src, dst in edges:
                xs, ys = pos[src]
                xd, yd = pos[dst]
                ax.plot([xs, xd], [ys, yd], 'k-', alpha=0.5, linewidth=2)
                # Стрілка
                ax.annotate('', xy=(xd, yd), xytext=(xs, ys),
                           arrowprops=dict(arrowstyle='->', color='gray', lw=1))
            
            # Малюємо вузли
            for node, (x, y) in pos.items():
                color = 'lightblue' if node != 'Result' else 'lightgreen'
                circle = plt.Circle((x, y), 0.3, color=color, ec='black', lw=2)
                ax.add_patch(circle)
                ax.text(x, y, node, ha='center', va='center', fontsize=10, fontweight='bold')
            
            ax.set_xlim(-1, 3)
            ax.set_ylim(-2, 2)
            ax.set_aspect('equal')
            ax.axis('off')
            ax.set_title("Структура Байєсової мережі для НМТ", fontsize=12, fontweight='bold')
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося побудувати граф: {e}")

if __name__ == "__main__":
    print("Запуск демонстрації Байєсової мережі для НМТ...")
    print("=" * 50)
    print("Спочатку запустіть populate_database.py для створення демо-даних")
    print("=" * 50)
    
    root = tk.Tk()
    app = NMTBayesianDemo(root)
    root.mainloop()
