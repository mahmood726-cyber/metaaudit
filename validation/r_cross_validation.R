#!/usr/bin/env Rscript
# MetaAudit R Cross-Validation Script
# Validates Python REML engine against metafor on benchmark datasets.
#
# NOTE: Python uses max(1.0, HKSJ_factor) as a conservative floor (prevents
# CI narrower than standard). metafor does not apply this floor by default.
# This script validates:
#   - Core engine (estimate, tau2, I2, Q): directly against metafor
#   - HKSJ SE/CI/PI: against metafor + manual floor adjustment
#
# Usage: Rscript r_cross_validation.R
# Requires: metafor (>= 4.0)

library(metafor)

resolve_project_root <- function() {
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", args, value = TRUE)
  if (length(file_arg) > 0) {
    script_path <- sub("^--file=", "", file_arg[[1]])
    return(normalizePath(file.path(dirname(script_path), ".."), winslash = "/", mustWork = TRUE))
  }
  normalizePath("..", winslash = "/", mustWork = TRUE)
}

PROJECT_ROOT <- resolve_project_root()
PY_IMPORT_PREFIX <- paste0(
  "import numpy as np; import sys; sys.path.insert(0, ",
  shQuote(PROJECT_ROOT),
  "); "
)

cat("=== MetaAudit R Cross-Validation ===\n")
cat("metafor version:", as.character(packageVersion("metafor")), "\n")
cat("Note: Python applies max(1, HKSJ_factor) floor; R comparison adjusts for this.\n\n")

n_pass <- 0
n_fail <- 0

check <- function(name, python_val, r_val, tol = 1e-4) {
  diff <- abs(python_val - r_val)
  ok <- diff < tol
  status <- ifelse(ok, "PASS", "FAIL")
  cat(sprintf("  %s: Python=%.6f  R=%.6f  diff=%.2e  [%s]\n",
              name, python_val, r_val, diff, status))
  if (ok) n_pass <<- n_pass + 1 else n_fail <<- n_fail + 1
  invisible(ok)
}

# Helper: apply Python's HKSJ floor to metafor result
apply_hksj_floor <- function(res) {
  # metafor stores the HKSJ factor internally. We reconstruct it.
  # HKSJ_factor = sum(w_i * (yi - theta)^2) / (k-1)
  # When factor < 1, Python uses 1.0 instead (wider CI, conservative)
  wi <- 1.0 / (res$vi + res$tau2)
  q_resid <- sum(wi * (res$yi - as.numeric(res$beta))^2)
  k <- res$k
  hksj_factor <- q_resid / (k - 1)

  se_standard <- 1.0 / sqrt(sum(wi))

  if (hksj_factor < 1.0) {
    # Python uses floor of 1.0
    se_adj <- se_standard  # factor = 1.0
    df <- k - 1
    t_crit <- qt(0.975, df)
    ci_lb <- as.numeric(res$beta) - t_crit * se_adj
    ci_ub <- as.numeric(res$beta) + t_crit * se_adj
    # PI
    pi_se <- sqrt(se_adj^2 + res$tau2)
    df_pi <- k - 2
    t_pi <- qt(0.975, max(1, df_pi))
    pi_lb <- as.numeric(res$beta) - t_pi * pi_se
    pi_ub <- as.numeric(res$beta) + t_pi * pi_se
  } else {
    # factor >= 1.0: Python and metafor agree
    se_adj <- res$se
    ci_lb <- res$ci.lb
    ci_ub <- res$ci.ub
    pred <- predict(res, level = 0.95)
    pi_lb <- pred$pi.lb
    pi_ub <- pred$pi.ub
  }
  list(se = se_adj, ci_lb = ci_lb, ci_ub = ci_ub,
       pi_lb = pi_lb, pi_ub = pi_ub, hksj_factor = hksj_factor)
}

