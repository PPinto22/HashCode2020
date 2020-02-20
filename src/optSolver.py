
from BaseSolver import BaseSolver
from scipy import optimize 

    def eval(self,sol):
        # TODO: write evaluation function -> assess score
        #sol is the solution to be assessed
        pass
    
    def boundaries(lower,upper): #returns de boundaries with the format expected by scipy
        return list(zip(lower,upper))
    
     def opt(self,sol,bounds):
        # TODO: optimize initial solution with metaheuristics
        #print(optimize.dual_annealing(eval,bounds))
        #print(optimize.differential_evolution(eval,bounds,maxiter = 2,workers=4))
        pass