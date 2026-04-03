args <- commandArgs(trailingOnly = TRUE)
csv_path <- args[1]

library(metafor)

dat <- read.csv(csv_path)

# Binary data: compute log OR with continuity correction only for zero cells
dat_es <- escalc(measure = "OR",
                 ai = dat$e_cases, n1i = dat$e_n,
                 ci = dat$c_cases, n2i = dat$c_n,
                 add = 0.5, to = "only0")

# --- Normal-theory REML ---
res <- rma(yi, vi, data = dat_es, method = "REML")

# Prediction interval (normal-theory, k-2 df)
pred <- predict(res, level = 0.95)

cat(sprintf("estimate=%.8f\n", coef(res)))
cat(sprintf("se=%.8f\n", res$se))
cat(sprintf("tau2=%.8f\n", res$tau2))
cat(sprintf("I2=%.6f\n", res$I2))
cat(sprintf("ci_lower=%.8f\n", res$ci.lb))
cat(sprintf("ci_upper=%.8f\n", res$ci.ub))
cat(sprintf("pi_lower=%.8f\n", pred$pi.lb))
cat(sprintf("pi_upper=%.8f\n", pred$pi.ub))
cat(sprintf("p_value=%.8f\n", res$pval))
cat(sprintf("Q=%.8f\n", res$QE))

# --- HKSJ (Knapp-Hartung) REML ---
res_hksj <- rma(yi, vi, data = dat_es, method = "REML", test = "knha")

pred_hksj <- predict(res_hksj, level = 0.95)

cat(sprintf("hksj_estimate=%.8f\n", coef(res_hksj)))
cat(sprintf("hksj_se=%.8f\n", res_hksj$se))
cat(sprintf("hksj_tau2=%.8f\n", res_hksj$tau2))
cat(sprintf("hksj_I2=%.6f\n", res_hksj$I2))
cat(sprintf("hksj_ci_lower=%.8f\n", res_hksj$ci.lb))
cat(sprintf("hksj_ci_upper=%.8f\n", res_hksj$ci.ub))
cat(sprintf("hksj_pi_lower=%.8f\n", pred_hksj$pi.lb))
cat(sprintf("hksj_pi_upper=%.8f\n", pred_hksj$pi.ub))
cat(sprintf("hksj_p_value=%.8f\n", res_hksj$pval))
cat(sprintf("hksj_Q=%.8f\n", res_hksj$QE))
