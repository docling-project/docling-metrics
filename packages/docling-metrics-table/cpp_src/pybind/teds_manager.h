#pragma once
#include <algorithm>
#include <iostream>
#include <memory>
#include <new>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_map>

#include "apted_tree_index.h"
#include "bracket_notation_parser.h"
#include "node.h"
#include "string_label.h"
#include "unit_cost_model.h"

namespace docling {

using Label = label::StringLabel;
using CostModelLD = cost_model::UnitCostModelLD<Label>;
using LabelDictionary = label::LabelDictionary<Label>;

/**
 * Error codes reported through the error_id field of both result structs below.
 *
 *   0  Success
 *   1  Malformed bracket notation, input A
 *   2  Malformed bracket notation, input B
 *   3  Computation failed - any std::exception outside the parse step
 *   4  Out of memory - std::bad_alloc
 *   5  Unknown failure - a non-std::exception type, caught by catch (...)
 *
 * A non-zero error_id always comes with a human-readable error_msg, and the score fields are
 * left at their constructor defaults.
 */

struct TEDSSampleEvaluation {
  TEDSSampleEvaluation() : TEDSSampleEvaluation("") {}

  TEDSSampleEvaluation(const std::string &sid)
      : error_id(0), error_msg(""), id(sid), tree_a_size(0), tree_b_size(0), teds(-1.) {}

  int error_id;
  std::string error_msg;
  std::string id;
  int tree_a_size;
  int tree_b_size;
  double teds;
};

struct TEDSDatasetEvaluation {
  TEDSDatasetEvaluation() : TEDSDatasetEvaluation("") {}

  TEDSDatasetEvaluation(const std::string &sid) : error_id(0), error_msg(""), teds(-1.) {}

  int error_id;
  std::string error_msg;
  double teds;
  std::unordered_map<std::string, TEDSSampleEvaluation> sample_evaluations;
};

/**
 * Computes TEDS and reports every failure it can observe through error_id / error_msg, so that
 * the evaluation logic never throws into the Python bindings.
 *
 * Three paths sit outside that guarantee, because they are outside the method bodies this class
 * controls. Reaching them would mean rewriting the bindings in pybind_module.cpp:
 *
 *  - Argument conversion, before any method body runs. A non-str argument, or a str holding lone
 *    surrogates, fails in pybind11's caster -> Python TypeError.
 *  - The constructor below, whose make_unique calls can throw std::bad_alloc -> Python
 *    MemoryError. A constructor has no result object to report with.
 *  - The binding boundary after a method returns. The def_readwrite setters on the result structs
 *    raise TypeError on a wrong-typed assignment, and the sample_evaluations accessor converts an
 *    unordered_map to a Python dict, which can throw once this class has already returned.
 */
class TEDSManager {
public:
  TEDSManager()
      : ucm_ptr_(std::make_unique<CostModelLD>(ld_)),
        apted_ptr_(
            std::make_unique<ted::APTEDTreeIndex<CostModelLD, node::TreeIndexAPTED>>(*ucm_ptr_)) {}

  /**
   * Evaluate a single sample in html format
   */
  TEDSSampleEvaluation evaluate_html_sample(const std::string &id, const std::string &html_a,
                                            const std::string &html_b, bool structure_only) {
    TEDSSampleEvaluation eval_sample(id);

    // Only the conversion needs a guard here - the delegated evaluate_sample call carries its own.
    std::string bracket_a;
    std::string bracket_b;
    try {
      // Convert the html to bracket format
      bracket_a = html_to_bracket(html_a, structure_only);
      bracket_b = html_to_bracket(html_b, structure_only);
    } catch (const std::bad_alloc &) {
      set_error(eval_sample, 4, "Out of memory");
      return eval_sample;
    } catch (const std::exception &e) {
      set_error(eval_sample, 3, std::string("HTML conversion failed: ") + e.what());
      return eval_sample;
    } catch (...) {
      set_error(eval_sample, 5, "Unknown error");
      return eval_sample;
    }

    return evaluate_sample(id, bracket_a, bracket_b);
  }

