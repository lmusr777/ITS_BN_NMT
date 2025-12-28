
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination
import numpy as np

class SimpleBayesianNetwork:
    """Проста Байєсова мережа для задач НМТ"""
    
    def __init__(self):
        self.model = None
        self.inference = None
        self.current_state = {}
        # Зберігаємо поточні CPT окремо
        self.skill_cpds = {
            'Algebra': np.array([[0.6], [0.4]]),
            'Geometry': np.array([[0.5], [0.5]]),
            'Functions': np.array([[0.7], [0.3]])
        }
        
    def build_network(self):
        """Побудова простої мережі з 3 темами"""
        self.model = DiscreteBayesianNetwork()
        
        # Додаємо вузли
        self.model.add_nodes_from(['Algebra', 'Geometry', 'Functions', 'Result'])
        
        # Додаємо зв'язки
        self.model.add_edges_from([
            ('Algebra', 'Result'),
            ('Geometry', 'Result'),
            ('Functions', 'Result')
        ])
        
        # Задаємо CPT
        self._set_cpds()
        
        # Перевірка моделі
        self.model.check_model()
        
        # Ініціалізація інференсу
        self.inference = VariableElimination(self.model)
        
        # Початковий стан
        self.current_state = self.get_prior_distribution()
        
        return self.model
    
    def _set_cpds(self):
        """Задання таблиць ймовірностей"""
        
        # CPT для Algebra
        cpd_algebra = TabularCPD(
            variable='Algebra',
            variable_card=2,
            values=[[0.6], [0.4]],  # Низький, Високий
            state_names={'Algebra': ['Low', 'High']}
        )
        
        # CPT для Geometry
        cpd_geometry = TabularCPD(
            variable='Geometry',
            variable_card=2,
            values=[[0.5], [0.5]],
            state_names={'Geometry': ['Low', 'High']}
        )
        
        # CPT для Functions
        cpd_functions = TabularCPD(
            variable='Functions',
            variable_card=2,
            values=[[0.7], [0.3]],
            state_names={'Functions': ['Low', 'High']}
        )
        
        # CPT для Result (спрощено - лише 8 комбінацій)
        cpd_result = TabularCPD(
            variable='Result',
            variable_card=2,
            values=[
                # P(Incorrect | Algebra, Geometry, Functions)
                [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2],
                # P(Correct | Algebra, Geometry, Functions)
                [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
            ],
            evidence=['Algebra', 'Geometry', 'Functions'],
            evidence_card=[2, 2, 2],  # 2×2×2=8 комбінацій
            state_names={
                'Result': ['Incorrect', 'Correct'],
                'Algebra': ['Low', 'High'],
                'Geometry': ['Low', 'High'],
                'Functions': ['Low', 'High']
            }
        )
        
        # Додаємо CPT до моделі
        self.model.add_cpds(cpd_algebra, cpd_geometry, cpd_functions, cpd_result)
    
    def get_prior_distribution(self):
        """Отримання апріорних розподілів"""
        beliefs = {}
        for cpd in self.model.get_cpds():
            var = cpd.variable
            if var != 'Result':
                states = cpd.state_names[var]
                probs = cpd.values.flatten()
                beliefs[var] = {state: float(prob) for state, prob in zip(states, probs)}
        return beliefs
    
    def update_from_answer(self, is_correct: bool, topic: str):
        """Оновлення на основі відповіді - СПРАВДІ ПРАЦЮЄ"""
        print(f"\n{'='*60}")
        print(f"ОНОВЛЕННЯ: тема='{topic}', правильна={is_correct}")
        print(f"{'='*60}")
        
        # 1. ОНОВЛЮЄМО CPT
        self._update_skills(topic, is_correct)
        
        # 2. ПЕРЕБУДОВУЄМО МЕРЕЖУ З НОВИМИ CPT
        self._rebuild_network()
        
        # 3. ВИКОНУЄМО ЗАПИТ
        evidence = {'Result': 'Correct' if is_correct else 'Incorrect'}
        
        for var in ['Algebra', 'Geometry', 'Functions']:
            result = self.inference.query(variables=[var], evidence=evidence)
            states = result.state_names[var]
            probs = result.values.flatten()
            
            self.current_state[var] = {
                state: float(prob) for state, prob in zip(states, probs)
            }
            
            print(f"{var}: Low={self.current_state[var]['Low']:.3f}, High={self.current_state[var]['High']:.3f}")
        
        print(f"{'='*60}")
        return self.current_state
    
    def _update_skills(self, topic: str, is_correct: bool):
        """Оновлення навичок"""
        topic_to_node = {
            'algebra': 'Algebra',
            'geometry': 'Geometry',
            'functions': 'Functions'
        }
        
        target = topic_to_node.get(topic.lower(), 'Algebra')
        
        print("Оновлення CPT навичок:")
        for skill in ['Algebra', 'Geometry', 'Functions']:
            old_values = self.skill_cpds[skill].copy()
            
            # Коефіцієнт
            if skill == target:
                factor = 1.3 if is_correct else 0.7  
                new_low = max(0.05, old_values[0, 0] / factor)
                new_high = min(0.95, old_values[1, 0] * factor)
            
                # Нормалізуємо
                total = new_low + new_high
                new_low /= total
                new_high /= total  
            else:
               new_low =  old_values[0, 0] 
               new_high = old_values[1, 0]
            # Зберігаємо
            self.skill_cpds[skill] = np.array([[new_low], [new_high]])
            print(f"  {skill}: {old_values.flatten().round(3)} -> {self.skill_cpds[skill].flatten().round(3)}")
    
    def _rebuild_network(self):
        """Перебудова мережі з новими CPT"""
        # Видаляємо старі CPT
        for var in ['Algebra', 'Geometry', 'Functions', 'Result']:
            try:
                self.model.remove_cpds(var)
            except:
                pass
        
        # Додаємо нові CPT навичок
        cpd_algebra = TabularCPD(
            variable='Algebra',
            variable_card=2,
            values=self.skill_cpds['Algebra'],
            state_names={'Algebra': ['Low', 'High']}
        )
        
        cpd_geometry = TabularCPD(
            variable='Geometry',
            variable_card=2,
            values=self.skill_cpds['Geometry'],
            state_names={'Geometry': ['Low', 'High']}
        )
        
        cpd_functions = TabularCPD(
            variable='Functions',
            variable_card=2,
            values=self.skill_cpds['Functions'],
            state_names={'Functions': ['Low', 'High']}
        )
        
        # Result CPT залишається незмінною
        cpd_result = TabularCPD(
            variable='Result',
            variable_card=2,
            values=[
                [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2],
                [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
            ],
            evidence=['Algebra', 'Geometry', 'Functions'],
            evidence_card=[2, 2, 2],
            state_names={
                'Result': ['Incorrect', 'Correct'],
                'Algebra': ['Low', 'High'],
                'Geometry': ['Low', 'High'],
                'Functions': ['Low', 'High']
            }
        )
        
        self.model.add_cpds(cpd_algebra, cpd_geometry, cpd_functions, cpd_result)
        #self.inference = VariableElimination(self.model)

    
    def predict_success(self, task_topic: str) -> float:
        """Прогнозування успішності для теми"""

        if not self.current_state:
            self.current_state = self.get_prior_distribution()
        
        # Визначаємо, який вузол відповідає темі
        topic_to_node = {
            'algebra': 'Algebra',
            'geometry': 'Geometry',
            'functions': 'Functions'
        }
        
        node = topic_to_node.get(task_topic, 'Algebra')
        
        if node in self.current_state:
            # Ймовірність успіху ≈ ймовірність високого рівня
            high_prob = self.current_state[node].get('High', 0)
            return high_prob * 0.8 + (1 - high_prob) * 0.3
        else:
            return 0.5
    
    def get_weakest_topic(self) -> str:
        """Визначення найслабшої теми"""
        if not self.current_state:
            return 'algebra'
        
        topics = {
            'Algebra': self.current_state.get('Algebra', {}).get('High', 0),
            'Geometry': self.current_state.get('Geometry', {}).get('High', 0),
            'Functions': self.current_state.get('Functions', {}).get('High', 0)
        }
        
        # Знаходимо тему з найменшою ймовірністю високого рівня
        weakest = min(topics.items(), key=lambda x: x[1])
        return weakest[0].lower()
    
    def save_to_database(self, db_manager, user_id: str):
        """Збереження моделі в БД - ГАРАНТУЄ ЗБЕРЕЖЕННЯ 2D СТРУКТУРИ"""
        if self.model is None:
            print("Модель не ініціалізована")
            return
        
        print(f"\n=== ЗБЕРЕЖЕННЯ МОДЕЛІ ДЛЯ {user_id} ===")
        
        network_structure = {
            'nodes': list(self.model.nodes()),
            'edges': list(self.model.edges())
        }
        
        cpt_parameters = {}
        for cpd in self.model.get_cpds():
            # ГАРАНТУЄМО 2D СТРУКТУРУ
            values_array = cpd.values
            
            print(f"\nCPT {cpd.variable}:")
            print(f"  Початкова форма: {values_array.shape}")
            print(f"  Початкові значення:\n{values_array}")
            
            # Перетворюємо в Python list, гарантуючи 2D структуру
            if values_array.ndim == 1:
                # 1D -> 2D: [[x1], [x2], ...]
                values_list = [[float(v)] for v in values_array]
            elif values_array.ndim == 2:
                # 2D -> список списків
                values_list = values_array.tolist()
            else:
                # 3D+ -> спрощуємо до 2D
                values_list = values_array.flatten().tolist()
                # Потім робимо 2D
                values_list = [[v] for v in values_list] if values_list else [[]]
            
            print(f"  Збережена форма: список з {len(values_list)} елементів")
            print(f"  Перший елемент: {values_list[0] if values_list else 'пусто'}")
            
            # Отримуємо evidence коректно
            evidence = []
            if hasattr(cpd, 'evidence') and cpd.evidence:
                evidence = list(cpd.evidence)
            
            cpt_parameters[cpd.variable] = {
                'values': values_list,  # ГАРАНТОВАНО 2D список!
                'evidence': evidence,
                'state_names': cpd.state_names,
                'original_shape': values_array.shape  # Зберігаємо оригінальну форму
            }
        
        print(f"\nПоточний стан: {self.current_state}")
        
        # Перевіряємо, чи існує вже модель
        existing_model = db_manager.get_bayesian_model(user_id)
        
        if existing_model:
            # Оновлюємо
            db_manager.update_bayesian_model(
                user_id=user_id,
                current_state=self.current_state
            )
            print(f"✓ Модель оновлена")
        else:
            # Створюємо нову
            db_manager.create_bayesian_model(
                user_id=user_id,
                network_structure=network_structure,
                cpt_parameters=cpt_parameters,
                current_state=self.current_state
            )
            print(f"✓ Модель створена")
    
    def load_from_database(self, db_manager, user_id: str):
        """Завантаження моделі з БД"""
        print(f"\n=== ЗАВАНТАЖЕННЯ МОДЕЛІ ДЛЯ {user_id} ===")
        
        model_data = db_manager.get_bayesian_model(user_id)
        
        if not model_data:
            print("✗ Модель не знайдена")
            return False
        
        try:
            print(f"✓ Дані отримано")
            
            self.current_state = model_data.get('current_state', {})
            
            if 'network_structure' not in model_data or 'cpt_parameters' not in model_data:
                print("⚠ Немає структури мережі, будую стандартну")
                self.build_network()
                return True
            
            # Будуємо нову модель
            self.model = DiscreteBayesianNetwork()
            
            # Додаємо вузли та зв'язки
            nodes = model_data['network_structure'].get('nodes', [])
            edges = model_data['network_structure'].get('edges', [])
            self.model.add_nodes_from(nodes)
            self.model.add_edges_from(edges)
            
            print(f"✓ Створено мережу: {len(nodes)} вузлів, {len(edges)} зв'язків")
            
            # Обробляємо CPT
            cpt_parameters = model_data['cpt_parameters']
            cpds = []
            
            for var, params in cpt_parameters.items():
                print(f"\nОбробка {var}:")
                
                values_list = params.get('values', [])
                evidence = params.get('evidence', [])
                state_names = params.get('state_names', {})
                
                # ГАРАНТУЄМО 2D СТРУКТУРУ
                if evidence:
                    # CPT з еквіденсами - має бути 2D
                    print(f"  CPT з {len(evidence)} еквіденсами")
                    
                    # Перетворюємо в numpy array
                    values_array = np.array(values_list)
                    print(f"  Початкова форма: {values_array.shape}")
                    
                    # Якщо це 4D масив (2,2,2,2), перетворюємо на 2D (2,8)
                    if values_array.ndim > 2:
                        print(f"  ⚠ {values_array.ndim}D масив! Перетворюю на 2D")
                        # Перетворюємо на 2D: (2, 2×2×2) = (2, 8)
                        new_shape = (values_array.shape[0], -1)
                        values_array = values_array.reshape(new_shape)
                        print(f"  Після reshape: {values_array.shape}")
                    
                    # Тепер точно 2D масив
                    evidence_card = [len(state_names[ev]) for ev in evidence] if state_names else [2] * len(evidence)
                    
                    print(f"  Фінальна форма: {values_array.shape}")
                    print(f"  Очікувана: ({len(state_names.get(var, ['Low', 'High']))}, {np.prod(evidence_card)})")
                    
                    cpd = TabularCPD(
                        variable=var,
                        variable_card=len(state_names.get(var, ['Incorrect', 'Correct'])),
                        values=values_array,
                        evidence=evidence,
                        evidence_card=evidence_card,
                        state_names=state_names
                    )
                else:
                    # Маргінальний CPT
                    print(f"  Маргінальний CPT")
                    
                    # Перетворюємо в numpy array
                    values_array = np.array(values_list)
                    print(f"  Початкова форма: {values_array.shape}")
                    
                    # ГАРАНТУЄМО 2D форму (n, 1)
                    if values_array.ndim == 1:
                        values_array = values_array.reshape(-1, 1)
                    elif values_array.ndim > 2:
                        values_array = values_array.reshape(-1, 1)
                    
                    print(f"  Фінальна форма: {values_array.shape}")
                    
                    cpd = TabularCPD(
                        variable=var,
                        variable_card=len(state_names.get(var, ['Low', 'High'])),
                        values=values_array,
                        state_names=state_names
                    )
                
                cpds.append(cpd)
                print(f"  ✓ CPT створено")
            
            # Додаємо всі CPT
            print(f"\nДодаю {len(cpds)} CPT до моделі...")
            self.model.add_cpds(*cpds)
            
            # Перевірка моделі
            print("Перевірка моделі...")
            self.model.check_model()
            print("✓ Модель перевірено")
            
            # Ініціалізація інференсу
            self.inference = VariableElimination(self.model)
            
            # Якщо current_state порожній
            if not self.current_state:
                self.current_state = self.get_prior_distribution()
            
            print(f"\n✓ Модель успішно завантажена!")
            print(f"Поточний стан: {self.current_state}")
            
            return True
            
        except Exception as e:
            print(f"\n✗ ПОМИЛКА: {e}")
            import traceback
            traceback.print_exc()
            
            print("\n⚠ Буду стандартну мережу...")
            self.build_network()
            return False
        
