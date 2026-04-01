import numpy as np
import random
from database import get_beban_mengajar, get_mapel_guru_mapping, get_special_ids, save_best_chromosome
from population import generate_population, WAKTU_IDS, HARI_IDS
from fitness import calculate_fitness

def selection(population, fitness_scores):
    # Tournament Selection
    selected = []
    pop_size = len(population)
    for _ in range(pop_size):
        i, j = random.sample(range(pop_size), 2)
        if fitness_scores[i] > fitness_scores[j]:
            selected.append(population[i].copy())
        else:
            selected.append(population[j].copy())
    return selected

def crossover(parent1, parent2, crossover_rate=0.8):
    if random.random() < crossover_rate:
        # One-point crossover on genes
        point = random.randint(1, len(parent1) - 1)
        child1 = np.vstack((parent1[:point], parent2[point:]))
        child2 = np.vstack((parent2[:point], parent1[point:]))
        return child1, child2
    return parent1.copy(), parent2.copy()

def mutate(chromosome, mutation_rate=0.05):
    # Randomly change waktu and hari
    mask = np.random.rand(len(chromosome)) < mutation_rate
    if np.any(mask):
        # We should NOT mutate fixed mapels (Upacara, Bersih, Istirahat)
        # to preserve their fixed slots and avoid high penalties.
        fixed_mapels_mask = np.isin(chromosome[:, 0], [1, 2, 3])
        # Only mutate genes that are NOT special mapels
        actual_mutation_mask = mask & ~fixed_mapels_mask
        
        if np.any(actual_mutation_mask):
            num_to_mutate = np.sum(actual_mutation_mask)
            
            # Simple strategy: keep trying until we get non-fixed slots for these regular subjects
            new_waktu = np.random.choice(WAKTU_IDS, size=num_to_mutate)
            new_hari = np.random.choice(HARI_IDS, size=num_to_mutate)
            
            # Vectorized check for fixed slots
            is_fixed = (
                ((new_hari == 1) & (new_waktu == 1)) |
                ((new_hari == 4) & (new_waktu == 1)) |
                (new_waktu == 5) |
                (new_waktu == 8)
            )
            
            # For those that hit a fixed slot, re-roll to a safe slot
            if np.any(is_fixed):
                safe_slots = [2, 3, 4, 6, 7, 9, 10, 11]
                new_waktu[is_fixed] = np.random.choice(safe_slots, size=np.sum(is_fixed))
            
            chromosome[actual_mutation_mask, 3] = new_waktu
            chromosome[actual_mutation_mask, 4] = new_hari
    return chromosome

def run_ga(pop_size=100, generations=1000):
    special_ids = get_special_ids()
    population = generate_population(pop_size)
    
    best_overall_chromosome = None
    best_overall_fitness = -1.0
    
    for gen in range(generations):
        fitness_scores = np.array([calculate_fitness(c, special_ids) for c in population])
        
        best_idx = np.argmax(fitness_scores)
        best_fitness = fitness_scores[best_idx]
        
        if best_fitness > best_overall_fitness:
            best_overall_fitness = best_fitness
            best_overall_chromosome = population[best_idx].copy()

        if gen % 10 == 0:
            print(f"Generation {gen}: Best Fitness = {best_fitness}")
            
        if best_fitness == 1.0:
            print(f"Solution found at generation {gen}!")
            break
            
        # Elitism
        new_population = [population[best_idx].copy()]
        
        # Selection
        selected = selection(population, fitness_scores)
        
        # Crossover & Mutation
        for i in range(0, pop_size - 1, 2):
            p1, p2 = selected[i], selected[i+1]
            c1, c2 = crossover(p1, p2)
            new_population.append(mutate(c1))
            if len(new_population) < pop_size:
                new_population.append(mutate(c2))
                
        population = new_population
        
    # Save the best chromosome found across all generations
    save_best_chromosome(best_overall_chromosome, best_overall_fitness, generations)
    
    return best_overall_chromosome, best_overall_fitness

if __name__ == "__main__":
    best_schedule, score = run_ga(pop_size=100, generations=1000)
    print(f"Final Best Fitness: {score}")
