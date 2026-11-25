import os, sys
import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
from DeckBattleGym.sim.experiment import BASE

# uses the training data to make predictions 
# save a case not to train on 
HOLDOUT = ["deck06", "deck07"]  

d = np.load(os.path.join(BASE, "value_data.npz"))
X, y, decks = d["X"], d["y"], d["deck"]
test = np.isin(decks, HOLDOUT)

# small nueral network 
scaler = StandardScaler().fit(X[~test])
net = MLPRegressor(hidden_layer_sizes=(64, 64), early_stopping=True, max_iter=300, random_state=0)
net.fit(scaler.transform(X[~test]), y[~test])
pred = np.clip(net.predict(scaler.transform(X[test])), 0, 1)
mse, base = np.mean((pred - y[test]) ** 2), np.var(y[test])
print(f"held-out decks: MSE {mse:.4f} vs predict-the-mean {base:.4f}  (R^2 {1 - mse / base:.2f})")

# train again but with every combination 
scaler = StandardScaler().fit(X)
net.fit(scaler.transform(X), y)
out = {"mean": scaler.mean_, "scale": scaler.scale_, "n": len(net.coefs_)}
for i, (W, b) in enumerate(zip(net.coefs_, net.intercepts_)):
    out[f"W{i}"], out[f"b{i}"] = W, b
np.savez(os.path.join(BASE, "value_net.npz"), **out)
print("saved value_net.npz")