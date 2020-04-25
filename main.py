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

    def roulette_wheel_selection(self):
        sum = 0
        parents = []
        for i in range(self.pop_size):
            sum += self.chromosomes[i].cost

        while len(parents) < 2:
            sum_temp = 0
            pick = random.uniform(0, sum)
            for i in range(self.pop_size):
                sum_temp += self.chromosomes[i].cost
                if sum_temp > pick:
                    if not i in parents:
                        parents.append(self.chromosomes[i])
                    break
        return parents
                



class Chromosome:
    def __init__(self, employers, days):
        # create 2D array
        self.employers = employers
        self.days = days
        self.grid = [[0 for x in range(days)] for y in range(employers)] 
        self.max_shifts = 3
        self.hard_constraint = [[10, 10, 5, 5, 5, 5, 5], [10, 10, 10, 5, 10, 5, 5], [5, 5, 5, 5, 5, 5, 5]]

        # declare duration of hours for each shift
        self.shift_hours = {1 : 8, 2 : 8, 3 : 10}

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

    def check_hard_constraint(self):
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
                    return False
                day_of_week = 0 if day_of_week >= 6 else day_of_week + 1

    def check_soft_constraints(self):
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
                if not (temp_consecutive_night_shifts == consecutive_night_shifts and self.grid[i][j+consecutive_night_shifts] == 0 and self.grid[i][j+consecutive_night_shifts+1] == 0):
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
                if not (temp_consecutive_days == consecutive_days and self.grid[i][j+temp_consecutive_days] == 0 and self.grid[i][j+temp_consecutive_days+1] == 0):
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
        return total_cost
            
# main
pop = Population(1)
valid_monochromes = []

for i in range(len(pop.chromosomes)):
    pop.chromosomes[i].print()
    print(str(pop.chromosomes[i].check_soft_constraints()))
    if pop.chromosomes[i].check_hard_constraint() == True:
        valid_monochromes.append(pop.chromosomes[i])
       # print("Chromosome " + str(i) + " meets hard constraint: " + str(pop.chromosomes[i].check_hard_constraint()))

for i in pop.roulette_wheel_selection():
    i.print()
    print(str(i.cost))
