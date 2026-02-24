#pragma once

#include <array>
#include <cstdint>
#include <map>
#include <string>
#include <vector>

namespace docling {

// ─── Data structures ─────────────────────────────────────────────────────────

/// Bounding-box annotation for a single layout element.
/// bbox layout: (x1, y1, x2, y2) with origin at the top-left corner;
/// coordinates are in pixels and are NOT normalised.
struct BboxResolution {
  int category_id;
  std::array<double, 4> bbox; ///< (x1, y1, x2, y2)
  double score = 0.0;
};

/// Per-class and aggregate precision / recall / F1 scalars derived from a
/// confusion matrix.
struct MultiLabelMatrixAggMetrics {
  std::map<std::string, double> classes_precision;
  std::map<std::string, double> classes_recall;
  std::map<std::string, double> classes_f1;

  double classes_precision_mean = 0.0;
  double classes_recall_mean = 0.0;
  double classes_f1_mean = 0.0;
};

/// Full set of matrices and aggregated metrics computed from a confusion matrix.
/// All matrix fields are flat row-major arrays of shape [num_categories × num_categories].
struct MultiLabelMatrixMetrics {
  std::map<int, std::string> class_names;
  int num_categories = 0;

  std::vector<double> confusion_matrix; ///< Raw confusion counts / weights
  std::vector<double> precision_matrix; ///< Precision per (row, col) pair
  std::vector<double> recall_matrix;    ///< Recall per (row, col) pair
  std::vector<double> f1_matrix;        ///< F1 per (row, col) pair

  MultiLabelMatrixAggMetrics agg_metrics;
};

/// Paired evaluation: one for all classes, one with non-background classes
/// collapsed into a single "all_classes" bucket.
struct MultiLabelMatrixEvaluation {
  MultiLabelMatrixMetrics detailed;  ///< Every class kept distinct
  MultiLabelMatrixMetrics collapsed; ///< Background vs. everything else
};

// ─── Free helpers ────────────────────────────────────────────────────────────

/// Unpack the @p num_bits lowest-order bits of each element in @p x.
///
/// Returns a flat row-major array of shape [x.size(), num_bits].
/// Bit 0 maps to column 0, bit 1 to column 1, etc.
///
/// Mirrors the Python helper of the same name used throughout the algorithm.
std::vector<int> unpackbits(const std::vector<uint64_t> &x, int num_bits);

/// Result type for compress_binary_representations().
struct CompressedPairs {
  std::vector<uint64_t> gt;    ///< Unique GT bit-pattern values
  std::vector<uint64_t> preds; ///< Corresponding prediction bit-patterns
  std::vector<int64_t> counts; ///< Number of pixels with this (gt, pred) pair
};

/// Find every unique (gt[i], preds[i]) pair across all pixel positions and
/// return each unique pair together with the count of how many pixels share it.
///
/// This is the C++ equivalent of the Python compress_binary_representations()
/// which uses np.unique on a structured array.
CompressedPairs compress_binary_representations(const std::vector<uint64_t> &gt,
                                                const std::vector<uint64_t> &preds);

// ─── MultiLabelConfusionMatrix ───────────────────────────────────────────────

enum class ValidationMode { Disabled, Log, Raise };

/// C++ port of the Python MultiLabelConfusionMatrix class.
///
/// All pixel arrays (gt, preds) are flat row-major vectors of uint64 values
/// where bit k is 1 iff the pixel belongs to class k.
///
/// Algorithm reference:
///   "Multi-label classifier performance evaluation with confusion matrix"
///   https://csitcp.org/paper/10/108csit01.pdf
class MultiLabelConfusionMatrix {
public:
  static constexpr const char *ALL_COLLAPSED_CLASSES_NAME = "all_classes";

  explicit MultiLabelConfusionMatrix(ValidationMode mode = ValidationMode::Disabled);

  // ── Core pipeline ──────────────────────────────────────────────────────

  /// Rasterise @p resolutions into a flat row-major pixel matrix of shape
  /// [image_height × image_width].  Each pixel value is a uint64 bit-mask
  /// where bit k is 1 iff the pixel is covered by a bbox with category_id k.
  ///
  /// When @p set_background is true, pixels with no class assigned are set
  /// to 1 (bit 0 = background class).
  std::vector<uint64_t> make_binary_representation(int image_width, int image_height,
                                                   const std::vector<BboxResolution> &resolutions,
                                                   bool set_background = true) const;

  /// Compute the multi-label confusion matrix from two flat pixel arrays of
  /// the same length and a list of valid category ids.
  ///
  /// Internally compresses duplicate (gt, pred) pairs for efficiency, then
  /// runs _compute_confusion_matrix() with the pixel counts as weights.
  ///
  /// Returns a flat row-major [C × C] double array where C = categories.size().
  std::vector<double> generate_confusion_matrix(const std::vector<uint64_t> &gt,
                                                const std::vector<uint64_t> &preds,
                                                const std::vector<int> &categories) const;

  /// Compute per-class precision / recall / F1 from a confusion matrix, and
  /// produce an additional collapsed 2×2 view (background vs. rest).
  MultiLabelMatrixEvaluation compute_metrics(const std::vector<double> &confusion_matrix,
                                             int num_categories,
                                             const std::map<int, std::string> &class_names) const;

  // ── Validation (optional debugging aid) ────────────────────────────────

  /// Check the mathematical invariants of a per-pixel contributions tensor:
  ///   1. For every row i where gt bit i is set: sum of that row equals 1.
  ///   2. Total tensor sum equals sum of popcount(gt) over all pixels.
  ///
  /// @p contributions is a flat row-major array of shape [k, C, C] where
  /// k = selected_gt.size() and C = num_categories.
  ///
  /// In Disabled mode this is a no-op.  In Log mode a message is written to
  /// std::cerr.  In Raise mode a std::runtime_error is thrown.
  void validate_contributions(const std::vector<uint64_t> &selected_gt,
                              const std::vector<double> &contributions, int num_categories,
                              const std::string &info) const;

private:
  ValidationMode _mode;

  /// Core accumulation: iterate over each unique (g, p, weight) triple and
  /// dispatch to one of four cases, accumulating directly into the [C×C]
  /// confusion matrix without materialising any intermediate 3-D tensor.
  std::vector<double>
  _compute_confusion_matrix(const std::vector<uint64_t> &gt, const std::vector<uint64_t> &preds,
                            const std::vector<int> &categories,
                            const std::vector<int64_t> *weights = nullptr) const;

  /// Derive precision_matrix, recall_matrix, f1_matrix and their diagonal
  /// summaries from a raw confusion matrix.
  MultiLabelMatrixMetrics
  _compute_matrix_metrics(const std::vector<double> &confusion_matrix, int num_categories,
                          const std::map<int, std::string> &class_names) const;

  void _handle_error(const std::string &msg) const;
};

} // namespace docling
