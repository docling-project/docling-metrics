#include <optional>
#include "pybind11/pybind11.h"
#include <pybind11/stl.h>

#include "teds_manager.h"


namespace py = pybind11;

namespace docling {

PYBIND11_MODULE(docling_metric_teds_cpp, m) {
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
        .def("evaluate_sample", &TEDSManager::evaluate_sample,
             py::arg("id"), py::arg("bracket_a"), py::arg("bracket_b"),
             "Evaluate a single sample\n\n"
             "Args:\n"
             "    id: Sample identifier\n"
             "    bracket_a: Input A in bracket notation\n"
             "    bracket_b: Input B in bracket notation\n\n"
             "Returns:\n"
             "    TEDSSampleEvaluation: Evaluation result containing TEDS score and metadata")
        .def("evaluate_html_sample", &TEDSManager::evaluate_html_sample,
             py::arg("id"), py::arg("html_a"), py::arg("html_b"), py::arg("structure_only"),
             "Evaluate a single sample from HTML format\n\n"
             "Args:\n"
             "    id: Sample identifier\n"
             "    html_a: Input A in HTML format\n"
             "    html_b: Input B in HTML format\n\n"
             "    structure_only: If true the HTML content is not considered\n\n"
             "Returns:\n"
             "    TEDSSampleEvaluation: Evaluation result containing TEDS score and metadata")
        .def("aggregate", &TEDSManager::aggregate,
             "Aggregate evaluation results across all samples")
        .def("evaluate_dataset", &TEDSManager::evaluate_dataset,
             "Evaluate the entire dataset\n\n"
             "Returns:\n"
             "    TEDSDatasetEvaluation: Dataset-level evaluation result");
}

}  // namespace docling