# Helper: get Python values for given yi, vi
get_python_vals <- function(yi_str, vi_str) {
  cmd <- paste0(
    PY_IMPORT_PREFIX,
    "from metaaudit.recompute import pool_effects_reml, compute_prediction_interval; ",
    "yi=np.array(", yi_str, "); vi=np.array(", vi_str, "); ",
    "p=pool_effects_reml(yi,vi); ",
    "pi=compute_prediction_interval(p['estimate'],p['se_hksj'],p['tau2'],p['k']); ",
    "print(','.join([f'{v:.10f}' for v in [p['estimate'],p['se_hksj'],p['ci_lower'],p['ci_upper'],",
    "p['tau2'],p['I2'],p['Q'],p['p_value'],pi['pi_lower'],pi['pi_upper']]]))"
  )
  py_out <- system2("python", args = c("-c", shQuote(cmd)), stdout = TRUE, stderr = FALSE)
  vals <- as.numeric(strsplit(py_out, ",")[[1]])
  names(vals) <- c("estimate", "se_hksj", "ci_lower", "ci_upper",
                    "tau2", "I2", "Q", "p_value", "pi_lower", "pi_upper")
  vals
}

run_benchmark <- function(name, yi, vi, py_yi_str, py_vi_str) {
  cat(sprintf("\n--- %s ---\n", name))

  res <- rma(yi = yi, vi = vi, method = "REML", test = "knha")
  adj <- apply_hksj_floor(res)
  py <- get_python_vals(py_yi_str, py_vi_str)

  cat(sprintf("  k=%d, tau2=%.4f, HKSJ_factor=%.4f %s\n",
              res$k, res$tau2, adj$hksj_factor,
              ifelse(adj$hksj_factor < 1, "(FLOOR APPLIED)", "")))

  # Core engine (always compare directly)
  check("estimate", py["estimate"], as.numeric(res$beta))
  check("tau2",     py["tau2"],     res$tau2)
  check("I2",       py["I2"],       res$I2, tol = 1e-2)
  check("Q",        py["Q"],        res$QE)

  # HKSJ-adjusted (compare with floor-adjusted R values)
  check("se_hksj",  py["se_hksj"],  adj$se, tol = 1e-3)
  check("ci_lower", py["ci_lower"], adj$ci_lb, tol = 1e-3)
  check("ci_upper", py["ci_upper"], adj$ci_ub, tol = 1e-3)

  # PI (only if k >= 3)
  if (res$k >= 3) {
    check("pi_lower", py["pi_lower"], adj$pi_lb, tol = 1e-3)
    check("pi_upper", py["pi_upper"], adj$pi_ub, tol = 1e-3)
  }
}

# =========================================================================
# Benchmark 1: Binary (k=5, logOR, tau2=0)
# =========================================================================
e_cases <- c(10, 20, 15, 25, 12)
e_n     <- c(50, 80, 60, 100, 45)
c_cases <- c(15, 25, 20, 30, 18)
c_n     <- c(55, 85, 65, 95, 50)
a <- e_cases; b <- e_n - e_cases; cc <- c_cases; d <- c_n - c_cases
yi1 <- log((a * d) / (b * cc))
vi1 <- 1/a + 1/b + 1/cc + 1/d

# Python computes log-OR internally, so pass raw data
py_cmd_b1 <- paste0(
  PY_IMPORT_PREFIX,
  "from metaaudit.recompute import compute_log_or, pool_effects_reml, compute_prediction_interval; ",
  "ec=np.array([10,20,15,25,12]); en=np.array([50,80,60,100,45]); ",
  "cc=np.array([15,25,20,30,18]); cn=np.array([55,85,65,95,50]); ",
  "yi,vi=compute_log_or(ec,en,cc,cn); ",
  "p=pool_effects_reml(yi,vi); pi=compute_prediction_interval(p['estimate'],p['se_hksj'],p['tau2'],p['k']); ",
  "print(','.join([f'{v:.10f}' for v in [p['estimate'],p['se_hksj'],p['ci_lower'],p['ci_upper'],",
  "p['tau2'],p['I2'],p['Q'],p['p_value'],pi['pi_lower'],pi['pi_upper']]]))"
)
py1 <- system2("python", args = c("-c", shQuote(py_cmd_b1)), stdout = TRUE, stderr = FALSE)
py1_vals <- as.numeric(strsplit(py1, ",")[[1]])
names(py1_vals) <- c("estimate","se_hksj","ci_lower","ci_upper","tau2","I2","Q","p_value","pi_lower","pi_upper")

