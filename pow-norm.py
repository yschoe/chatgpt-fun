'''

  comparing half-normal distribution with power-law distribution with 
  the same standard deviation.

  https://chatgpt.com/share/6734eee1-a9b4-8003-88c0-b835291ba6f8

'''


import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import halfnorm

# Set parameters
num_samples = 100000
alpha = 10.0  # Power-law exponent (typically > 1)
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

# Define more histogram bins based on the combined range of the data
all_samples = np.concatenate((power_law_samples, half_normal_samples_scaled_shifted))
num_bins = 300
bins = np.linspace(np.min(all_samples), np.max(all_samples), num_bins)

# Compute histograms for each distribution to find the 0.1 density threshold
power_law_hist, bin_edges = np.histogram(power_law_samples, bins=bins, density=True)
half_normal_hist, _ = np.histogram(half_normal_samples_scaled_shifted, bins=bins, density=True)

# Find the range where density is greater than 0.1 in either distribution
bin_centers = 0.5 * (bin_edges[1:] + bin_edges[:-1])
mask = (power_law_hist > 0.1) | (half_normal_hist > 0.1)
plot_min, plot_max = bin_centers[mask][0], bin_centers[mask][-1]

# Plot the two scaled and shifted distributions using the same bins, restricting the range
plt.figure(figsize=(12, 6))
plt.hist(power_law_samples, bins=bins, density=True, alpha=0.5, color='red', label='Power-Law Distribution')
plt.hist(half_normal_samples_scaled_shifted, bins=bins, density=True, alpha=0.5, color='blue', label='Scaled & Shifted Half-Normal Distribution')
plt.xlim(plot_min, plot_max)

# Set both axes to log scale
plt.xscale('log')
plt.yscale('log')

# Add title with empirical standard deviations
plt.xlabel('Value')
plt.ylabel('Density')
plt.legend()
plt.title(f'Empirical Distributions: Power-Law vs. Scaled & Shifted Half-Normal (Log-Log Plot)\n'
          f'Std Dev (Power-Law): {power_law_std:.3f} | Std Dev (Scaled Half-Normal): {half_normal_std:.3f}')
plt.show()
