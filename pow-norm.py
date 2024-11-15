import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import halfnorm
import sys

def find_inversions(A, B):
    inversions = []

    for i in range(len(A) - 1):
        # Check if A[i] > B[i] and A[i+1] <= B[i+1]
        if A[i] > B[i] and A[i+1] <= B[i+1]:
            inversions.append(i)
        # Check the opposite inversion: A[i] < B[i] and A[i+1] >= B[i+1]
        elif A[i] < B[i] and A[i+1] >= B[i+1]:
            inversions.append(i)

    return inversions

'''
# Example usage:
A = np.array([5, 4, 3, 2, 6, 7])
B = np.array([1, 2, 3, 4, 5, 8])
inversions = find_inversions(A, B)
print("Inversion indices:", inversions)
'''

# Set parameters
num_samples = 100000
#alpha = 3.0  # Power-law exponent (typically > 1)
# get alpha from the command line
if len(sys.argv)<2:
    print("usage: pow-norm.py <alpha>")
    exit()
else:
    alpha = float(sys.argv[1])
min_value = 0.001  # Lower bound for the power-law distribution

# Generate samples from the half-normal distribution
half_normal_samples = halfnorm.rvs(size=num_samples)

# Generate samples from the decreasing power-law distribution using the inverse transform
u = np.random.uniform(size=num_samples)
power_law_samples = min_value * (u ** (-1 / (alpha - 1)))

# Calculate mean and variance for both distributions
half_normal_mean = np.mean(half_normal_samples)
half_normal_variance = np.var(half_normal_samples)
half_normal_std = np.std(half_normal_samples)

power_law_mean = np.mean(power_law_samples)
power_law_variance = np.var(power_law_samples)
power_law_std = np.std(power_law_samples)

# Scale and shift the half-normal samples to match the power-law distribution
scaling_factor = np.sqrt(power_law_variance / half_normal_variance)
half_normal_samples_scaled = half_normal_samples * scaling_factor

# Shift half-normal samples to match the mean of the power-law distribution
mean_shift = power_law_mean - np.mean(half_normal_samples_scaled)
half_normal_samples_scaled_shifted = half_normal_samples_scaled + mean_shift

# Define linear bins based on the combined range of both distributions
all_samples = np.concatenate((power_law_samples, half_normal_samples_scaled_shifted))
num_bins = 300
bins = np.linspace(np.min(all_samples), np.max(all_samples), num_bins)

# Compute histogram densities (in linear scale) for both distributions
power_law_hist, bin_edges = np.histogram(power_law_samples, bins=bins, density=True)
half_normal_hist, _ = np.histogram(half_normal_samples_scaled_shifted, bins=bins, density=True)

# Define bin centers for plotting
bin_centers = 0.5 * (bin_edges[1:] + bin_edges[:-1])

# find inversions
inv_idx = find_inversions(power_law_hist, half_normal_hist)
print("Inversion indices:", inv_idx)

# Plot the histograms in log-log scale
plt.figure(figsize=(12, 6))
plt.plot(bin_centers, power_law_hist, marker="x", color='red', label='Power-Law Distribution', alpha=0.7)
plt.plot(bin_centers, half_normal_hist, marker="x", color='blue', label='Scaled & Shifted Half-Normal Distribution', alpha=0.7)
plt.plot(bin_centers[inv_idx], half_normal_hist[inv_idx], marker="o", color="green", linestyle='none', label='cross') 

# Set both axes to log scale
plt.xscale('log')
plt.yscale('log')

# Limit x-axis to relevant range where density is above 0.1
mask = (power_law_hist > 0.1) | (half_normal_hist > 0.1)
plot_min, plot_max = bin_centers[mask][0], bin_centers[mask][-1]
plt.xlim(plot_min, plot_max)

# Add title with empirical standard deviations
plt.xlabel('Value')
plt.ylabel('Density')
plt.legend()
plt.title(f'Empirical Distributions: Power-Law vs. Scaled & Shifted Half-Normal (Log-Log Plot)\n'
          f'Std Dev (Power-Law): {power_law_std:.3f} | Std Dev (Scaled Half-Normal): {half_normal_std:.3f}')
plt.show()