cat("\n--- Benchmark 1: Binary (k=5, logOR, tau2=0) ---\n")
res1 <- rma(yi = yi1, vi = vi1, method = "REML", test = "knha")
adj1 <- apply_hksj_floor(res1)
cat(sprintf("  k=%d, tau2=%.4f, HKSJ_factor=%.4f %s\n",
            res1$k, res1$tau2, adj1$hksj_factor,
            ifelse(adj1$hksj_factor < 1, "(FLOOR APPLIED)", "")))
check("estimate", py1_vals["estimate"], as.numeric(res1$beta))
check("tau2",     py1_vals["tau2"],     res1$tau2)
check("I2",       py1_vals["I2"],       res1$I2, tol = 1e-2)
check("Q",        py1_vals["Q"],        res1$QE)
check("se_hksj",  py1_vals["se_hksj"],  adj1$se, tol = 1e-3)
check("ci_lower", py1_vals["ci_lower"], adj1$ci_lb, tol = 1e-3)
check("ci_upper", py1_vals["ci_upper"], adj1$ci_ub, tol = 1e-3)
check("pi_lower", py1_vals["pi_lower"], adj1$pi_lb, tol = 1e-3)
check("pi_upper", py1_vals["pi_upper"], adj1$pi_ub, tol = 1e-3)

# =========================================================================
# Benchmark 2: Continuous (k=4, MD, tau2=0)
# =========================================================================
e_mean <- c(5.2, 4.8, 5.5, 4.9); c_mean <- c(4.5, 4.2, 4.8, 4.3)
e_sd <- c(1.1, 1.3, 0.9, 1.2); c_sd <- c(1.2, 1.4, 1.0, 1.3)
e_n2 <- c(30, 25, 35, 28); c_n2 <- c(32, 27, 33, 30)
yi2 <- e_mean - c_mean
vi2 <- (e_sd^2)/e_n2 + (c_sd^2)/c_n2

# Use exact Python compute_md for proper comparison
py_cmd_b2 <- paste0(
  PY_IMPORT_PREFIX,
  "from metaaudit.recompute import compute_md, pool_effects_reml, compute_prediction_interval; ",
  "em=np.array([5.2,4.8,5.5,4.9]); esd=np.array([1.1,1.3,0.9,1.2]); en=np.array([30,25,35,28]); ",
  "cm=np.array([4.5,4.2,4.8,4.3]); csd=np.array([1.2,1.4,1.0,1.3]); cn=np.array([32,27,33,30]); ",
  "yi,vi=compute_md(em,esd,en,cm,csd,cn); ",
  "p=pool_effects_reml(yi,vi); pi=compute_prediction_interval(p['estimate'],p['se_hksj'],p['tau2'],p['k']); ",
  "print(','.join([f'{v:.10f}' for v in [p['estimate'],p['se_hksj'],p['ci_lower'],p['ci_upper'],",
  "p['tau2'],p['I2'],p['Q'],p['p_value'],pi['pi_lower'],pi['pi_upper']]]))"
)
py2 <- system2("python", args = c("-c", shQuote(py_cmd_b2)), stdout = TRUE, stderr = FALSE)
py2_vals <- as.numeric(strsplit(py2, ",")[[1]])
names(py2_vals) <- c("estimate","se_hksj","ci_lower","ci_upper","tau2","I2","Q","p_value","pi_lower","pi_upper")

