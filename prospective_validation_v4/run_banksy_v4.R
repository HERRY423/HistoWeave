#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 5L) {
  stop("usage: run_banksy_v4.R <input.h5ad> <output.csv> <seed> <q> <r_lib>")
}
in_h5 <- args[[1]]
out_csv <- args[[2]]
seed <- as.integer(args[[3]])
q <- as.integer(args[[4]])
r_lib <- args[[5]]
.libPaths(c(r_lib, .libPaths()))

suppressPackageStartupMessages({
  library(Banksy)
  library(SpatialExperiment)
  library(zellkonverter)
})

sce <- zellkonverter::readH5AD(in_h5, X_name = "X", reader = "R")
counts <- assay(sce, 1)
stored <- if (inherits(counts, "sparseMatrix")) counts@x else as.vector(counts)
if (length(stored) > 0L && any(abs(stored - round(stored)) > 1e-6)) {
  stop("BANKSY requires integer-like raw counts")
}
coordinates <- reducedDim(sce, "spatial")
if (is.null(coordinates)) {
  coordinates <- attr(sce, "obsm")[["spatial"]]
}
if (is.null(coordinates) && all(c("array_row", "array_col") %in% colnames(colData(sce)))) {
  coordinates <- as.matrix(colData(sce)[, c("array_row", "array_col")])
}
if (is.null(coordinates) || ncol(coordinates) != 2L) {
  stop("BANKSY input is missing two-dimensional spatial coordinates")
}
rownames(coordinates) <- colnames(sce)
spe <- SpatialExperiment(
  assays = list(counts = counts),
  spatialCoords = coordinates
)
spe <- scuttle::computeLibraryFactors(spe)
spe <- scuttle::logNormCounts(spe)
spe <- Banksy::computeBanksy(
  spe, assay_name = "logcounts", compute_agf = FALSE,
  k_geom = min(15L, ncol(spe) - 1L)
)
spe <- Banksy::runBanksyPCA(
  spe, assay_name = "logcounts", use_agf = FALSE, lambda = 0.2,
  npcs = min(15L, nrow(spe) - 1L, ncol(spe) - 1L)
)
spe <- Banksy::clusterBanksy(
  spe, assay_name = "logcounts", use_agf = FALSE, lambda = 0.2,
  algo = "kmeans", npcs = min(15L, nrow(spe) - 1L, ncol(spe) - 1L),
  k_neighbors = min(50L, ncol(spe) - 1L),
  kmeans.centers = q, seed = seed
)
cluster_names <- Banksy::clusterNames(spe)
if (length(cluster_names) == 0L) {
  stop("BANKSY did not produce a cluster-label column")
}
write.csv(
  data.frame(
    spot_id = colnames(spe),
    label = as.character(SummarizedExperiment::colData(spe)[[tail(cluster_names, 1L)]])
  ),
  out_csv, row.names = FALSE, quote = FALSE
)
