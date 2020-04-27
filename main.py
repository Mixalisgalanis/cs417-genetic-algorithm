import random


class Population:
    """ This class represents our chromosome population. It is described
    by a list of generations. Each value of this list contains another 
    list of the chromosomes of a particular generation."""

    def __init__(self, pop_size, crossover_method = 0, mutation_method = 0, min_gen_improvement = 0, verbose = False):
        """This is the constructor of the Population class. The first pop_size
        chromosomes are created instantly and represent the first generation.
        For each 2 parents a new child is created in a subsequent generation."""

        # instance variables
        self.pop_size = pop_size
        self.generations = []

        # generate initial population (generation 0)
        current_gen = 0
        temp_chromosomes = []
        for i in range(pop_size):
            # stats of WHPP problem
            employers = 30
            days = 14

            # store chromosome
            c = Chromosome(i, current_gen, employers, days, mutation_method, verbose = verbose)
            temp_chromosomes.append(c)

        # insert generated chromosomes into first generations
        self.generations.append(temp_chromosomes)
        
        # generate subsequent generations. creates as many childs as 
        # possible (whenever there are at least 2 parents in a previous generation).
        if self.pop_size <= 1: return
        while True:
            i = 0
            # create as many childs in this generation as possible
            for i in range(len(self.generations[current_gen]) // 2):
                temp_parents = self.roulette_wheel_selection(current_gen)
                c = Chromosome(self.pop_size, current_gen + 1, temp_parents[0].employers, temp_parents[0].days, mutation_method, crossover_params = (crossover_method, temp_parents[0], temp_parents[1]), verbose = verbose)
                if len(self.generations) >= current_gen + 2:
                    self.generations[current_gen + 1].append(c)
                else:
                    self.generations.append([c])
                self.pop_size += 1
            # calculate generation cost improvement over the previous one
            if min_gen_improvement > 0:
                avg_gen_improvement = 0
                for i in range(len(self.generations[current_gen]) // 2):
                    avg_gen_improvement += self.generations[current_gen][i].improvement_over_parent
                avg_gen_improvement /= len(self.generations[current_gen])
                print("GENERATION " + str(current_gen) + ": "+ str(avg_gen_improvement) + " improvement over previous gen.")
                if avg_gen_improvement < min_gen_improvement:
                    break
            if len(self.generations[current_gen + 1]) == 1:
                break
            # proceed to next generation
            current_gen += 1
        
        print("\n=============SUMMARY=============")
        for i in range(current_gen + 2):
            print("Generation " + str(i) + "  [" + str(len(self.generations[i])) + "]\t -> lowest: " + str(min([c.cost for c in self.generations[i]])) + ", average: " + str(round(sum([c.cost for c in self.generations[i]])/len(self.generations[i]) , 2))  + ", highest: " + str(max([c.cost for c in self.generations[i]])))

    def roulette_wheel_selection(self, generation):
        """This function picks two parents from a pool of chromosomes in a particular
        generation. Both of the parents have to be different chromosomes. The roulette
        method takes into account the cost (penalty of soft constraints) of each chromosome
        into account. Lower costs mean a higher change of that chromosome to be picked as 
        a parent."""
        sum_initial = 0
        parents = []
        gen_costs = []
        gen_costs_2 = []
        # calculate sum
        for i in range(len(self.generations[generation])):
            gen_costs.append(1 / self.generations[generation][i].cost)
            sum_initial += 1 / self.generations[generation][i].cost

        # calculate min
        min_cost = min(gen_costs)
        FACTOR = 1.02

        for i in range(len(gen_costs)):
            gen_costs_2.append(gen_costs[i] - (min_cost / FACTOR))
        sum_costs = sum(gen_costs_2)
        
        avg = sum_initial / len(self.generations[generation])

        while len(parents) < 2:
            sum_temp = 0
            pick = random.uniform(0, sum_costs)
            for i in range(len(gen_costs_2)):
                sum_temp +=  gen_costs_2[i]
                if sum_temp > pick:
                    if not self.generations[generation][i] in parents:
                        parents.append(self.generations[generation][i])
                    break
        
        #for i in parents:
        #    print("picked parent " + str(i.id) + " with a cost of: " + str(1/i.cost) + ", generation average: " + str(avg))
        return parents
    
class Chromosome:

    def __init__(self, id, generation, employers, days, mutation_method, crossover_params = None, verbose = False):
        self.id = id                    # used for identification
        self.generation = generation    # used for identification
        
        self.feasible = True            # used for evaluation of hard constraints
        self.cost = 0                   # used for evaluation of soft constraints

        self.employers = employers      # chromosome stats
        self.days = days                # chromosome stats
        self.grid = [[0 for x in range(days)] for y in range(employers)]

        self.hard_constraint = [[10, 10, 5, 5, 5, 5, 5], [10, 10, 10, 5, 10, 5, 5], [5, 5, 5, 5, 5, 5, 5]]

        # declare duration of hours for each shift
        self.max_shifts = 3
        self.shift_hours = {1 : 8, 2 : 8, 3 : 10}

        self.improvement_over_parent = 100 # used for termination condition
        
        # crossover_params : (parentA, parentB, [index1, index2, ... indexN])
        if crossover_params is None: # Does not perform crossover between parents (first gen only)
            self.generateGrid()
            self.check_hard_constraint()   
            self.check_soft_constraints()

        else: # child is created by parents
            self.crossover(crossover_params)
            self.mutate(mutation_method)
            self.check_hard_constraint()   
            self.check_soft_constraints()

            avg_parents_cost = (crossover_params[1].cost + crossover_params[2].cost) / 2
            self.improvement_over_parent = (avg_parents_cost - self.cost) / avg_parents_cost
        
        if verbose: self.describe()
        #if verbose: self.print()

    def generateGrid(self):
        day_of_week = 0
        for i in range(self.days):
            sum_shifts = 0
            # filling shifts_remaining from hard constraints
            shifts_remaining = {}
            for j in range(len(self.hard_constraint)):
                shifts_remaining[j+1] = self.hard_constraint[j][day_of_week]
                sum_shifts += self.hard_constraint[j][day_of_week]

            # generating random shifts for employers
            for j in range(self.employers):
                picked = False
                while picked == False:
                    #pick = random.randint(0, self.max_shifts)
                    pick = 0 if random.randint(0,1) == 0 else random.randint(1, self.max_shifts) # needed for diversity (0.5 chance to pick 0)
                    for h in range(len(self.hard_constraint)):
                        if pick == h + 1 and shifts_remaining[h+1] > 0:
                            self.grid[j][i] = pick
                            shifts_remaining[h+1] -= 1
                            sum_shifts -= 1
                            picked = True
                    if pick == 0 and self.employers - j > sum_shifts:
                        self.grid[j][i] = pick
                        picked = True
            day_of_week = 0 if day_of_week >= 6 else day_of_week + 1

    def generateGridUpdated(self):
        # attempt 2 (trying out more diversity)
        day_of_week = 0
        for j in range(self.days):
            # filling shifts_remaining from hard constraints
            shifts = {}
            sum_shifts = 0
            for s in range(len(self.hard_constraint)):
                shifts[s+1] = self.hard_constraint[s][day_of_week]
                sum_shifts += self.hard_constraint[s][day_of_week]

            # generating indexes in which our different shift types are going to be inserted
            indexes = {}
            for key in shifts:
                added = 0
                while added < shifts[key]:
                    rand_index = random.randint(0, self.employers - 1)
                    if not rand_index in indexes.keys():
                        indexes[rand_index] = key
                        added += 1

            for i in range(self.employers):
                self.grid[i][j] = indexes[i] if i in indexes.keys() else 0

            day_of_week = 0 if day_of_week >= 6 else day_of_week + 1

    def crossover(self, crossover_params):
        indexes = []
        parentA = crossover_params[1]
        parentB = crossover_params[2]

        # select crossover method
        if crossover_params[0] == 0: # method 0 (off)
            self.grid = parentA.grid if random.randint(0,1) == 1 else parentB.grid
            return
        elif crossover_params[0] == 1: # method 1 (simple method)
            pick = random.randint(1,parentA.days - 1)
            indexes.append(pick)
        elif crossover_params[0] == 2: # method 2 (random crossover points method)
            for i in range(parentA.days):
                if random.randint(0, 3) == 0: # 25% chance to store this index
                    indexes.append(i)
        
        # begin crossover procedure
        activeParent = parentA if random.randint(0,1) == 0 else parentB
        for j in range(self.days):
            if j in indexes: # if crossover index is found, then toggle active parent
                activeParent = parentA if activeParent.cost == parentB.cost else parentB
            for i in range(self.employers):
                self.grid[i][j] = activeParent.grid[i][j]

    def mutate(self, mode):
        if mode == 0:
            return
        elif mode == 1:# method 1, random vertical swaps
            for j in range(self.days):
                swaps = random.randint(0, self.employers // 15)
                for i in range(swaps):
                    swap_index_1 = random.randint(0, self.employers - 1)
                    swap_index_2 = random.randint(0, self.employers - 1)
                    temp_shift = self.grid[swap_index_1][j]
                    self.grid[swap_index_1][j] = self.grid[swap_index_2][j]
                    self.grid[swap_index_2][j] = temp_shift
        elif mode == 2: # method 2, inversion of order of shifts in a day
            for j in range(self.days):
                shifts = [row[j] for row in self.grid]
                shifts.reverse()
                for i in range(len(shifts)):
                    self.grid[i][j] = shifts[i]

    def check_hard_constraint(self):
        self.feasible = True
        day_of_week = 0 # used for repeating weeks
        for j in range(self.days):
            # create dict to store shift day_of_week
            self.employers_per_shift = {}

            # initialize 
            for i in range(self.max_shifts + 1):
                self.employers_per_shift[i] = 0

            # store shift day_of_week in dict
            for i in range(self.employers):
                self.employers_per_shift[self.grid[i][j]] += 1
            
            # check if chromosome meets hard constraint
            for m in range(len(self.hard_constraint)):
                if self.hard_constraint[m][day_of_week] != self.employers_per_shift[m + 1]:
                    #print("shift:", m, "day:",j,"official:", self.hard_constraint[m][day_of_week],"real:", self.employers_per_shift[m + 1])
                    self.feasible = False
            day_of_week = 0 if day_of_week >= 6 else day_of_week + 1

    def check_soft_constraints(self):
        costs = []

        # 1. max 70 hours of work (cost = 1000)
        max_work_hours = 70
        cost = 1000
        total_cost = 0
        for i in range(len(self.grid)):
            sum_work_hours = 0
            for j in range(len(self.grid[0])):
                if self.grid[i][j] != 0:
                    sum_work_hours += self.shift_hours[self.grid[i][j]]
            if sum_work_hours > max_work_hours:
                total_cost += cost
        
        # 2. max 7 consecutive days of work (cost = 1000)
        consecutive_days = 7
        cost = 1000
        for i in range(self.employers):
            count = 0
            for j in range(self.days):
                if count > consecutive_days:
                    total_cost += cost
                    count = 0
                else:
                    count = count + 1 if self.grid[i][j] != 0 else 0

        # 3. max 4 consecutive night shifts (cost = 1000)
        consecutive_night_shifts = 4
        cost = 1000
        for i in range(self.employers):
            count = 0
            for j in range(self.days):
                if count > consecutive_night_shifts:
                    total_cost += cost
                    count = 0
                else:
                    count = count + 1 if self.grid[i][j] == 3 else 0

        # 4. avoid night shift of a day with a morning shift of the next day (cost = 1000)
        avoid_shift = (3, 1)
        cost = 1000
        for i in range(self.employers):
            for j in range(self.days - 1):
                if self.grid[i][j] == avoid_shift[0] and self.grid[i][j+1] == avoid_shift[1]:
                    total_cost += cost

        # 5. avoid afteroon shift of a day with a morning shift of the next day (cost = 800)
        avoid_shift = (2, 1)
        cost = 800
        for i in range(self.employers):
            for j in range(self.days - 1):
                if self.grid[i][j] == avoid_shift[0] and self.grid[i][j+1] == avoid_shift[1]:
                    total_cost += cost

        # 6. avoid night shift of a day with an afteroon shift of the next day (cost = 800)
        avoid_shift = (3, 2)
        cost = 800
        for i in range(self.employers):
            for j in range(self.days - 1):
                if self.grid[i][j] == avoid_shift[0] and self.grid[i][j+1] == avoid_shift[1]:
                    total_cost += cost
        
        # 7. at least 2 days off after 4 consecutive days of night shifts (cost = 100)
        consecutive_night_shifts = 4
        days_off = 2
        cost = 100
        for i in range(self.employers):
            for j in range(self.days - (consecutive_night_shifts + days_off - 1)):
                temp_consecutive_night_shifts = 0
                for k in range(consecutive_night_shifts):
                    if self.grid[i][j+k] == 3:
                        temp_consecutive_night_shifts += 1
                if (temp_consecutive_night_shifts == consecutive_night_shifts and (self.grid[i][j+consecutive_night_shifts] != 0 or self.grid[i][j+consecutive_night_shifts+1] != 0)):
                    total_cost += cost

        # 8. at least 2 days off after 7 days of work (cost = 100)
        consecutive_days = 7
        days_off = 2
        cost = 100
        for i in range(self.employers):
            for j in range(self.days - (consecutive_days + days_off - 1)):
                temp_consecutive_days = 0
                for k in range(consecutive_days):
                    if self.grid[i][j+k] != 0:
                        temp_consecutive_days += 1
                if temp_consecutive_days == consecutive_days and (self.grid[i][j+temp_consecutive_days] != 0 or self.grid[i][j+temp_consecutive_days+1] != 0):
                    total_cost += cost

        # 9. avoid day off - work - day off (cost = 1)
        cost = 1
        for i in range(self.employers):
            check = 0
            for j in range(self.days):
                if check == 0:
                    if self.grid[i][j] != 0:
                        check = 1
                elif check == 1:
                    if self.grid[i][j] == 0:
                        check = 2
                    else:
                        check = 0
                else:
                    if self.grid[i][j] != 0:
                        total_cost += cost
                    check = 0

        # 10. avoid work - day off - work (cost = 1)
        cost = 1
        for i in range(self.employers):
            check = 0
            for j in range(self.days):
                if check == 0:
                    if self.grid[i][j] == 0:
                        check = 1
                elif check == 1:
                    if self.grid[i][j] != 0:
                        check = 2
                    else:
                        check = 0
                else:
                    if self.grid[i][j] == 0:
                        total_cost += cost
                    check = 0

        # 11. max 1 weekend of work (cost = 1)
        max_work_weekends = 1
        cost = 1
        for i in range(self.employers):
            day_of_week = 0
            weekends_worked = 0
            saturday_worked = False
            sunday_worked = False
            for j in range(self.days):
                if day_of_week == 5 and self.grid[i][j] != 0:
                    saturday_worked = True
                if day_of_week == 6 and self.grid[i][j] != 0:
                    sunday_worked = True
                if saturday_worked and sunday_worked:
                    weekends_worked += 1
                    if weekends_worked > 1:
                        total_cost += cost
                if day_of_week >= 6:
                    day_of_week = 0
                    saturday_worked = False
                    sunday_worked = False
                else:
                    day_of_week += 1

        self.cost = total_cost
      
    def print(self):
        for i in range(self.employers):
            for j in range(self.days):
                print(self.grid[i][j], end = "   ")
            print()

    def describe(self):
        print("Chromosome " + str(self.id) + "[" + str(self.generation) + "], feasible: " + str(self.feasible) + ", penalty cost: " + str(self.cost) + ((", improvement: " + str(round(self.improvement_over_parent, 3)) + "%") if self.generation > 0 else ""))

# MAIN
max_number_of_generations = 8   # max generations (term_cond_1)
min_gen_improvement = 0         # minimum gen-over-gen improvement to keep going (term_cond_2)
pop = Population(2 ** (max_number_of_generations - 1), crossover_method = 2, mutation_method = 2, min_gen_improvement = min_gen_improvement, verbose = True)