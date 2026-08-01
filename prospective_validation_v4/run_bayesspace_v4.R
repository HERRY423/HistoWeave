#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 5L) {
  stop("usage: run_bayesspace_v4.R <input.h5ad> <output.csv> <seed> <q> <r_lib>")
}
in_h5 <- args[[1]]
out_csv <- args[[2]]
seed <- as.integer(args[[3]])
q <- as.integer(args[[4]])
r_lib <- args[[5]]
.libPaths(c(r_lib, .libPaths()))

suppressPackageStartupMessages({
  library(BayesSpace)
  library(SingleCellExperiment)
  library(zellkonverter)
})

sce <- zellkonverter::readH5AD(in_h5, X_name = "X", reader = "R")
if (!"counts" %in% assayNames(sce)) {
  assay(sce, "counts") <- assay(sce, 1)
}
required <- c("array_row", "array_col")
if (!all(required %in% colnames(colData(sce)))) {
  stop("input h5ad is missing array_row/array_col")
}
n_pcs <- min(15L, q + 3L, nrow(sce) - 1L, ncol(sce) - 1L)
set.seed(seed)
sce <- spatialPreprocess(
  sce, platform = "Visium", n.PCs = n_pcs,
  n.HVGs = min(2000L, nrow(sce)), log.normalize = TRUE
)
sce <- spatialCluster(
  sce, q = q, platform = "Visium", d = n_pcs,
  init.method = "mclust", model = "t", gamma = 2,
  nrep = 10000L, burn.in = 1000L, save.chain = FALSE
)
write.csv(
  data.frame(
    spot_id = colnames(sce),
    label = as.integer(colData(sce)$spatial.cluster)
  ),
  out_csv, row.names = FALSE, quote = FALSE
)
