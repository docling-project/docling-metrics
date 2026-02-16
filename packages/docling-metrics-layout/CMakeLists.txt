cmake_minimum_required(VERSION 3.15)


#################################################################################
# Names and versions
#
set(project_name "docling_metrics_layout_cpp")
set(cli_name "docling_metrics_layout_cli")
set(install_root "docling_metrics_layout")
set(externals_root "externals")

project("${project_name}" VERSION 1.0.0 LANGUAGES CXX C)

add_compile_definitions(PROJECT_VERSION_MAJOR=${PROJECT_VERSION_MAJOR})
add_compile_definitions(PROJECT_VERSION_MINOR=${PROJECT_VERSION_MINOR})
add_compile_definitions(PROJECT_VERSION_PATCH=${PROJECT_VERSION_PATCH})

# Debug: Show make commands
set(CMAKE_VERBOSE_MAKEFILE ON)


###########################################################################################
# Path variables
# External dependencies are downloaded inside the externals/ dir
#
include(GNUInstallDirs)

if(NOT DEFINED TOPLEVEL_PREFIX_PATH)
    set(TOPLEVEL_PREFIX_PATH "${CMAKE_CURRENT_SOURCE_DIR}")
endif()

if (DEFINED SKBUILD)
    set(CMAKE_INSTALL_PREFIX "${install_root}" CACHE PATH "Install prefix" FORCE)
elseif(CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)
    set(CMAKE_INSTALL_PREFIX "${TOPLEVEL_PREFIX_PATH}/${install_root}" CACHE PATH "Install prefix" FORCE)
endif()

if(NOT DEFINED EXTERNALS_PREFIX_PATH)
    set(EXTERNALS_PREFIX_PATH "${TOPLEVEL_PREFIX_PATH}/${externals_root}" CACHE INTERNAL "")
endif()

if(NOT "${TOPLEVEL_PREFIX_PATH}/cmake" IN_LIST CMAKE_MODULE_PATH)
    set(CMAKE_MODULE_PATH "${CMAKE_MODULE_PATH}" "${TOPLEVEL_PREFIX_PATH}/cmake")
endif()

if(CMAKE_SIZEOF_VOID_P EQUAL 8)
    set(ARCH_BIT 64)
else()
    set(ARCH_BIT 32)
endif()

set(EXTERNALS_LIB_PATH "${EXTERNALS_PREFIX_PATH}/${CMAKE_INSTALL_LIBDIR}")


set(ENV_ARCHFLAGS $ENV{ARCHFLAGS})
message(STATUS "ENV_ARCH_FLAGS: ${ENV_ARCHFLAGS}")
message(STATUS "TOP_LEVEL_PREFIX_PATH: ${TOPLEVEL_PREFIX_PATH}")
message(STATUS "EXTERNALS_PREFIX_PATH: ${EXTERNALS_PREFIX_PATH}")
message(STATUS "CMAKE_INSTALL_PREFIX: ${CMAKE_INSTALL_PREFIX}")
message(STATUS "CMAKE_MODULE_PATH: ${CMAKE_MODULE_PATH}")
message(STATUS "CMAKE_SYSTEM_PROCESSOR: ${CMAKE_SYSTEM_PROCESSOR}")
message(STATUS "MAKE_OSX_ARCHITECTURES: ${CMAKE_OSX_ARCHITECTURES}")
message(STATUS "ARCH_BIT: ${ARCH_BIT}")
message(STATUS "EXTERNALS_LIB_PATH: ${EXTERNALS_LIB_PATH}")


#################################################################################
# Compiler
#
message(STATUS "cmake osx-deployment: " ${CMAKE_OSX_DEPLOYMENT_TARGET})

# minimum macosx, ignored on other platforms
if(APPLE)
    if(NOT CMAKE_OSX_DEPLOYMENT_TARGET)
        set(CMAKE_OSX_DEPLOYMENT_TARGET "11.0" CACHE STRING "Minimum macOS version" FORCE)
    elseif(CMAKE_OSX_DEPLOYMENT_TARGET VERSION_LESS 11.0)
        set(CMAKE_OSX_DEPLOYMENT_TARGET "11.0" CACHE STRING "Minimum macOS version" FORCE)
    endif()
endif()

message(STATUS "cmake system-version: " ${CMAKE_SYSTEM_VERSION})
message(STATUS "cmake osx-deployment: " ${CMAKE_OSX_DEPLOYMENT_TARGET})

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if (WIN32)
    set(TEST_PATH "\\\"${TOPLEVEL_PREFIX_PATH}\\\"")
    add_definitions(-DROOT_PATH="\\\"${TOPLEVEL_PREFIX_PATH}\\\"")
    if (MSVC)
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /W3 /O2 ${ENV_ARCHFLAGS}")
    else()
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wno-sign-compare -O3 ${ENV_ARCHFLAGS}")
    endif()
else()
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wno-sign-compare -O3 -DROOT_PATH='\"${TOPLEVEL_PREFIX_PATH}\"' ${ENV_ARCHFLAGS}")
endif()

message(STATUS "cxx-compiler: " ${CMAKE_CXX_COMPILER})
message(STATUS "cxx-flags   : " ${CMAKE_CXX_FLAGS})
message(STATUS "cxx-standard: " ${CMAKE_CXX_STANDARD})


#################################################################################
# Source files, include dirs
#

# List of header files
# Get all *.h except those begining with underscore
file(GLOB_RECURSE layout_headers "${PROJECT_SOURCE_DIR}/cpp/include/[!_]*.h")
# message(STATUS "Header files: ${layout_headers}")