  /**
   * Evaluate a single sample
   */
  TEDSSampleEvaluation evaluate_sample(const std::string &id, const std::string &bracket_a,
                                       const std::string &bracket_b) {
    // Return object with full information: teds, tree sizes, ...
    // Constructed outside the guard: it is the only thing a failed evaluation can report with.
    TEDSSampleEvaluation eval_sample(id);

    try {
      // Parse the inputs. Each failure becomes an error_id.
      std::optional<node::Node<Label>> tree_a;
      std::optional<node::Node<Label>> tree_b;

      // parse_single throws std::invalid_argument for malformed input, and nothing else
      // deliberately. Catching that type rather than std::exception keeps an allocation failure
      // from being mislabelled a format error - it falls through to the std::bad_alloc handler.
      try {
        tree_a = bnp_.parse_single(bracket_a);
      } catch (const std::invalid_argument &e) {
        set_error(eval_sample, 1, std::string("Incorrect format of input A: ") + e.what());
        return eval_sample;
      }

      try {
        tree_b = bnp_.parse_single(bracket_b);
      } catch (const std::invalid_argument &e) {
        set_error(eval_sample, 2, std::string("Incorrect format of input B: ") + e.what());
        return eval_sample;
      }

      // Compute ted
      int tree_a_size = tree_a->get_tree_size();
      int tree_b_size = tree_b->get_tree_size();
      int max_tree_size = std::max(tree_a_size, tree_b_size);

      // The validator guarantees at least one node, so this cannot trigger today. It is here so
      // that the divisor below can never turn a broken tree into a silent inf/nan score.
      if (max_tree_size <= 0) {
        set_error(eval_sample, 3, "Empty tree");
        return eval_sample;
      }

      node::TreeIndexAPTED ti1;
      node::TreeIndexAPTED ti2;
      node::index_tree(ti1, *tree_a, ld_, *ucm_ptr_);
      node::index_tree(ti2, *tree_b, ld_, *ucm_ptr_);
      double distance = apted_ptr_->ted(ti1, ti2);
      double teds = 1. - (distance / max_tree_size);

      eval_sample.tree_a_size = tree_a_size;
      eval_sample.tree_b_size = tree_b_size;
      eval_sample.teds = teds;
    } catch (const std::bad_alloc &) {
      // Short literal on purpose: it fits the small-string optimisation, so reporting an
      // out-of-memory condition does not itself need to allocate.
      set_error(eval_sample, 4, "Out of memory");
    } catch (const std::exception &e) {
      // Concatenating e.what() does allocate, so a nested bad_alloc here would still escape.
      set_error(eval_sample, 3, std::string("TEDS computation failed: ") + e.what());
    } catch (...) {
      set_error(eval_sample, 5, "Unknown error");
    }

    return eval_sample;
  }

  void aggregate() {
    try {
      // TODO: Add implementation
    } catch (...) {
    }
  }

  TEDSDatasetEvaluation evaluate_dataset() {
    TEDSDatasetEvaluation eval_dataset;

    try {
      // TODO: Add implementation
    } catch (const std::bad_alloc &) {
      set_error(eval_dataset, 4, "Out of memory");
    } catch (const std::exception &e) {
      set_error(eval_dataset, 3, std::string("Dataset evaluation failed: ") + e.what());
    } catch (...) {
      set_error(eval_dataset, 5, "Unknown error");
    }

    return eval_dataset;
  }

private:
  std::string html_to_bracket(const std::string &html, bool structure_only) {
    // TODO: Add implementation
    return "";
  }

  /**
   * Record a failure and reset the score fields to their constructor defaults, so that a failed
   * evaluation never returns a half-filled result.
   */
  static void set_error(TEDSSampleEvaluation &eval_sample, int error_id, const std::string &msg) {
    eval_sample.error_id = error_id;
    eval_sample.error_msg = msg;
    eval_sample.tree_a_size = 0;
    eval_sample.tree_b_size = 0;
    eval_sample.teds = -1.;
  }

  static void set_error(TEDSDatasetEvaluation &eval_dataset, int error_id, const std::string &msg) {
    eval_dataset.error_id = error_id;
    eval_dataset.error_msg = msg;
    eval_dataset.teds = -1.;
  }

private:
  parser::BracketNotationParser<Label> bnp_;
  LabelDictionary ld_;
  std::unique_ptr<CostModelLD> ucm_ptr_ = nullptr;
  std::unique_ptr<ted::APTEDTreeIndex<CostModelLD, node::TreeIndexAPTED>> apted_ptr_;

  // Accumulated evaluations per sample
  std::unordered_map<std::string, TEDSSampleEvaluation> sample_evaluations;
};

} // namespace docling
