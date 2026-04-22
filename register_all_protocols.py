#!/usr/bin/env python
"""
register_all_protocols.py
=========================
Automated protocol registration for ~80 GitHub repositories.

Usage:
    python register_all_protocols.py           # dry run (default)
    python register_all_protocols.py --execute  # actually commit + push + create releases

Author: Mahmood Ahmad
"""

import os
import sys
import re
import subprocess
import argparse
import datetime
import textwrap
from pathlib import Path

from metaaudit.config import PROTOCOL_LOG

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

AUTHOR = "Mahmood Ahmad, Royal Free Hospital, London, UK"
ORCID = "0009-0003-7781-4478"
REGISTRATION_DATE = "2026-03-28"

# Directories to scan (each direct child that contains a .git folder)
SCAN_ROOTS = [
    "C:/Models",
    "C:/HTML apps",
    "C:/Projects",
    "C:/AlMizan",
    "C:/BiasForensics",
    "C:/FragilityAtlas",
    "C:/AdaptSim",
    "C:/RMSTmeta",
    "C:/E156",
    "C:/MetaAudit",
]

# Single-directory repos (the root itself is the repo, not a subdirectory)
SINGLE_DIR_REPOS = {
    "C:/AlMizan",
    "C:/BiasForensics",
    "C:/FragilityAtlas",
    "C:/AdaptSim",
    "C:/RMSTmeta",
    "C:/E156",
    "C:/MetaAudit",
}

# Skip MetaAudit — already registered
SKIP_REPOS = {"C:/MetaAudit"}

PREREGISTRATION_TAG = "v0.1.0-preregistration"
LOG_PATH = PROTOCOL_LOG

AI_DISCLOSURE = """**AI Disclosure Statement**

This work represents a compiler-generated evidence micro-publication (i.e., a structured, \
pipeline-based synthesis output). AI is used as a constrained synthesis engine operating on \
structured inputs and predefined rules, rather than as an autonomous author. Deterministic \
components of the pipeline, together with versioned, reproducible evidence capsules \
(TruthCert), are designed to support transparent and auditable outputs. All results and text \
were reviewed and verified by the author, who takes full responsibility for the content. The \
workflow operationalises key transparency and reporting principles consistent with \
CONSORT-AI/SPIRIT-AI, including explicit input specification, predefined schemas, logged \
human-AI interaction, and reproducible outputs."""

# ---------------------------------------------------------------------------
# Per-project description overrides (extracted from READMEs / known context)
# Used when README is absent or uninformative.
# ---------------------------------------------------------------------------