# List all header directories
set(layout_include_dirs "")
foreach(header ${layout_headers})
    get_filename_component(dir "${header}" DIRECTORY)
    list(APPEND layout_include_dirs "${dir}")
endforeach()
list(REMOVE_DUPLICATES layout_include_dirs)
list(APPEND layout_include_dirs "${pybind11_INCLUDE_DIRS}")
list(APPEND layout_include_dirs "${EXTERNALS_PREFIX_PATH}/include")
# Debug
string(REPLACE ";" "\n" layout_include_dirs_str "${layout_include_dirs}")
message(STATUS "Include dirs: ${layout_include_dirs_str}")

# List of source files that are not the CLI or the python bindings
file(GLOB_RECURSE layout_sources "cpp/[!_]*.cpp")
file(GLOB_RECURSE layout_sources_EXCLUSIONS "cpp/src/main.cpp" "cpp/src/pybind_module.cpp")
list(REMOVE_ITEM layout_sources ${layout_sources_EXCLUSIONS})
message(STATUS "Source files: ${layout_sources}")


###########################################################################################
# Dependencies
#

# Interface library for our source code
add_library(layout_interface INTERFACE)
target_include_directories(layout_interface INTERFACE "${layout_include_dirs}")
target_link_directories(layout_interface INTERFACE "${EXTERNALS_LIB_PATH}")

option(
    USE_SYSTEM_DEPS OFF
    "If enabled, find and link to system libs, otherwise compile on the fly from original source."
)

# Directory structure to building external packages
if(NOT USE_SYSTEM_DEPS)
    if(NOT EXISTS ${EXTERNALS_PREFIX_PATH})
        file(MAKE_DIRECTORY ${EXTERNALS_PREFIX_PATH})
        file(MAKE_DIRECTORY ${EXTERNALS_PREFIX_PATH}/bin)
        file(MAKE_DIRECTORY ${EXTERNALS_LIB_PATH})
        file(MAKE_DIRECTORY ${EXTERNALS_PREFIX_PATH}/include)
    endif()
endif()

# Include external dependencies
# include(cmake/extlib_cxxopts.cmake)
# include(cmake/extlib_loguru.cmake)
# include(cmake/extlib_abseil.cmake)
# include(cmake/extlib_re2.cmake)
# include(cmake/extlib_edlib.cmake)

# Use the Python from the python venv
find_package(Python3 COMPONENTS Interpreter Development.Module REQUIRED)
message(STATUS "Python3 executable: ${Python3_EXECUTABLE}")
message(STATUS "Python3 version: ${Python3_VERSION}")

# Add pybind11 from the python venv with the python from venv
set(PYBIND11_FINDPYTHON ON)
set(PYBIND11_PYTHON_VERSION ${Python3_VERSION})
execute_process(
  COMMAND ${Python3_EXECUTABLE} -m pybind11 --cmakedir
  OUTPUT_VARIABLE pybind11_DIR
  OUTPUT_STRIP_TRAILING_WHITESPACE
)
find_package(pybind11 CONFIG REQUIRED)
message(STATUS "PyBind11 + Python include dirs: ${pybind11_INCLUDE_DIRS}")
message(STATUS "PyBind11 libs: ${pybind11_LIBRARIES}")

# define LIB_LINK and OS_DEPENDENCIES
# include(cmake/os_opts.cmake)
# list(APPEND DEPENDENCIES ${OS_DEPENDENCIES})

# define subdirlist utility
# include(cmake/subdirlist.cmake)

set(dependencies
    layout_interface
    # "${ext_name_loguru}"
    # "${ext_name_cxxopts}"
    # "${ext_name_re2}"
)

###########################################################################################
# Object libraries
#
add_library(layout_objects OBJECT ${layout_sources})
add_dependencies(layout_objects ${dependencies})
target_link_libraries(layout_objects PUBLIC ${dependencies})


###########################################################################################
# Executables
#

# Compile CLI
add_executable("${cli_name}" "cpp/src/main.cpp")
add_dependencies("${cli_name}" ${dependencies})
target_link_libraries(
    "${cli_name}" PUBLIC
    layout_objects
    ${dependencies}
    ${CMAKE_DL_LIBS}
)


###########################################################################################
# Python bindings
#

pybind11_add_module(
    "${project_name}"
    "${TOPLEVEL_PREFIX_PATH}/cpp/src/pybind_module.cpp"
)
add_dependencies("${project_name}" ${dependencies})
target_link_libraries(
    "${project_name}" PUBLIC
    layout_objects
    ${dependencies}
)


###########################################################################################
# Install
#

# CLI
install(TARGETS "${cli_name}" RUNTIME DESTINATION "${CMAKE_INSTALL_PREFIX}")

# Python bindings
install(TARGETS "${project_name}" LIBRARY DESTINATION "${CMAKE_INSTALL_PREFIX}")


###########################################################################################
# Tests
#

include(CTest)

# Collect all test targets
set(all_test_targets)

file(GLOB_RECURSE test_srcs "cpp_tests/[!_]*.cpp")
foreach(test_fn ${test_srcs})
  cmake_path(GET test_fn STEM test_name)
  message(STATUS "Build test: ${test_name}")
  set(all_test_targets ${all_test_targets} ${test_name})

  add_executable("${test_name}" "${test_fn}")
  target_link_libraries("${test_name}" PRIVATE
    layout_objects
    ${dependencies}
  )
  add_test(NAME "${test_name}" COMMAND "${test_name}" WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}")
endforeach()

