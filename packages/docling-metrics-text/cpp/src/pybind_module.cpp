#include "pybind11/pybind11.h"
#include <pybind11/stl.h>

#include "text_manager.h"

namespace py = pybind11;

namespace docling {

PYBIND11_MODULE(docling_metrics_text_cpp, m) {
  m.doc() = "Text metrics module";

  pybind11::class_<TextManager>(m, "TextManager", "Manager for computing text metrics")
      .def(py::init<>(), "Initialize a new TextManager instance")
      .def("tokenize", &TextManager::tokenize, py::arg("text"), py::arg("convert_parentheses"),
           "Tokenize text according to the Tree Bank Tokenizer\n\n"
           "Args:\n"
           "    text: The input text to tokenize\n"
           "    convert_parentheses: Convert all parentheses\n\n"
           "Returns:\n"
           "    List of the tokens")
      .def("edit_distance", &TextManager::edit_distance, py::arg("tokens_a"), py::arg("tokens_b"),
           "Calculate the normalized edit distance between two token lists\n\n"
           "Args:\n"
           "    tokens_a: The first list of tokens\n"
           "    tokens_b: The second list of tokens\n\n"
           "Returns:\n"
           "    The normalized edit distance as a float");
}

} // namespace docling
