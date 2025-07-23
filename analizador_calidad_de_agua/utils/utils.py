import numpy as np

def create_multivariate_sequences(X, y=None, n_steps=1):
    sequences = []
    targets = []

    for i in range(len(X) - n_steps):
        sequences.append(X[i:i+n_steps])
        if y is not None:
            targets.append(y[i+n_steps])
    
    return (np.array(sequences), np.array(targets)) if y is not None else np.array(sequences)
