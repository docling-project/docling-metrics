#include "multi_label_confusion_matrix.h"

#include <algorithm>
#include <cassert>
#include <cmath>
#include <iostream>
#include <numeric>
#include <stdexcept>

// Use the compiler built-in popcount (maps to a single POPCNT instruction on
// x86-64 with -mpopcnt / -march=native, or is emulated otherwise).
#if defined(_MSC_VER)
#include <intrin.h>
#define POPCNT64(x) static_cast<int>(__popcnt64(x))
#else
#define POPCNT64(x) __builtin_popcountll(static_cast<unsigned long long>(x))
#endif

namespace docling {

// ─────────────────────────────────────────────────────────────────────────────
// Free helpers
// ─────────────────────────────────────────────────────────────────────────────

std::vector<int> unpackbits(const std::vector<uint64_t> &x, int num_bits) {
  const std::size_t N = x.size();
  std::vector<int> result(N * static_cast<std::size_t>(num_bits));

  for (std::size_t i = 0; i < N; ++i) {
    const uint64_t v = x[i];
    for (int b = 0; b < num_bits; ++b) {
      result[i * num_bits + b] = static_cast<int>((v >> b) & 1ULL);
    }
  }
  return result;
}

CompressedPairs compress_binary_representations(const std::vector<uint64_t> &gt,
                                                const std::vector<uint64_t> &preds) {
  assert(gt.size() == preds.size());
  const std::size_t N = gt.size();

  // Build and sort (gt, preds) pairs for deduplication.
  std::vector<std::pair<uint64_t, uint64_t>> pairs(N);
  for (std::size_t i = 0; i < N; ++i) {
    pairs[i] = {gt[i], preds[i]};
  }
  std::sort(pairs.begin(), pairs.end());

  // Linear scan: collect unique pairs and their counts.
  CompressedPairs result;
  std::size_t i = 0;
  while (i < N) {
    const auto cur = pairs[i];
    int64_t cnt = 0;
    while (i < N && pairs[i] == cur) {
      ++cnt;
      ++i;
    }
    result.gt.push_back(cur.first);
    result.preds.push_back(cur.second);
    result.counts.push_back(cnt);
  }
  return result;
}

// ─────────────────────────────────────────────────────────────────────────────
// MultiLabelConfusionMatrix – constructor
// ─────────────────────────────────────────────────────────────────────────────

MultiLabelConfusionMatrix::MultiLabelConfusionMatrix(ValidationMode mode) : _mode(mode) {}

// ─────────────────────────────────────────────────────────────────────────────
// make_binary_representation
// ─────────────────────────────────────────────────────────────────────────────

std::vector<uint64_t> MultiLabelConfusionMatrix::make_binary_representation(
    int image_width, int image_height, const std::vector<BboxResolution> &resolutions,
    bool set_background) const {
  std::vector<uint64_t> matrix(
      static_cast<std::size_t>(image_height) * static_cast<std::size_t>(image_width), 0ULL);

  for (const auto &res : resolutions) {
    // Mirror Python: math.floor(x1), math.ceil(x2), etc.
    int x_begin = static_cast<int>(std::floor(res.bbox[0]));
    int y_begin = static_cast<int>(std::floor(res.bbox[1]));
    int x_end = static_cast<int>(std::ceil(res.bbox[2]));
    int y_end = static_cast<int>(std::ceil(res.bbox[3]));

    // Clamp to image bounds (numpy slicing silently handles OOB).
    x_begin = std::max(0, x_begin);
    y_begin = std::max(0, y_begin);
    x_end = std::min(image_width, x_end);
    y_end = std::min(image_height, y_end);

    const uint64_t bit_index = 1ULL << res.category_id;

    for (int y = y_begin; y < y_end; ++y) {
      for (int x = x_begin; x < x_end; ++x) {
        matrix[static_cast<std::size_t>(y) * image_width + x] |= bit_index;
      }
    }
  }

  // Assign background (bit 0 = class 0 = 1) to pixels with no class.
  if (set_background) {
    for (uint64_t &pixel : matrix) {
      if (pixel == 0ULL)
        pixel = 1ULL;
    }
  }

  return matrix;
}

// ─────────────────────────────────────────────────────────────────────────────
// generate_confusion_matrix
// ─────────────────────────────────────────────────────────────────────────────

std::vector<double>
MultiLabelConfusionMatrix::generate_confusion_matrix(const std::vector<uint64_t> &gt,
                                                     const std::vector<uint64_t> &preds,
                                                     const std::vector<int> &categories) const {
  auto [comp_gt, comp_preds, counts] = compress_binary_representations(gt, preds);
  return _compute_confusion_matrix(comp_gt, comp_preds, categories, &counts);
}

// ─────────────────────────────────────────────────────────────────────────────
// _compute_confusion_matrix
//
// Ports the four-case algorithm from the Python implementation.
// For each unique (g, p, weight) triple we dispatch to exactly one case and
// accumulate directly into the flat [C × C] confusion matrix WITHOUT
// materialising the intermediate [k, C, C] contributions tensor.
//
// The four mutually exclusive cases are:
//
//   Case 1  g == p                       – perfect prediction
//   Case 2  (g & p) == g,  g != p        – preds ⊃ gt (extra false positives)
//   Case 3  (g | p) == g,  g != p        – gt ⊃ preds (missed classes)
//   Case 4  otherwise                    – symmetric difference on both sides
//
// Mathematical derivation of each case is documented inline.
// ─────────────────────────────────────────────────────────────────────────────

std::vector<double> MultiLabelConfusionMatrix::_compute_confusion_matrix(
    const std::vector<uint64_t> &gt, const std::vector<uint64_t> &preds,
    const std::vector<int> &categories, const std::vector<int64_t> *weights) const {
  const int C = static_cast<int>(categories.size());
  const std::size_t N = gt.size();
  std::vector<double> cm(static_cast<std::size_t>(C * C), 0.0);

  for (std::size_t idx = 0; idx < N; ++idx) {
    const uint64_t g = gt[idx];
    const uint64_t p = preds[idx];
    const double w = weights ? static_cast<double>((*weights)[idx]) : 1.0;

    // ── Case 1: perfect prediction (g == p) ──────────────────────────────
    //
    // Python:
    //   contributions[pixel, i, j] = gt_bits[j] * eye[i,j]
    //                              = gt_bits[i]  if i == j, else 0
    //
    // → For each set bit b in g:  cm[b, b] += weight
    //
    if (g == p) {
      for (int b = 0; b < C; ++b) {
        if ((g >> b) & 1ULL) {
          cm[b * C + b] += w;
        }
      }
    }

    // ── Case 2: preds is a strict superset of gt  (gt ⊂ preds) ──────────
    //
    // Python:
    //   intersection = g & p  (== g in this case)
    //   diff         = (p ^ g) & p  (bits in preds only)
    //
    //   penalty[i, j] = intersection_bits[i] * diff_bits[j]
    //                  = gt_bits[i] * diff_bits[j]            (since intersect == g)
    //   gain[i, i]    = popcount(g) * gt_bits[i]              (diagonal only)
    //
    //   contributions[i, j] = (penalty[i, j] + gain[i, j]) / popcount(p)
    //
    // → For each bit i in g:
    //     cm[i, i] += w * popcount(g) / popcount(p)           (gain)
    //     for each bit j in diff:
    //       cm[i, j] += w / popcount(p)                       (penalty, always i≠j)
    //
    else if ((g & p) == g) {
      const uint64_t diff = p & ~g;
      const double denom = static_cast<double>(POPCNT64(p));
      const double gt_count = static_cast<double>(POPCNT64(g));

      for (int i = 0; i < C; ++i) {
        if (!((g >> i) & 1ULL))
          continue;                            // only iterate over gt bits
        cm[i * C + i] += w * gt_count / denom; // gain (diagonal)
        for (int j = 0; j < C; ++j) {
          if ((diff >> j) & 1ULL) {
            cm[i * C + j] += w / denom; // penalty (off-diagonal)
          }
        }
      }
    }

    // ── Case 3: gt is a strict superset of preds  (preds ⊂ gt) ──────────
    //
    // Python:
    //   gt_diff = (p ^ g) & g  (bits in gt only)
    //
    //   preds_diagonals[i, i] = preds_bits[i]                 (diagonal term)
    //   penalty[i, j]         = gt_diff_bits[i] * preds_bits[j] / popcount(p)
    //
    //   contributions[i, j] = penalty[i, j] + preds_diagonals[i, j]
    //
    // → For each bit j in p:  cm[j, j] += w                  (diagonal)
    //   For each bit i in gt_diff, each bit j in p:
    //     cm[i, j] += w / popcount(p)                        (penalty, always i≠j)
    //
    else if ((g | p) == g) {
      const uint64_t gt_diff = g & ~p;
      const double denom = static_cast<double>(POPCNT64(p));

      for (int j = 0; j < C; ++j) {
        if ((p >> j) & 1ULL) {
          cm[j * C + j] += w; // diagonal (preds bits)
        }
      }
      for (int i = 0; i < C; ++i) {
        if (!((gt_diff >> i) & 1ULL))
          continue;
        for (int j = 0; j < C; ++j) {
          if ((p >> j) & 1ULL) {
            cm[i * C + j] += w / denom; // penalty (always i≠j)
          }
        }
      }
    }

    // ── Case 4: symmetric difference on both sides ────────────────────────
    //
    // Python:
    //   gt_diff    = (p ^ g) & g  (bits in gt only)
    //   preds_diff = (p ^ g) & p  (bits in preds only)
    //   isect      = g & p        (bits in both)
    //   denom      = popcount(preds_diff)    ← NOTE: NOT popcount(p)
    //
    //   intersection_diagonals[k, k] = isect_bits[k]          (diagonal term)
    //   penalty[i, j] = gt_diff_bits[i] * preds_diff_bits[j] / denom
    //
    //   contributions[i, j] = penalty[i, j] + intersection_diagonals[i, j]
    //
    // → For each bit k in isect: cm[k, k] += w               (diagonal)
    //   For each bit i in gt_diff, each bit j in preds_diff:
    //     cm[i, j] += w / denom                               (penalty)
    //
    else {
      const uint64_t gt_diff = g & ~p;
      const uint64_t preds_diff = p & ~g;
      const uint64_t isect = g & p;
      const double denom = static_cast<double>(POPCNT64(preds_diff));

      for (int k = 0; k < C; ++k) {
        if ((isect >> k) & 1ULL) {
          cm[k * C + k] += w; // diagonal (intersection)
        }
      }
      for (int i = 0; i < C; ++i) {
        if (!((gt_diff >> i) & 1ULL))
          continue;
        for (int j = 0; j < C; ++j) {
          if ((preds_diff >> j) & 1ULL) {
            cm[i * C + j] += w / denom; // penalty
          }
        }
      }
    }
  }

  return cm;
}

// ─────────────────────────────────────────────────────────────────────────────
// _compute_matrix_metrics
// ─────────────────────────────────────────────────────────────────────────────

MultiLabelMatrixMetrics MultiLabelConfusionMatrix::_compute_matrix_metrics(
    const std::vector<double> &cm, int C, const std::map<int, std::string> &class_names) const {
  // Column sums (used for precision) and row sums (used for recall).
  std::vector<double> col_sums(C, 0.0);
  std::vector<double> row_sums(C, 0.0);
  for (int i = 0; i < C; ++i) {
    for (int j = 0; j < C; ++j) {
      row_sums[i] += cm[i * C + j];
      col_sums[j] += cm[i * C + j];
    }
  }

  std::vector<double> prec_mat(C * C, 0.0);
  std::vector<double> rec_mat(C * C, 0.0);
  std::vector<double> f1_mat(C * C, 0.0);

  for (int i = 0; i < C; ++i) {
    for (int j = 0; j < C; ++j) {
      const double v = cm[i * C + j];
      if (col_sums[j] != 0.0)
        prec_mat[i * C + j] = v / col_sums[j];
      if (row_sums[i] != 0.0)
        rec_mat[i * C + j] = v / row_sums[i];
    }
  }

  for (int i = 0; i < C; ++i) {
    for (int j = 0; j < C; ++j) {
      const double p = prec_mat[i * C + j];
      const double r = rec_mat[i * C + j];
      const double denom = p + r;
      if (denom != 0.0)
        f1_mat[i * C + j] = 2.0 * p * r / denom;
    }
  }

  // Diagonal gives per-class scalars.
  MultiLabelMatrixAggMetrics agg;
  double p_sum = 0.0, r_sum = 0.0, f1_sum = 0.0;
  for (int k = 0; k < C; ++k) {
    auto it = class_names.find(k);
    const std::string name = (it != class_names.end()) ? it->second : std::to_string(k);

    const double p = prec_mat[k * C + k];
    const double r = rec_mat[k * C + k];
    const double f1 = f1_mat[k * C + k];
    agg.classes_precision[name] = p;
    agg.classes_recall[name] = r;
    agg.classes_f1[name] = f1;
    p_sum += p;
    r_sum += r;
    f1_sum += f1;
  }
  if (C > 0) {
    agg.classes_precision_mean = p_sum / C;
    agg.classes_recall_mean = r_sum / C;
    agg.classes_f1_mean = f1_sum / C;
  }

  MultiLabelMatrixMetrics result;
  result.class_names = class_names;
  result.num_categories = C;
  result.confusion_matrix = cm;
  result.precision_matrix = std::move(prec_mat);
  result.recall_matrix = std::move(rec_mat);
  result.f1_matrix = std::move(f1_mat);
  result.agg_metrics = std::move(agg);
  return result;
}

// ─────────────────────────────────────────────────────────────────────────────
// compute_metrics
// ─────────────────────────────────────────────────────────────────────────────

MultiLabelMatrixEvaluation
MultiLabelConfusionMatrix::compute_metrics(const std::vector<double> &cm, int C,
                                           const std::map<int, std::string> &class_names) const {
  auto detailed = _compute_matrix_metrics(cm, C, class_names);

  // Collapsed 2×2 matrix: background (class 0) vs. all other classes.
  //
  // Python:
  //   collapsed[0, 0] = cm[0, 0]
  //   collapsed[0, 1] = sum(cm[0, 1:])
  //   collapsed[1, 0] = sum(cm[1:, 0])
  //   collapsed[1, 1] = sum(cm[1:, 1:])
  //
  std::vector<double> ccm(4, 0.0);
  ccm[0 * 2 + 0] = cm[0 * C + 0];
  for (int j = 1; j < C; ++j)
    ccm[0 * 2 + 1] += cm[0 * C + j];
  for (int i = 1; i < C; ++i)
    ccm[1 * 2 + 0] += cm[i * C + 0];
  for (int i = 1; i < C; ++i)
    for (int j = 1; j < C; ++j)
      ccm[1 * 2 + 1] += cm[i * C + j];

  std::map<int, std::string> cn2;
  cn2[0] = class_names.at(0);
  cn2[1] = ALL_COLLAPSED_CLASSES_NAME;

  auto collapsed = _compute_matrix_metrics(ccm, 2, cn2);

  return {std::move(detailed), std::move(collapsed)};
}

// ─────────────────────────────────────────────────────────────────────────────
// validate_contributions
// ─────────────────────────────────────────────────────────────────────────────

void MultiLabelConfusionMatrix::validate_contributions(const std::vector<uint64_t> &selected_gt,
                                                       const std::vector<double> &contributions,
                                                       int C, const std::string &info) const {
  if (_mode == ValidationMode::Disabled)
    return;

  const std::size_t k = selected_gt.size();
  if (contributions.size() != k * static_cast<std::size_t>(C * C)) {
    _handle_error(info + ": Wrong contributions dimension");
    return;
  }

  // Property 1: For each pixel and each row i where gt bit i is set,
  // the row sum must equal 1.  Rows for bits not set in gt must sum to 0.
  for (std::size_t pixel = 0; pixel < k; ++pixel) {
    const uint64_t g = selected_gt[pixel];
    for (int i = 0; i < C; ++i) {
      const int expected = static_cast<int>((g >> i) & 1ULL);
      double row_sum = 0.0;
      for (int j = 0; j < C; ++j) {
        row_sum += contributions[pixel * C * C + i * C + j];
      }
      if (std::abs(row_sum - expected) > 1e-9) {
        _handle_error(info + ": Wrong contributions row sums");
        return;
      }
    }
  }

  // Property 2: The full tensor sum must equal the sum of popcount(gt)
  // across all selected pixels.
  double full_sum = 0.0;
  int64_t expected_full = 0;
  for (double v : contributions)
    full_sum += v;
  for (uint64_t g : selected_gt)
    expected_full += POPCNT64(g);

  if (std::abs(full_sum - static_cast<double>(expected_full)) > 1e-9) {
    _handle_error(info + ": Wrong contributions full sums");
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// _handle_error
// ─────────────────────────────────────────────────────────────────────────────

void MultiLabelConfusionMatrix::_handle_error(const std::string &msg) const {
  if (_mode == ValidationMode::Raise) {
    throw std::runtime_error(msg);
  } else {
    std::cerr << "[MultiLabelConfusionMatrix] ERROR: " << msg << '\n';
  }
}

} // namespace docling
