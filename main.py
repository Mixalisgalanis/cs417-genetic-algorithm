import random
import matplotlib.pyplot as plt

class Population:
    """This class represents our chromosome population. It is described
    by a list of generations. Each value of this list contains another 
    list of the chromosomes of a particular generation."""

    def __init__(self, pop_size, crossover_params, mutation_params, min_gen_improvement, verbose = False):
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
            c = Chromosome(i, current_gen, employers, days, verbose = verbose)
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
                c = Chromosome(self.pop_size, current_gen + 1, temp_parents[0].employers, temp_parents[0].days, mutation_params = mutation_params, crossover_params = (crossover_params[0], crossover_params[1], temp_parents[0], temp_parents[1]), verbose = verbose)
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
        
        # outputting results in console & in form of a graph.
        print("\n=============SUMMARY=============")
        lowest = []; average = []; highest = []
        generation_axis = []
        for i in range(current_gen + 2):
            generation_axis.append(i)
            lowest.append(min([c.cost for c in self.generations[i]]))
            average.append(round(sum([c.cost for c in self.generations[i]])/len(self.generations[i])))
            highest.append(max([c.cost for c in self.generations[i]]))
            print("Generation " + str(i) + "  [" + str(len(self.generations[i])) + "]\t -> lowest: " + str(lowest[i]) + ", average: " + str(average[i])  + ", highest: " + str(highest[i]))
        plt.plot(generation_axis, lowest, 'o-b'); plt.plot(generation_axis, average, 'o-g'); plt.plot(generation_axis, highest, 'o-r')
        plt.legend(['lowest', 'average', 'highest'])
        plt.show()

    def roulette_wheel_selection(self, generation): # selection method
        """This function picks two parents from a pool of chromosomes in a particular
        generation. Both of the parents have to be different chromosomes. The roulette
        method takes into account the cost (penalty of soft constraints) of each chromosome
        into account. Lower costs mean a higher change of that chromosome to be picked as 
        a parent."""
        
        # extract costs of a particular generation
        gen_costs = []
        for i in range(len(self.generations[generation])):
            gen_costs.append(1 / self.generations[generation][i].cost)

        # subtract each chromosome's cost by the minimum cost of this generation. 
        # This increases the contrast between "good" and "bad" parents.
        min_cost = min(gen_costs)
        FACTOR = 1.02
        gen_costs_2 = []
        for i in range(len(gen_costs)):
            gen_costs_2.append(gen_costs[i] - (min_cost / FACTOR))
        sum_costs = sum(gen_costs_2)

        # pick two unique parents
        parents = []
        while len(parents) < 2:
            sum_temp = 0
            pick = random.uniform(0, sum_costs)
            for i in range(len(gen_costs_2)):
                sum_temp +=  gen_costs_2[i]
                if sum_temp > pick:
                    if not self.generations[generation][i] in parents:
                        parents.append(self.generations[generation][i])
                    break
        return parents
    