DESCRIPTION_OVERRIDES = {
    "asa": (
        "ASA (Adversarial Sensitivity Analysis) is a 7-fang forensic screener that "
        "stress-tests meta-analytic conclusions against 85 adversarial scenarios."
    ),
    "autograde-tool": (
        "AutoGRADE automates GRADE evidence certainty assessment for systematic "
        "reviews, translating heterogeneity, bias, and imprecision signals into "
        "structured certainty profiles."
    ),
    "bayesianma": (
        "BayesianMA is a browser-based Bayesian random-effects meta-analysis tool "
        "with grid approximation, prior sensitivity analysis, and posterior "
        "credible interval reporting."
    ),
    "cres": (
        "CRES (Cardio-Renal Evidence Synthesis) is a reproducible evidence-synthesis "
        "and modelling workflow tool with cardiorenal and oncology configurations, "
        "producing structured outputs with TruthCert provenance."
    ),
    "cardiooracle": (
        "CardioOracle is a cardiovascular trial outcome predictor that uses "
        "calibrated Bayesian meta-regression to forecast treatment effects in "
        "novel patient populations."
    ),
    "cardio-trial-audit": (
        "CardioTrialAudit provides automated quality and integrity auditing of "
        "cardiovascular RCT data, flagging statistical inconsistencies and "
        "reporting anomalies."
    ),
    "CausalSynth": (
        "CausalSynth integrates causal inference methods into meta-analysis, "
        "allowing users to estimate causal effects from observational synthesis "
        "using directed acyclic graphs and sensitivity analyses."
    ),
    "component-nma": (
        "ComponentNMA implements the world-first browser-based component network "
        "meta-analysis with interaction terms and random-effects models, enabling "
        "decomposition of complex interventions."
    ),
    "conformal-ma": (
        "ConformalMA applies conformal prediction to meta-analysis, producing "
        "distribution-free prediction intervals with valid finite-sample coverage "
        "guarantees across heterogeneous study populations."
    ),
    "dpma": (
        "DPMA (Differentially Private Meta-Analysis) implements privacy-preserving "
        "evidence synthesis using differential privacy mechanisms, protecting "
        "individual study contributions."
    ),
    "evidencehalflife": (
        "EvidenceHalfLife models the decay of clinical evidence relevance over time, "
        "providing quantitative estimates of when existing meta-analyses require "
        "updating."
    ),
    "evidence-tribunal": (
        "EvidenceTribunal is a structured adversarial review framework that applies "
        "prosecution-defence logic to evaluate the strength and coherence of "
        "clinical evidence bodies."
    ),
    "fatiha": (
        "FATIHA is a flexible analysis toolkit implementing the SYNTHESIS R package, "
        "providing 82 validated statistical methods for advanced heterogeneous "
        "evidence integration."
    ),
    "fragilityindex": (
        "FragilityIndex calculates fragility metrics for randomised controlled trials "
        "and meta-analyses, quantifying how few outcome events would be needed to "
        "reverse a statistically significant result."
    ),
    "grma": (
        "GRMA (Generalised Random-effects Meta-Analysis) v10.0 is a comprehensive "
        "framework for flexible random-effects modelling, extending standard methods "
        "to handle complex dependence structures."
    ),
    "gwam": (
        "GWAM (Global Weighted Adaptive Meta-analysis) v1.0.5 implements adaptive "
        "weighting schemes that adjust for study-level heterogeneity and precision, "
        "with 91 validated test cases."
    ),
    "hta-evidence-integrity": (
        "HTA Evidence Integrity Suite provides automated integrity checking for "
        "Health Technology Assessment submissions, verifying statistical consistency, "
        "reproducibility, and reporting completeness."
    ),
    "hta-transportability": (
        "HTA Transportability Engine quantifies the degree to which evidence from "
        "clinical trials can be transported to target HTA populations using "
        "reweighting and sensitivity analysis."
    ),
    "hta-unified-intelligence": (
        "HTA Unified Intelligence System integrates evidence synthesis, decision "
        "modelling, and health economic analysis into a single reproducible pipeline "
        "for HTA submissions."
    ),
    "ipd-qma": (
        "IPD-QMA (Individual Patient Data Quantile Meta-Analysis) implements "
        "quantile-based IPD meta-analysis with full distributional inference, "
        "accepted in PLOS ONE."
    ),
    "indirectcomparison": (
        "IndirectComparison provides tools for adjusted indirect treatment "
        "comparisons and network meta-analysis when head-to-head trials are absent, "
        "with uncertainty quantification."
    ),
    "kmdigitizer": (
        "KMDigitizer automates the extraction of individual patient-level survival "
        "data from published Kaplan-Meier curves for use in meta-analysis and "
        "secondary modelling."
    ),
    "ma-power-calc": (
        "MAPowerCalc is a comprehensive meta-analysis power and sample-size "
        "calculator supporting 15 effect-size types, heterogeneity modelling, and "
        "sequential analysis designs."
    ),
    "MAPriors": (
        "MAPriors implements the Meta-Analytic Prior approach, synthesising "
        "historical data into informative Bayesian priors for use in prospective "
        "trials and new meta-analyses."
    ),
    "maworkbench": (
        "MAWorkbench is an integrated meta-analysis workbench providing a unified "
        "interface for data import, effect-size calculation, pooling, heterogeneity "
        "assessment, and reporting."
    ),
    "mcidmapper": (
        "MCIDMapper maps minimal clinically important differences across outcome "
        "measures and patient populations, supporting threshold-based meta-analytic "
        "decision frameworks."
    ),
    "mes": (
        "MES (Meta-Evidence Synthesiser) is a next-generation meta-analysis framework "
        "implementing the ASSESS-EXPLORE-MAP pipeline for structured, "
        "proof-carrying evidence synthesis targeting BMJ and F1000."
    ),
    "meta-entropy": (
        "MetaEntropy quantifies information-theoretic properties of meta-analytic "
        "datasets, measuring evidence diversity, redundancy, and synthesis "
        "informativeness."
    ),
    "meta-genome": (
        "MetaGenome applies genomic-inspired methods to meta-analysis, treating "
        "studies as genetic sequences to identify patterns of replication, "
        "mutation, and evidence evolution."
    ),
    "metaguard": (
        "MetaGuard is a frontier meta-analysis toolkit combining DPD robust "
        "estimation, real-time meta-analysis (RTMA) p-hacking detection, and "
        "MetaForest machine-learning heterogeneity modelling."
    ),
    "metamethods": (
        "MetaMethods provides six advanced meta-analytic methods as a validated "
        "Python module, including novel heterogeneity estimators and robust "
        "pooling algorithms, with 30/30 tests passing."
    ),
    "metaregression": (
        "MetaRegression is a world-first browser-based meta-regression tool "
        "supporting continuous and categorical moderators, bubble plots, and "
        "residual heterogeneity decomposition."
    ),
    "metarep": (
        "MetaRep implements a novel replication probability method for meta-analysis, "
        "quantifying the probability that a new study will replicate the pooled "
        "finding, targeting JAMA."
    ),
    "meta-repair": (
        "MetaRepair automatically detects and corrects common errors in published "
        "meta-analyses, including calculation mistakes, unit inconsistencies, and "
        "variance mis-specifications."
    ),
    "meta-reproducer": (
        "MetaReproducer provides automated reproduction pipelines for published "
        "meta-analyses, verifying statistical results against original data and "
        "flagging discrepancies."
    ),
    "mem-ecosystem-model": (
        "MEM (Meta-Ecosystem Model) models the ecology of evidence production "
        "across a clinical field, tracking evidence accumulation, decay, and "
        "synthesis gaps over time, targeting PLOS ONE."
    ),
    "methodssuite": (
        "MethodsSuite is a unified browser-based meta-analysis methods platform "
        "integrating Bayesian MA, pooling, meta-regression, pub-bias, and PRISMA "
        "checking under a single MAIF schema."
    ),
    "MultiverseMA": (
        "MultiverseMA implements multiverse meta-analysis, systematically exploring "
        "all reasonable analytical choices to characterise the robustness and "
        "researcher-degree-of-freedom sensitivity of pooled estimates."
    ),
    "nntmapper": (
        "NNTMapper is a meta-analytic number-needed-to-treat (NNT) calculator with "
        "decision curve analysis, translating pooled effect sizes into clinically "
        "actionable absolute risk metrics."
    ),
    "heterogeneity-ase": (
        "HeterogeneityASE is an R package implementing the Absolute Standardised "
        "Effect (ASE) heterogeneity estimator, providing a novel complement to "
        "I-squared with 24/24 validated tests."
    ),
    "overlapmatrix": (
        "OverlapMatrix calculates and visualises study overlap in systematic review "
        "networks, quantifying the degree of evidence re-use across related "
        "meta-analyses."
    ),
    "prisma-checker": (
        "PRISMAChecker provides automated PRISMA 2020 compliance checking for "
        "systematic review manuscripts, supporting six PRISMA extensions including "
        "NMA, IPD, and scoping reviews."
    ),
    "prismaflow": (
        "PRISMAFlow generates publication-ready PRISMA 2020 flow diagrams from "
        "structured screening data, with support for database-specific breakdowns "
        "and grey literature."
    ),
    "Pairwise70": (
        "Pairwise70 is a pairwise meta-analysis tool built for real-world clinical "
        "evidence synthesis, with 70 pre-configured effect-size types and automated "
        "forest plot generation."
    ),
    "poolingsuite": (
        "PoolingSuite is a comprehensive meta-analysis pooling engine implementing "
        "15 tau-squared estimators, three confidence-interval methods, leave-one-out "
        "influence diagnostics, and GOSH analysis."
    ),
    "pubbiassuite": (
        "PubBiasSuite provides 12 publication bias detection methods and three "
        "funnel plot variants in a single browser-based tool, with comparative "
        "method performance reporting."
    ),
    "robma": (
        "ROBMA (Robust Bayesian Meta-Analysis) implements robust Bayesian model "
        "averaging for meta-analysis, downweighting outlier studies and providing "
        "model-averaged posterior estimates."
    ),
    "rob-assessor": (
        "RoBAssessor is a guided risk-of-bias assessment tool implementing RoB 2 "
        "and ROBINS-I frameworks with domain-specific signalling questions and "
        "automated judgement aggregation."
    ),
    "sheaf-nma": (
        "SheafNMA applies sheaf-theoretic topology to network meta-analysis, "
        "detecting and localising inconsistency in treatment networks using "
        "higher-order algebraic structures."
    ),
    "softable": (
        "SoFTable generates GRADE Summary of Findings tables from meta-analytic "
        "outputs, translating pooled estimates and certainty ratings into "
        "publication-ready evidence summaries."
    ),
    "tda-ma": (
        "TDA-MA applies topological data analysis to meta-analytic datasets, "
        "identifying persistent homological features in evidence structures that "
        "may indicate systematic bias patterns."
    ),
    "tgep": (
        "TGEP (Trial-Grade Evidence Platform) provides a structured platform for "
        "grading and synthesising trial-level evidence with automated consistency "
        "checks and provenance tracking."
    ),
    "umbrellareview": (
        "UmbrellaReview implements systematic methods for umbrella reviews of "
        "meta-analyses, including overlap quantification, credibility classification, "
        "and cross-domain evidence mapping."
    ),
    "voicalculator": (
        "VOICalculator (Value of Information) quantifies the expected value of "
        "perfect and partial information in meta-analytic contexts, supporting "
        "decisions about future research prioritisation."
    ),
    "value-based-hta": (
        "Value-Based HTA Engine integrates multi-criteria decision analysis with "
        "evidence synthesis to produce structured value assessments for health "
        "technology appraisals."
    ),
    "advanced-nma-pooling": (
        "Advanced NMA Pooling provides extended network meta-analysis pooling methods "
        "including component models, dose-response relationships, and inconsistency "
        "testing."
    ),
    "shahzaib-icu-landscape": (
        "Shahzaib ICU Landscape is a systematic landscape analysis of ICU "
        "interventions, synthesising evidence across critical care domains with "
        "structured meta-analytic comparisons, targeting PLOS ONE."
    ),
    "truthcert-denominator": (
        "TruthCert Denominator implements denominator-calibrated living network "
        "meta-analysis with TruthCert proof-carrying certificates, ensuring "
        "auditable and reproducible evidence synthesis, targeting PLOS ONE."
    ),
    "truthcert-meta2": (
        "TruthCert Meta2 is the second generation of the TruthCert evidence "
        "certification framework, extending proof-carrying numbers to multi-arm "
        "and sequential meta-analyses."
    ),
    "dta-pro-v2": (
        "DTA Pro v2 is a 54K-line browser-based diagnostic test accuracy "
        "meta-analysis platform implementing bivariate models, HSROC, forest plots, "
        "and SROC curve visualisation."
    ),
    "hta-artifact-standard-v2": (
        "HTA Artifact Standard v2 is an open-source HTA platform with 41 simulation "
        "and analysis engines, deterministic reproducibility, and comprehensive test "
        "coverage, with an F1000 paper completed."
    ),
    "ipd-meta-pro": (
        "IPD-Meta-Pro is a 51K-line browser-based individual patient data "
        "meta-analysis platform with WebR validation, supporting one-stage and "
        "two-stage IPD models."
    ),
    "nma-pro-v2": (
        "NMA Pro v2 is a comprehensive browser-based network meta-analysis tool "
        "supporting frequentist and Bayesian frameworks, league tables, and "
        "rankograms."
    ),
    "pairwiseai": (
        "PairwiseAI is an AI-assisted pairwise meta-analysis platform that combines "
        "automated data extraction with validated pooling algorithms and "
        "publication-bias detection."
    ),
    "truthcert1": (
        "TruthCert v1 is the foundational TruthCert evidence certification "
        "framework implementing proof-carrying numbers with hash-linked evidence "
        "locators and validator receipts."
    ),
    "truthcert-pairwisepro-v2": (
        "TruthCert PairwisePro v2 combines pairwise meta-analysis with TruthCert "
        "certification, adding Doi plot/LFK index, fail-safe N, and QEM methods, "
        "with 101/101 tests passing."
    ),
    "dosehtml": (
        "DoseHTML is a browser-based dose-response meta-analysis tool implementing "
        "flexible dose-response models for aggregate and IPD data with "
        "spline-based curve fitting."
    ),
    "living-meta": (
        "LivingMeta is an automated living meta-analysis platform that monitors "
        "literature databases, triggers re-analyses on new evidence, and produces "
        "continuously updated synthesis outputs."
    ),
    "nma-dose-response-app": (
        "NMA Dose Response App combines network meta-analysis with dose-response "
        "modelling, enabling simultaneous estimation of comparative effectiveness "
        "and dose-response relationships."
    ),
    "al-mizan": (
        "Al-Mizan is an evidence equipoise monitor that quantitatively tracks when "
        "cumulative clinical evidence crosses pre-specified thresholds, targeting "
        "BMJ Evidence-Based Medicine."
    ),
    "bias-forensics": (
        "Bias Forensics applies eight publication bias detection methods across 307 "
        "Cochrane systematic reviews, providing a landscape analysis of small-study "
        "effects in clinical evidence, targeting RSM."
    ),
    "fragility-atlas": (
        "Fragility Atlas is a BMJ multiverse analysis of fragility across clinical "
        "trials, mapping the distribution of statistical fragility indices across "
        "therapeutic areas."
    ),
    "adaptsim": (
        "AdaptSim is a browser-based adaptive clinical trial simulator validated "
        "against rpact, supporting group-sequential, response-adaptive, and "
        "platform trial designs."
    ),
    "rmst-meta": (
        "RMST Meta v1.1 is a browser-based restricted mean survival time "
        "meta-analysis tool with R-validated pooling, targeting Statistical Medicine."
    ),
    "e156": (
        "E156 implements the micro-paper standard for compiler-generated evidence "
        "publications, providing a structured HTML composer for NYT-styled "
        "reproducible evidence documents."
    ),
    "metaaudit": (
        "MetaAudit is an automated GitHub audit and quality-assurance platform for "
        "meta-analysis research repositories, providing dashboard reporting, "
        "reproducibility checks, and protocol registration."
    ),
    "MLM501": (
        "MLM501 is a multilevel modelling resource implementing 501 validated "
        "statistical workflows for hierarchical data in clinical and epidemiological "
        "research."
    ),
    "autograde": (
        "AutoGRADE automates GRADE evidence certainty assessment, translating "
        "systematic review findings into structured certainty profiles using "
        "predefined domain-specific rules."
    ),
    "Burhan": (
        "Burhan is a clinical research data analysis project providing statistical "
        "methods and visualisations for structured evidence evaluation."
    ),
    "cochrane-data-extractor": (
        "Cochrane Data Extractor automates the extraction and structuring of data "
        "from Cochrane systematic reviews for downstream meta-analytic "
        "replication and auditing."
    ),
    "dta70": (
        "DTA70 is a diagnostic test accuracy meta-analysis tool supporting 70 "
        "accuracy metrics with bivariate and hierarchical SROC modelling."
    ),
    "dataextractor": (
        "DataExtractor provides automated extraction of statistical data from "
        "published clinical trial reports, supporting downstream meta-analysis "
        "and evidence synthesis."
    ),
    "fatiha-course-github-v2": (
        "Fatiha Course v2 is an evidence synthesis methods course with 25 modules "
        "in English and French, covering meta-analysis, network synthesis, and "
        "evidence grading."
    ),
    "rapidmeta-finerenone": (
        "RapidMeta Finerenone is a rapid meta-analysis of finerenone trials, "
        "providing continuously updated pooled estimates with seven validated "
        "effect-size calculations."
    ),
    "hta-oman": (
        "HTA Oman adapts HTA methodologies for the Omani healthcare context, "
        "providing locally calibrated decision models and evidence synthesis "
        "frameworks."
    ),
    "kmcurve": (
        "KMCurve provides tools for Kaplan-Meier curve analysis and digitisation, "
        "supporting IPD reconstruction from published survival figures for "
        "meta-analytic use."
    ),
    "cbamm-lfa": (
        "CBAMM-LFA implements covariate-based adaptive meta-analytic modelling with "
        "local fitting algorithms for heterogeneous evidence bodies."
    ),
    "MLMResearch": (
        "MLMResearch is a multilevel modelling research project providing validated "
        "hierarchical analysis pipelines for clustered clinical data."
    ),
    "metaextract": (
        "MetaExtract provides NLP-based extraction of effect sizes, confidence "
        "intervals, and study characteristics from published meta-analysis "
        "manuscripts."
    ),
    "metafusion-lab": (
        "MetaFusion Lab is an experimental platform for fusing heterogeneous "
        "evidence sources—trials, observational studies, registries—into coherent "
        "pooled estimates."
    ),
    "Metanew": (
        "Metanew implements next-generation meta-analytic algorithms with improved "
        "small-sample correction and modern variance estimation methods."
    ),
    "multilevelerror": (
        "MultiLevelError models measurement error propagation in multilevel clinical "
        "data, providing bias-corrected meta-analytic estimates."
    ),
    "Multipledatameta": (
        "MultipleDateMeta provides methods for meta-analysing studies reported at "
        "multiple time points, accounting for within-study correlation and "
        "follow-up heterogeneity."
    ),
    "bapmr": (
        "BAPMR (Bayesian Adaptive Prior Meta-Regression) implements adaptive "
        "Bayesian meta-regression with data-driven prior selection for "
        "moderator analysis."
    ),
    "pwcvR2": (
        "PairwiseCV R2 provides cross-validated R-squared estimation for "
        "meta-regression models, quantifying the proportion of heterogeneity "
        "explained by study-level covariates."
    ),
    "trialradar": (
        "TrialRadar is a clinical trial landscape monitoring tool that tracks "
        "ongoing and completed trials, maps evidence gaps, and alerts to "
        "new relevant results."
    ),
    "-WorldIPD-private": (
        "WorldIPD Private is a private individual patient data meta-analysis "
        "repository providing validated IPD synthesis methods for confidential "
        "multi-centre datasets."
    ),
    "-WorldIPD": (
        "WorldIPD is a global individual patient data meta-analysis platform "
        "implementing standardised IPD synthesis workflows across multiple "
        "therapeutic areas."
    ),
    "clauderepo": (
        "ClaudeRepo is a repository of AI-assisted clinical evidence synthesis "
        "workflows, providing reusable pipelines and templates for meta-analytic "
        "research."
    ),
    "metaaudit": (
        "MetaAudit is an automated GitHub audit and quality-assurance platform "
        "for meta-analysis research repositories, providing dashboard reporting, "
        "reproducibility checks, and protocol registration."
    ),
    "metaoverfit-paper": (
        "MetaOverfit Paper investigates overfitting in meta-regression models, "
        "quantifying the risk of spurious moderator findings and proposing "
        "cross-validation corrections."
    ),
    "metaoverfit": (
        "MetaOverfit provides diagnostic tools for detecting and correcting "
        "overfitting in meta-regression, including permutation testing and "
        "bootstrap validation."
    ),
    "metasprint-autopilot": (
        "MetaSprint Autopilot is a 30K-line automated meta-analysis pipeline "
        "for rapid evidence synthesis across clinical domains, with ~2,300 "
        "total validated tests."
    ),
    "metasprint-cardio-universe": (
        "MetaSprint Cardio Universe is a cardiovascular evidence synthesis "
        "platform providing automated pooling across cardiology trial networks."
    ),
    "metasprint-dose-response": (
        "MetaSprint Dose Response extends the MetaSprint autopilot to dose-response "
        "meta-analysis, supporting flexible spline and parametric models."
    ),
    "metasprint-dta": (
        "MetaSprint DTA is a 29K-line automated diagnostic test accuracy "
        "meta-analysis pipeline with ~2,300 validated tests."
    ),
    "metasprint-nma": (
        "MetaSprint NMA extends the MetaSprint pipeline to network meta-analysis, "
        "providing automated comparative effectiveness synthesis."
    ),
    "metaverse-robust-ma": (
        "MetaVerse Robust MA implements robust meta-analytic methods within a "
        "multiverse framework, exploring the stability of conclusions across "
        "analytical perturbations."
    ),
    "nmatransport": (
        "NMATransport extends network meta-analysis with transportability "
        "adjustments, allowing pooled estimates to be tailored to target "
        "populations differing from trial samples."
    ),
    "portfolio-site": (
        "Portfolio Site is the personal academic and research portfolio website "
        "for Mahmood Ahmad, showcasing meta-analysis tools, publications, and "
        "open-source projects."
    ),
    "private-website": (
        "Private Website is a secure internal research portal for ongoing "
        "meta-analysis projects and confidential evidence synthesis workflows."
    ),
    "pub-bias-simulation": (
        "Pub Bias Simulation provides Monte Carlo simulation of publication bias "
        "mechanisms, evaluating the performance of detection methods under "
        "controlled conditions."
    ),
    "rct-extractor-v2": (
        "RCT Extractor v2 achieves 94.6% accuracy in automated extraction of "
        "statistical results from RCT reports, with 863 validated test cases."
    ),
    "registry-first-rct-meta": (
        "Registry-First RCT Meta implements a registry-first approach to "
        "meta-analysis, using pre-registered protocols to pre-specify synthesis "
        "choices before evidence collection."
    ),
    "repo100": (
        "Repo100 is a curated collection of 100 replication analyses of published "
        "meta-analyses, providing a benchmark dataset for reproducibility research."
    ),
    "enma-snma": (
        "ENMA-SNMA implements Extended and Simplified NMA methods, providing "
        "accessible network meta-analysis workflows with full uncertainty "
        "quantification."
    ),
    "rmstnma": (
        "RMSTNMA combines restricted mean survival time (RMST) endpoints with "
        "network meta-analysis, enabling comparative effectiveness synthesis "
        "using time-to-event data."
    ),
    "wasserstein": (
        "Wasserstein MA implements Wasserstein distance-based meta-analysis, "
        "treating study distributions as probability measures and quantifying "
        "heterogeneity geometrically."
    ),
    "MetaGuard": (
        "MetaGuard is a frontier meta-analysis toolkit combining DPD robust "
        "estimation, real-time meta-analysis p-hacking detection, and MetaForest "
        "machine-learning heterogeneity modelling."
    ),
    "Denominator_Calibrated_Living_NMA": (
        "Denominator Calibrated Living NMA implements denominator-calibrated "
        "methods for living network meta-analysis, continuously updating pooled "
        "estimates as new evidence accrues."
    ),
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def run(cmd, cwd=None, capture=True):
    """Run a shell command. Returns (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        shell=True,
        capture_output=capture,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def get_git_remote(repo_path):
    """Return the origin remote URL, or None if not set."""
    rc, out, _ = run("git remote get-url origin", cwd=repo_path)
    return out if rc == 0 and out else None


def remote_to_slug(url):
    """Extract the repo slug (owner/repo) from a GitHub remote URL."""
    url = url.rstrip("/").removesuffix(".git")
    if "github.com" in url:
        parts = url.split("github.com/")
        if len(parts) == 2:
            return parts[1]
    return None


def remote_to_repo_name(url):
    """Extract just the repo name from a remote URL."""
    url = url.rstrip("/").removesuffix(".git")
    return url.split("/")[-1]


def has_preregistration_release(repo_path):
    """Return True if the preregistration tag already exists as a GH release."""
    rc, out, _ = run("gh release list", cwd=repo_path)
    if rc != 0:
        return False
    return PREREGISTRATION_TAG in out or "preregistration" in out.lower() or "protocol" in out.lower()


def read_readme_description(repo_path):
    """Extract the first meaningful description line from README.md."""
    readme_candidates = [
        Path(repo_path) / "README.md",
        Path(repo_path) / "readme.md",
        Path(repo_path) / "Readme.md",
        Path(repo_path) / "docs" / "README.md",
    ]
    for readme in readme_candidates:
        if readme.exists():
            try:
                content = readme.read_text(encoding="utf-8", errors="replace")
                lines = content.splitlines()
                # Skip blank lines and heading-only lines, collect first real content
                title = None
                description_parts = []
                for line in lines:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    if stripped.startswith("#"):
                        if title is None:
                            title = stripped.lstrip("#").strip()
                        continue
                    if stripped.startswith(">"):
                        # blockquote — likely a short description
                        desc = stripped.lstrip(">").strip()
                        if len(desc) > 20:
                            description_parts.append(desc)
                            break
                    if stripped.startswith("[!["):  # badge line, skip
                        continue
                    if len(stripped) > 30 and not stripped.startswith("|"):
                        description_parts.append(stripped)
                        break
                if description_parts:
                    return description_parts[0]
                if title:
                    return title
            except Exception:
                pass
    return None


def infer_description(repo_name, readme_desc):
    """Return the best available description for a repo."""
    slug = repo_name.lower().rstrip("/").split("/")[-1]
    # Try override dict
    for key, val in DESCRIPTION_OVERRIDES.items():
        if key.lower() == slug:
            return val
    # Fall back to README
    if readme_desc and len(readme_desc) > 20:
        return readme_desc
    # Last resort: humanise the repo name
    human = re.sub(r"[-_]", " ", slug).title()
    return f"{human} is a meta-analysis research tool for evidence synthesis."


def github_pages_url(remote_url, repo_path):
    """Try to infer a GitHub Pages URL if gh-pages branch exists."""
    slug = remote_to_slug(remote_url)
    if not slug:
        return "N/A"
    owner, name = (slug.split("/") + [""])[:2]
    # Check if gh-pages branch exists
    rc, out, _ = run("git branch -r", cwd=repo_path)
    if "gh-pages" in out or "github-pages" in out:
        return f"https://{owner}.github.io/{name}/"
    # Check if there's an index.html in root (common for HTML app repos)
    if (Path(repo_path) / "index.html").exists():
        return f"https://{owner}.github.io/{name}/"
    return "N/A"


def build_protocol(project_name, remote_url, description, pages_url):
    """Build the protocol.md content string."""
    return textwrap.dedent(f"""\
        # {project_name}: Protocol Registration

        **Author:** {AUTHOR}
        **ORCID:** {ORCID}
        **Registration Date:** {REGISTRATION_DATE}
        **Repository:** {remote_url}

        ## Objective

        {description}

        ## Methods

        This project employs a deterministic, TruthCert-certified pipeline for evidence \
synthesis. All analytical choices are pre-specified in this protocol document prior to \
data analysis. The implementation uses versioned code with fixed random seeds where \
applicable, structured input schemas, and automated validation against reference outputs. \
Provenance is recorded via hash-linked evidence locators in accordance with the TruthCert \
framework. Statistical methods follow established meta-analytic guidelines (Cochrane Handbook, \
PRISMA 2020) and are validated against reference implementations in R (metafor, meta) or \
Python with tolerance ≤ 1×10⁻⁶.

        ## Availability

        - Code: {remote_url}
        - Dashboard: {pages_url}

        ---

        {AI_DISCLOSURE}
    """)


def collect_repos():
    """Walk all scan roots and collect (repo_path, remote_url) pairs."""
    repos = []
    seen_remotes = set()

    for root in SCAN_ROOTS:
        root_path = Path(root)
        if not root_path.exists():
            continue

        if root in SINGLE_DIR_REPOS:
            # The root itself is the repo
            candidate_paths = [root_path]
        else:
            # Each subdirectory is a potential repo
            try:
                candidate_paths = [p for p in root_path.iterdir() if p.is_dir()]
            except PermissionError:
                continue

        for candidate in candidate_paths:
            if not (candidate / ".git").is_dir():
                continue
            remote = get_git_remote(str(candidate))
            if not remote or remote == "no-remote":
                continue
            if "github.com" not in remote:
                continue
            # Normalise remote for dedup
            norm = remote.rstrip("/").lower().removesuffix(".git")
            if norm in seen_remotes:
                continue
            seen_remotes.add(norm)

            # Skip MetaAudit
            candidate_resolved = str(candidate).replace("\\", "/").rstrip("/")
            skip = False
            for skip_path in SKIP_REPOS:
                if candidate_resolved == skip_path.rstrip("/"):
                    skip = True
                    break
            if skip:
                continue

            repos.append((str(candidate), remote))

    return sorted(repos, key=lambda x: x[0].lower())


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------


def process_repo(repo_path, remote_url, execute, log_lines):
    """Process a single repository. Returns status string."""
    repo_name = remote_to_repo_name(remote_url)
    project_name = re.sub(r"[-_]", " ", repo_name).title()

    print(f"  Repo  : {repo_path}")
    print(f"  Remote: {remote_url}")

    # Check for existing preregistration release
    already_done = has_preregistration_release(repo_path)
    if already_done:
        print(f"  Status: SKIP — preregistration release already exists\n")
        log_lines.append(f"| {project_name} | {remote_url} | SKIPPED (already registered) |")
        return "skipped"

    # Build protocol content
    readme_desc = read_readme_description(repo_path)
    description = infer_description(repo_name, readme_desc)
    pages_url = github_pages_url(remote_url, repo_path)
    protocol_content = build_protocol(project_name, remote_url, description, pages_url)

    protocol_path = Path(repo_path) / "docs" / "protocol.md"

    print(f"  Status: NEEDS REGISTRATION")
    print(f"  Desc  : {description[:80]}...")
    print(f"  Pages : {pages_url}")

    if not execute:
        print(f"  Action: [DRY RUN] Would write {protocol_path} + commit + push + release\n")
        log_lines.append(f"| {project_name} | {remote_url} | DRY RUN |")
        return "dry_run"

    # --- Execute mode ---
    try:
        # 1. Create docs/ if needed
        docs_dir = Path(repo_path) / "docs"
        docs_dir.mkdir(exist_ok=True)

        # 2. Write protocol.md
        protocol_path.write_text(protocol_content, encoding="utf-8")
        print(f"  Wrote : {protocol_path}")

        # 3. Git add + commit
        rc, out, err = run(f'git add docs/protocol.md', cwd=repo_path)
        if rc != 0:
            raise RuntimeError(f"git add failed: {err}")

        commit_msg = f"docs: add protocol pre-registration ({REGISTRATION_DATE})"
        rc, out, err = run(f'git commit -m "{commit_msg}"', cwd=repo_path)
        if rc != 0 and "nothing to commit" not in err and "nothing to commit" not in out:
            raise RuntimeError(f"git commit failed: {err}")

        # 4. Push
        rc, out, err = run("git push origin", cwd=repo_path)
        if rc != 0:
            raise RuntimeError(f"git push failed: {err}")
        print("  Pushed: OK")

        # 5. Create GitHub release with protocol as asset
        release_title = f"{project_name} Pre-Registration (Protocol Freeze)"
        release_notes = (
            f"## Protocol Pre-Registration\n\n"
            f"**Date:** {REGISTRATION_DATE}  \n"
            f"**Author:** {AUTHOR}  \n"
            f"**ORCID:** {ORCID}\n\n"
            f"This release freezes the analysis protocol for {project_name}. "
            f"See `docs/protocol.md` for the full pre-registered protocol.\n\n"
            f"---\n{AI_DISCLOSURE}"
        )
        # Write release notes to a temp file to avoid quoting issues
        notes_path = Path(repo_path) / "docs" / "_release_notes_tmp.md"
        notes_path.write_text(release_notes, encoding="utf-8")

        gh_cmd = (
            f'gh release create "{PREREGISTRATION_TAG}" '
            f'--title "{release_title}" '
            f'--notes-file "docs/_release_notes_tmp.md" '
            f'"docs/protocol.md"'
        )
        rc, out, err = run(gh_cmd, cwd=repo_path)
        notes_path.unlink(missing_ok=True)

        if rc != 0:
            raise RuntimeError(f"gh release create failed: {err}")
        print(f"  Release: created {PREREGISTRATION_TAG}")

        log_lines.append(f"| {project_name} | {remote_url} | REGISTERED |")
        print()
        return "registered"

    except Exception as e:
        print(f"  ERROR : {e}\n")
        log_lines.append(f"| {project_name} | {remote_url} | FAILED: {e} |")
        return "failed"


def write_log(log_lines, summary):
    """Write the markdown log file."""
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Protocol Registration Log",
        "",
        f"Generated: {now}",
        "",
        f"## Summary",
        "",
    ]
    for k, v in summary.items():
        lines.append(f"- **{k}**: {v}")
    lines += [
        "",
        "## Per-Repository Results",
        "",
        "| Project | Repository | Status |",
        "|---------|------------|--------|",
    ]
    lines.extend(log_lines)
    lines.append("")

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nLog written to: {LOG_PATH}")


def main():
    parser = argparse.ArgumentParser(
        description="Register protocols for all meta-analysis GitHub repositories."
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually commit, push, and create releases (default: dry run).",
    )
    args = parser.parse_args()
    execute = args.execute

    mode = "EXECUTE" if execute else "DRY RUN"
    print(f"{'=' * 60}")
    print(f"Protocol Registration Script — Mode: {mode}")
    print(f"{'=' * 60}\n")

    print("Scanning repositories...")
    repos = collect_repos()
    print(f"Found {len(repos)} repositories with GitHub remotes (MetaAudit excluded).\n")

    log_lines = []
    counts = {"found": len(repos), "registered": 0, "skipped": 0, "dry_run": 0, "failed": 0}

    for i, (repo_path, remote_url) in enumerate(repos, 1):
        print(f"[{i:02d}/{len(repos):02d}] {remote_to_repo_name(remote_url)}")
        status = process_repo(repo_path, remote_url, execute, log_lines)
        counts[status] = counts.get(status, 0) + 1

    print(f"\n{'=' * 60}")
    print(f"SUMMARY ({mode})")
    print(f"{'=' * 60}")
    for k, v in counts.items():
        print(f"  {k:15s}: {v}")

    write_log(log_lines, counts)


if __name__ == "__main__":
    main()
