cmake_minimum_required(VERSION 3.18)
project(docling_metric_hello_world_cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(_hello_world_cpp cpp/hello_world.cpp)

target_compile_features(_hello_world_cpp PRIVATE cxx_std_17)

install(
    TARGETS _hello_world_cpp
    LIBRARY DESTINATION "${CMAKE_CURRENT_SOURCE_DIR}/docling_metrics_hello_world_cpp"
)
