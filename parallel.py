import multiprocessing
from simulation import RunEpidemic

def async_RunEpidemic(q, *args):
    results = RunEpidemic(*args)
    q.put(results[:-1])

def run_async(num_runs, *args):

    # Make the queue and the parameters
    q = multiprocessing.Manager().Queue()

    # Run all of the simulations
    multiprocessing.freeze_support()
    with multiprocessing.Pool() as pool:
        pool.starmap(async_RunEpidemic, ((q, *args) for _ in range(num_runs)))

    # Grab and return all the loggers
    outputs = []
    while not q.empty():
        outputs.append(q.get())
    
    return outputs

if __name__ == "__main__":
    print(run_async(8, 10000, 20, 100))