cat("\n--- Benchmark 2: Continuous (k=4, MD, tau2=0) ---\n")
res2 <- rma(yi = yi2, vi = vi2, method = "REML", test = "knha")
adj2 <- apply_hksj_floor(res2)
cat(sprintf("  k=%d, tau2=%.4f, HKSJ_factor=%.4f %s\n",
            res2$k, res2$tau2, adj2$hksj_factor,
            ifelse(adj2$hksj_factor < 1, "(FLOOR APPLIED)", "")))
check("estimate", py2_vals["estimate"], as.numeric(res2$beta))
check("tau2",     py2_vals["tau2"],     res2$tau2)
check("I2",       py2_vals["I2"],       res2$I2, tol = 1e-2)
check("Q",        py2_vals["Q"],        res2$QE)
check("se_hksj",  py2_vals["se_hksj"],  adj2$se, tol = 1e-3)
check("ci_lower", py2_vals["ci_lower"], adj2$ci_lb, tol = 1e-3)
check("ci_upper", py2_vals["ci_upper"], adj2$ci_ub, tol = 1e-3)
check("pi_lower", py2_vals["pi_lower"], adj2$pi_lb, tol = 1e-3)
check("pi_upper", py2_vals["pi_upper"], adj2$pi_ub, tol = 1e-3)

# =========================================================================
# Benchmark 3: High heterogeneity (k=8, binary)
# =========================================================================
e3_cases <- c(3, 12, 25, 8, 40, 5, 18, 30)
e3_n     <- c(20, 50, 80, 30, 120, 25, 60, 100)
c3_cases <- c(8, 18, 20, 12, 35, 10, 22, 25)
c3_n     <- c(22, 55, 75, 35, 110, 28, 65, 95)

a3 <- e3_cases; b3 <- e3_n-e3_cases; cc3 <- c3_cases; d3 <- c3_n-c3_cases
yi3 <- log((a3*d3)/(b3*cc3)); vi3 <- 1/a3+1/b3+1/cc3+1/d3

py_cmd_b3 <- paste0(
  PY_IMPORT_PREFIX,
  "from metaaudit.recompute import pool_effects_reml, compute_prediction_interval; ",
  "a=np.array([3,12,25,8,40,5,18,30],float); b=np.array([20,50,80,30,120,25,60,100],float)-a; ",
  "c=np.array([8,18,20,12,35,10,22,25],float); d=np.array([22,55,75,35,110,28,65,95],float)-c; ",
  "yi=np.log((a*d)/(b*c)); vi=1/a+1/b+1/c+1/d; ",
  "p=pool_effects_reml(yi,vi); pi=compute_prediction_interval(p['estimate'],p['se_hksj'],p['tau2'],p['k']); ",
  "print(','.join([f'{v:.10f}' for v in [p['estimate'],p['se_hksj'],p['ci_lower'],p['ci_upper'],",
  "p['tau2'],p['I2'],p['Q'],p['p_value'],pi['pi_lower'],pi['pi_upper']]]))"
)
py3 <- system2("python", args = c("-c", shQuote(py_cmd_b3)), stdout = TRUE, stderr = FALSE)
py3_vals <- as.numeric(strsplit(py3, ",")[[1]])
names(py3_vals) <- c("estimate","se_hksj","ci_lower","ci_upper","tau2","I2","Q","p_value","pi_lower","pi_upper")

cat("\n--- Benchmark 3: High heterogeneity (k=8, binary) ---\n")
res3 <- rma(yi = yi3, vi = vi3, method = "REML", test = "knha")
adj3 <- apply_hksj_floor(res3)
cat(sprintf("  k=%d, tau2=%.4f, HKSJ_factor=%.4f %s\n",
            res3$k, res3$tau2, adj3$hksj_factor,
            ifelse(adj3$hksj_factor < 1, "(FLOOR APPLIED)", "")))
