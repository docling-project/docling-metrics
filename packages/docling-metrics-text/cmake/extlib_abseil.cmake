message(STATUS "Entering in extlib_abseil.cmake")

set(ext_name_abseil "abseil")

if(USE_SYSTEM_DEPS)
    message(STATUS "Using system-deps in extlib_abseil.cmake")

    find_package(abseil CONFIG REQUIRED)
    pkg_check_modules(abseil REQUIRED abseil)
    add_library(${ext_name_abseil} ALIAS PkgConfig::libabseil)
else()
    message(STATUS "Ignoring system-deps in extlib_abseil.cmake")

    include(ExternalProject)
    include(CMakeParseArguments)

    # Abseil GitHub
    set(abseil_git_url https://github.com/abseil/abseil-cpp.git)
    set(abseil_git_tag 20260107.0)
    ExternalProject_Add(extlib_abseil_source
        PREFIX extlib_abseil

        UPDATE_COMMAND ""
        GIT_REPOSITORY "${abseil_git_url}"
        GIT_TAG "${re_git_tag}"

        BUILD_ALWAYS OFF

        INSTALL_DIR ${EXTERNALS_PREFIX_PATH}

        # By default it builds static *.a files
        # Add flag to switch into dynamic libraries -DBUILD_SHARED_LIBS=ON \\
        CMAKE_ARGS \\
        -DCMAKE_POSITION_INDEPENDENT_CODE=ON \\
        -DCMAKE_INSTALL_PREFIX=${EXTERNALS_PREFIX_PATH} \\
        -DCMAKE_CXX_STANDARD=20

        BUILD_IN_SOURCE ON
        LOG_DOWNLOAD ON
    )

    # Collect all abseil libraries that will be built
    add_library("${ext_name_abseil}" INTERFACE)
    add_dependencies("${ext_name_abseil}" extlib_abseil_source)
    target_include_directories(
        "${ext_name_abseil}" INTERFACE
        ${EXTERNALS_PREFIX_PATH}/include
    )
    target_link_directories(
        "${ext_name_abseil}" INTERFACE
        ${EXTERNALS_PREFIX_PATH}/lib
    )
endif()
