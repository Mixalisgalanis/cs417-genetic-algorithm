import random

class Population:
    # constructor
    def __init__(self, pop_size):
        self.pop_size = pop_size
        self.chromosomes = []
        for i in range(pop_size):
            employers = 30
            days = 14
            self.chromosomes.append(Chromosome(employers, days))

class Chromosome:
    max_shifts = 3

    def __init__(self, employers, days):
        # create 2D array
        self.employers = employers
        self.days = days
        self.grid = [[0 for x in range(days)] for y in range(employers)] 

        # fill up array with shifts
        for i in range(employers):
            for j in range(days):
                self.grid[i][j] = random.randint(0, self.max_shifts)

    def print(self):
        print("\nChromosome with " + str(self.employers) + " employers and " + str(self.days) + " days.")
        for i in range(self.employers):
            for j in range(self.days):
                print(self.grid[i][j], end = "   ")
            print()

# main
pop = Population(4)

for i in pop.chromosomes:
    i.print()