check("estimate", py3_vals["estimate"], as.numeric(res3$beta))
check("tau2",     py3_vals["tau2"],     res3$tau2)
check("I2",       py3_vals["I2"],       res3$I2, tol = 1e-2)
check("Q",        py3_vals["Q"],        res3$QE)
check("se_hksj",  py3_vals["se_hksj"],  adj3$se, tol = 1e-3)
check("ci_lower", py3_vals["ci_lower"], adj3$ci_lb, tol = 1e-3)
check("ci_upper", py3_vals["ci_upper"], adj3$ci_ub, tol = 1e-3)
check("pi_lower", py3_vals["pi_lower"], adj3$pi_lb, tol = 1e-3)
check("pi_upper", py3_vals["pi_upper"], adj3$pi_ub, tol = 1e-3)

# =========================================================================
# Benchmark 4: Homogeneous (k=5, GIV-style)
# =========================================================================
yi4 <- c(-0.30, -0.28, -0.32, -0.29, -0.31)
vi4 <- c(0.04, 0.05, 0.04, 0.05, 0.04)

run_benchmark("Benchmark 4: Homogeneous (k=5, GIV, tau2~0)",
              yi4, vi4,
              "[-0.30,-0.28,-0.32,-0.29,-0.31]",
              "[0.04,0.05,0.04,0.05,0.04]")

# =========================================================================
# Benchmark 5: Edge case (k=2, large tau2)
# =========================================================================
yi5 <- c(-0.50, 0.20)
vi5 <- c(0.10, 0.08)

cat("\n--- Benchmark 5: Edge case (k=2, large tau2) ---\n")
res5 <- rma(yi = yi5, vi = vi5, method = "REML", test = "knha")
adj5 <- apply_hksj_floor(res5)
py5 <- get_python_vals("[-0.50,0.20]", "[0.10,0.08]")
cat(sprintf("  k=%d, tau2=%.4f, HKSJ_factor=%.4f %s\n",
            res5$k, res5$tau2, adj5$hksj_factor,
            ifelse(adj5$hksj_factor < 1, "(FLOOR APPLIED)", "")))
check("estimate", py5["estimate"], as.numeric(res5$beta))
check("tau2",     py5["tau2"],     res5$tau2)
check("I2",       py5["I2"],       res5$I2, tol = 1e-2)
check("Q",        py5["Q"],        res5$QE)
check("se_hksj",  py5["se_hksj"],  adj5$se, tol = 1e-3)
check("ci_lower", py5["ci_lower"], adj5$ci_lb, tol = 1e-3)
check("ci_upper", py5["ci_upper"], adj5$ci_ub, tol = 1e-3)

# =========================================================================
# Benchmark 6: Real-world scenario (k=12, moderate heterogeneity)
# =========================================================================
set.seed(42)
true_mu <- -0.35; true_tau <- 0.15
yi6 <- c(-0.52, -0.18, -0.41, -0.33, -0.55, -0.22, -0.38, -0.47, -0.29, -0.61, -0.15, -0.43)
vi6 <- c(0.03, 0.05, 0.04, 0.06, 0.03, 0.07, 0.04, 0.05, 0.06, 0.03, 0.08, 0.04)

run_benchmark("Benchmark 6: Realistic (k=12, moderate heterogeneity)",
              yi6, vi6,
              "[-0.52,-0.18,-0.41,-0.33,-0.55,-0.22,-0.38,-0.47,-0.29,-0.61,-0.15,-0.43]",
              "[0.03,0.05,0.04,0.06,0.03,0.07,0.04,0.05,0.06,0.03,0.08,0.04]")

# =========================================================================
# Summary
# =========================================================================
total <- n_pass + n_fail
cat(sprintf("\n========================================\n"))
cat(sprintf("SUMMARY: %d/%d PASS (%d FAIL)\n", n_pass, total, n_fail))
cat(sprintf("========================================\n"))
if (n_fail == 0) {
  cat("ALL BENCHMARKS PASSED.\n")
  cat("Python REML engine matches metafor (with documented HKSJ floor).\n")
} else {
  cat("Some benchmarks failed. Investigate.\n")
}
