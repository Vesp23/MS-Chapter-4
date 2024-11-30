import simpy
import random
from collections import Counter
import matplotlib.pyplot as plt
from queue import PriorityQueue

TIME_QUANTUM = 0.136
BUFFER_SIZE = 10
NUM_REQUESTS = 110
NUM_PRIORITIES = 9

cox_params = {
    'lambda': [9, 9],
    'prob': [0.5, 0.5]
}

def cox_distribution():
    phase = random.choices(range(len(cox_params['lambda'])), weights=cox_params['prob'])[0]
    return random.expovariate(cox_params['lambda'][phase])

def request_generator(env, buffer, stats):
    for _ in range(NUM_REQUESTS):
        arrival_time = env.now
        priority = random.randint(1, NUM_PRIORITIES)
        yield env.timeout(cox_distribution())
        if buffer.qsize() < BUFFER_SIZE:
            buffer.put((priority, arrival_time))
            stats['buffer_occupancy'].append(buffer.qsize())
        else:
            stats['dropped'] += 1
            print("Заявка отброшена! Буфер заполнен.")

def processor(env, buffer, stats):
    while len(stats['processed']) < NUM_REQUESTS:
        if not buffer.empty():
            priority, arrival_time = buffer.get()
            wait_time = env.now - arrival_time
            stats['wait_times'].append(wait_time)
            yield env.timeout(TIME_QUANTUM)
            stats['processed'].append(env.now - arrival_time)
            stats['processor_busy_time'] += TIME_QUANTUM
        else:
            yield env.timeout(0.01)

def analyze_results(stats):
    print("=== Результаты ===")
    print(f"Обработанные заявки: {len(stats['processed'])}")
    print(f"Отброшенные заявки: {stats['dropped']}")
    print(f"Среднее время ожидания: {sum(stats['wait_times']) / len(stats['wait_times']):.3f} сек")
    print(f"Среднее время обслуживания: {sum(stats['processed']) / len(stats['processed']):.3f} сек")
    print(f"Суммарное время занятости процессора: {stats['processor_busy_time']:.3f} сек")
    print(f"Эффективность системы: {len(stats['processed']) / (len(stats['processed']) + stats['dropped']) * 100:.2f}%")

    buffer_count = Counter(stats['buffer_occupancy'])
    x = sorted(buffer_count.keys())
    y = [buffer_count[i] for i in x]

    plt.figure(figsize=(10, 5))
    plt.bar(x, y, color='skyblue', edgecolor='black')
    plt.xticks(range(min(x), max(x) + 1))
    plt.xlabel("Количество заявок в буфере")
    plt.ylabel("Частота")  # Убрал "(сек)"
    plt.title("Распределение занятости буфера")
    plt.show()

    plt.figure(figsize=(10, 5))
    plt.hist(stats['wait_times'], bins=20, alpha=0.5, label='Время ожидания')
    plt.hist(stats['processed'], bins=20, alpha=0.5, label='Время обслуживания')
    plt.xlabel("Время (сек)")
    plt.ylabel("Частота")
    plt.title("Распределение времен ожидания и обслуживания")
    plt.legend()
    plt.show()

def main():
    env = simpy.Environment()
    buffer = PriorityQueue()
    stats = {
        'buffer_occupancy': [],
        'dropped': 0,
        'processed': [],
        'wait_times': [],
        'processor_busy_time': 0.0
    }
    env.process(request_generator(env, buffer, stats))
    env.process(processor(env, buffer, stats))
    env.run(until=10)
    analyze_results(stats)

if __name__ == "__main__":
    main()
