#include "pybind11/pybind11.h"
#include <pybind11/stl.h>

#include "layout_manager.h"

namespace py = pybind11;

namespace docling {

PYBIND11_MODULE(docling_metrics_layout_cpp, m) {
  m.doc() = "Layout metrics module";

  pybind11::class_<LayoutManager>(m, "LayoutManager", "Manager for computing layout metrics")
      .def(py::init<>(), "Initialize a new LayoutManager instance");
}

} // namespace docling
