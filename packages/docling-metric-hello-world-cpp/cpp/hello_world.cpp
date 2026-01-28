#include <pybind11/pybind11.h>
#include <string>

namespace py = pybind11;

static double evaluate_sample(
    const std::string &id,
    const std::string &payload_a,
    const std::string &payload_b
) {
    (void)id;
    (void)payload_a;
    (void)payload_b;
    return 1.0;
}

PYBIND11_MODULE(_hello_world_cpp, m) {
    m.doc() = "Hello World C++ metric bindings";
    m.def("evaluate_sample", &evaluate_sample, "Return constant score");
}