class Chromosome:
    """This class represents each chromosome, containing, identification 
    information, cost information and grid stats. The timeplan is represented
    as a 2D grid with employers serving as rows and days as columns. The cell
    value describes the type of shift assigned to an employer a particular day."""

    def __init__(self, id, generation, employers, days, mutation_params = None, crossover_params = None, verbose = False):
        """This is the constructor of the Chromosome class. All the basic variables are 
        initialized here. In the first generation, a chromosome does not come from any 
        parents. Thus its grid is generated randomly according to the hard constraints. 
        In subsequent genertaions, crossover_params are passed containing information 
        about its parents and the mutation method used."""

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
            self.generateGridAlternative()
            self.check_hard_constraint()   
            self.check_soft_constraints()

        else: # child is created by parents (subsequent gens)
            self.crossover(crossover_params)
            self.mutate(mutation_params)
            self.check_hard_constraint()   
            self.check_soft_constraints()

            avg_parents_cost = (crossover_params[2].cost + crossover_params[3].cost) / 2
            self.improvement_over_parent = (avg_parents_cost - self.cost) / avg_parents_cost
        
        if verbose: self.describe()
        #if verbose: self.print()

    def generateGrid(self):
        """This function generates a shift timeplan for the employers. It is used 
        only by the chromosomes of the first generation. In this method, we iterate
        through the initialized grid and we pick random shifts according to the hard 
        constrains of WHPP. The feasibility of the grid is guaranteed 100%."""

        day_of_week = 0
        for i in range(self.days):
            # extracting information from the hard constraints 
            sum_shifts = 0
            shifts_remaining = {}
            for j in range(len(self.hard_constraint)):
                shifts_remaining[j+1] = self.hard_constraint[j][day_of_week]
                sum_shifts += self.hard_constraint[j][day_of_week]

            # generating random shifts for employers
            for j in range(self.employers):
                picked = False
                while picked == False:
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
            
            # compatible for repeating weeks
            day_of_week = 0 if day_of_week >= 6 else day_of_week + 1

    def generateGridAlternative(self):
        """This is an alternative function of generateGrid(). It generates a shift 
        timeplan for the employers and it is used only by the chromosomes of the 
        first generation. In this method, each shift type is randomly assigned on
        the indexes (employers) according to the hard constrains of WHPP. The 
        feasibility of the grid is also guaranteed 100%."""

        day_of_week = 0
        for j in range(self.days):
            # extracting information from the hard constraints 
            shifts = {}
            sum_shifts = 0
            for s in range(len(self.hard_constraint)):
                shifts[s+1] = self.hard_constraint[s][day_of_week]
                sum_shifts += self.hard_constraint[s][day_of_week]

            # generating randomly indexes in which our different shift types are going to be assigned
            indexes = {}
            for key in shifts:
                added = 0
                while added < shifts[key]:
                    rand_index = random.randint(0, self.employers - 1)
                    if not rand_index in indexes.keys():
                        indexes[rand_index] = key
                        added += 1
            
            # applying the assignments and fill the empty cells with zeros.
            for i in range(self.employers):
                self.grid[i][j] = indexes[i] if i in indexes.keys() else 0

            # compatible for repeating weeks
            day_of_week = 0 if day_of_week >= 6 else day_of_week + 1

    def crossover(self, crossover_params):
        """This functions applies crossover to a new child chromosome coming from
        two parents. Both of the methods present below involve copying information
        vertically by switching the active parent depending on the indexes generated. 
        Crossover can only be applied vertically in order to maintain the feasibility.
        The first method is a simpler case of the second (max one crossover point)."""

        indexes = []
        propability = crossover_params[0]
        first_method = crossover_params[1]
        parentA = crossover_params[2]
        parentB = crossover_params[3]

        # propability
        if random.uniform(0, 1) < propability:
            if first_method: # method 1 (simpler - max one toggle index)
                pick = random.randint(1,parentA.days - 1)
                indexes.append(pick)
            else: # method 2 (complex - multiple random crossover points)
                for i in range(parentA.days):
                    if random.randint(0, 3) == 0: # 25% chance to store this index
                        indexes.append(i)
            
            # begin crossover procedure
            activeParent = parentA if random.randint(0,1) == 0 else parentB
            for j in range(self.days):
                if j in indexes: # if a crossover index is found, then switch active parent
                    activeParent = parentA if activeParent.cost == parentB.cost else parentB
                for i in range(self.employers):
                    self.grid[i][j] = activeParent.grid[i][j]
        else:
            self.grid = parentA.grid if random.randint(0,1) == 1 else parentB.grid

    def mutate(self, mutation_params):
        """This function applies mutation to a new child chromosome coming from
        two parents. Both of the methods present below involve making a few changes
        after a crossover is applied. Mutation changes can only be done vertically 
        in order to maintain feasibility. The first method applies a random number
        of shifts swaps between employers. The second method applies a complete 
        inversion of a particular column of the grid"""

        propability = mutation_params[0]
        first_method = mutation_params[1]

        if random.uniform(0, 1) < propability:
            if first_method == 1:# method 1, random vertical swaps
                for j in range(self.days):
                    swaps = random.randint(0, self.employers // 15)
                    for i in range(swaps):
                        swap_index_1 = random.randint(0, self.employers - 1)
                        swap_index_2 = random.randint(0, self.employers - 1)
                        temp_shift = self.grid[swap_index_1][j]
                        self.grid[swap_index_1][j] = self.grid[swap_index_2][j]
                        self.grid[swap_index_2][j] = temp_shift
            else: # method 2, inversion of order of shifts in a day
                for j in range(self.days):
                    if random.randit(0, 4): # around 20% chance
                        shifts = [row[j] for row in self.grid]
                        shifts.reverse()
                        for i in range(len(shifts)):
                            self.grid[i][j] = shifts[i]

    def check_hard_constraint(self):
        """This function checks the generated grid's feasibility. The result is
        stored in a boolean feasible variable."""

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
                    self.feasible = False
            day_of_week = 0 if day_of_week >= 6 else day_of_week + 1

    def check_soft_constraints(self):
        """This functions evaluates the soft constrains of the WHPP. This consists
        of eleven (11) individual tests associated with a penalty cost. The sum of
        these consts are stored in a cost variable representing the total penalty
        cost of a chromosome. The checks are done separatedly so new ones can be
        easily inserted as needed."""

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
        """This function performs an output of a chromosome's grid. It's 
        used mainly as a diagnostic tool."""
        for i in range(self.employers):
            for j in range(self.days):
                print(self.grid[i][j], end = "   ")
            print()

    def describe(self):
        """This function outputs the most important information about 
        each chromosome in one line. It can be enabled/disabled from 
        the verbose arguement."""
        print("Chromosome " + str(self.id) + "[" + str(self.generation) + "], feasible: " + str(self.feasible) + ", penalty cost: " + str(self.cost) + ((", improvement: " + str(round(self.improvement_over_parent, 3)) + "%") if self.generation > 0 else ""))

# ========================= MAIN =========================
# setting up variables (editable) ------------------------
max_gens = 8            # max generations (term_cond_1)
min_improvement = 0     # enforce minimum gen-over-gen percentage (term_cond_2)

p_cross = 0.8                   # propability of applying crossover (recommended > 0.5)
cross_method_1_selected = True  # switch between two crossover methods

p_mut = 0.5                     # propability of applying mutation (recommended > 0.3)
mut_method_1_selected = True    # switch between two mutation methods

# beginning procedure (do not edit) ----------------------
pop = Population(2 ** (max_gens - 1), crossover_params = (p_cross , cross_method_1_selected), mutation_params = (p_mut, mut_method_1_selected), min_gen_improvement = min_improvement, verbose = False)