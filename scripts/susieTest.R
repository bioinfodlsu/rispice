library(susieR)
library(MASS)

set.seed(42)

n <- 50     # num of samples
p <- 10     # num of SNPs

# Create Toy Example Case: 
#     SNP2 and SNP4 are causal,
#     SNP 1 is correlated to SNP 2
#     SNP 3 is correlated to SNP 4
Z_indep <- matrix(rnorm(n * p), nrow = n, ncol = p)     # make a n*p matrix from normally dist. random var

Z_indep[,1] <- Z_indep[,2]   # SNP1 <- SNP2 (perfectly correlated)
Z_indep[,3] <- Z_indep[,4]   # SNP3 <- SNP4 (perfectly correlated)

# Convert values into raw genotypes (0,1,2)
make_genotypes <- function(col) {
  as.numeric(as.character(cut(col,
                              breaks = quantile(col, probs = c(0, 0.33, 0.66, 1)),
                              labels = c(0,1,2),
                              include.lowest = TRUE)))
}
X_raw <- apply(Z_indep, 2, make_genotypes)  # n x p matrix of 0/1/2
X <- scale(X_raw)   # Standardize

# Check correlation
print(round(cor(X[,1:4]), 3))


# Define True Effect Values
beta_true <- rep(0, p)
beta_true[2] <- 1.5   # causal
beta_true[4] <- 1.2   # causal

sigma_noise <- 1
y <- as.numeric(X %*% beta_true + rnorm(n, sd = sigma_noise))   # generate phenotype based on true causal and generated X values


# Note: SuSIE in Individual Type Data (SNPs) does not need to use the LD matrix
# It is implicitly acquired via the Genotype Matrix (via standardization)

# RUN SuSIE without Prior (Uniform)
fit <- susie(X, y, L = 2)

cat("SuSIE Results without a Prior\n")
cat("PIPs:\n")
print(round(fit$pip, 3))
cat("")
cat("\nCredible sets (variables in sets):\n")
print(fit$sets$cs)    # list of vectors of indices in each credible set
cat("")
summary(fit)


# Add a Prior
prior <- rep(1/15, p)       # Note this adds up to 1
prior[2] <- 4/15
prior[4] <- 3/15
cat("\n PRIOR: \n")
print(prior)

fit_prior <- susie(X, y, L = 2, prior_weights = prior)

cat("SuSIE Results WITH a Prior\n")
cat("PIPs:\n")
print(round(fit_prior$pip, 3))
cat("")
cat("\nCredible sets (variables in sets):\n")
print(fit_prior$sets$cs) 
cat("")
summary(fit_prior)

# Note: Case above simulated "Perfect" Correlation between SNPs (1 & 2) and (3 & 4)
# This result showed the significant effect of having uniform vs informed priors (although the case is ideal)