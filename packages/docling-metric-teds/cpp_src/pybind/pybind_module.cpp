#include <optional>
#include "pybind11/pybind11.h"
#include <pybind11/stl.h>
// #include <pybind11/buffer_info.h>
// #include <pybind/utils/pybind11_json.h>

#include "teds_manager.h"


namespace py = pybind11;

namespace docling {

PYBIND11_MODULE(docling_metric_teds, m) {
    m.doc() = "Docling TEDS (Tree Edit Distance based Similarity) metric module";

    pybind11::class_<TEDSSampleEvaluation>(m, "TEDSSampleEvaluation", "Evaluation result for a single sample")
        .def_readwrite("error_id", &TEDSSampleEvaluation::error_id, "Error identifier (0 if no error)")
        .def_readwrite("error_msg", &TEDSSampleEvaluation::error_msg, "Error message (empty if no error)")
        .def_readwrite("id", &TEDSSampleEvaluation::id, "Sample identifier")
        .def_readwrite("gt_tree_size", &TEDSSampleEvaluation::gt_tree_size, "Size of the ground truth tree")
        .def_readwrite("pred_tree_size", &TEDSSampleEvaluation::pred_tree_size, "Size of the prediction tree")
        .def_readwrite("teds", &TEDSSampleEvaluation::teds, "TEDS score (1.0 - normalized tree edit distance)");

    pybind11::class_<TEDSDatasetEvaluation>(m, "TEDSDatasetEvaluation", "Evaluation result for an entire dataset")
        .def_readwrite("error_id", &TEDSDatasetEvaluation::error_id, "Error identifier (0 if no error)")
        .def_readwrite("error_msg", &TEDSDatasetEvaluation::error_msg, "Error message (empty if no error)")
        .def_readwrite("teds", &TEDSDatasetEvaluation::teds, "Aggregated TEDS score for the dataset")
        .def_readwrite("sample_evaluations", &TEDSDatasetEvaluation::sample_evaluations, "Dictionary of sample evaluations keyed by sample ID");

    pybind11::class_<TEDSManager>(m, "TEDSManager", "Manager for computing TEDS metrics on tree structures")
        .def(py::init<>(), "Initialize a new TEDSManager instance")
        .def("eval_sample", &TEDSManager::eval_sample,
             py::arg("id"), py::arg("gt_bracket"), py::arg("pred_bracket"),
             "Evaluate a single sample\n\n"
             "Args:\n"
             "    id: Sample identifier\n"
             "    gt_bracket: Ground truth tree in bracket notation\n"
             "    pred_bracket: Prediction tree in bracket notation\n\n"
             "Returns:\n"
             "    TEDSampleEvaluation: Evaluation result containing TEDS score and metadata")
        .def("aggregate", &TEDSManager::aggregate,
             "Aggregate evaluation results across all samples")
        .def("eval_dataset", &TEDSManager::eval_dataset,
             "Evaluate the entire dataset\n\n"
             "Returns:\n"
             "    TEDSDatasetEvaluation: Dataset-level evaluation result");

}

}  // namespace docling

