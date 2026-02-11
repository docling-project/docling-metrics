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
           "    List of the tokens");
}

} // namespace docling
