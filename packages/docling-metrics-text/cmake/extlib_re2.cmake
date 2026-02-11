message(STATUS "Entering in extlib_re2.cmake")

set(ext_name_re2 "re2")

if(USE_SYSTEM_DEPS)
    message(STATUS "Using system-deps in extlib_re2.cmake")

    find_package(re2 CONFIG REQUIRED)
    pkg_check_modules(RE2 REQUIRED re2)
    add_library(${ext_name_re2} ALIAS PkgConfig::libre2)
else()
    message(STATUS "Ignoring system-deps in extlib_re2.cmake")

    include(ExternalProject)
    include(CMakeParseArguments)

    # Re2 GitHub
    set(re_git_url https://github.com/google/re2.git)
    set(re_git_tag 2025-11-05)
    ExternalProject_Add(extlib_re2_source
        # Add dependency on abseil to ensure that the source code of Abseil builds first
        DEPENDS extlib_abseil_source

        PREFIX extlib_re2

        UPDATE_COMMAND ""
        GIT_REPOSITORY "${re_git_url}"
        GIT_TAG "${re_git_tag}"

        BUILD_ALWAYS OFF

        INSTALL_DIR ${EXTERNALS_PREFIX_PATH}

        # By default it builds static *.a files
        # Add flag to switch into dynamic libraries -DBUILD_SHARED_LIBS=ON \\
        # Ensure that abseil is properly seen by setting DCMAKE_PREFIX_PATH=${EXTERNALS_PREFIX_PATH}
        CMAKE_ARGS \\
        -DCMAKE_POSITION_INDEPENDENT_CODE=ON \\
        -DCMAKE_INSTALL_PREFIX=${EXTERNALS_PREFIX_PATH} \\
        -DCMAKE_PREFIX_PATH=${EXTERNALS_PREFIX_PATH}

        BUILD_IN_SOURCE ON
        LOG_DOWNLOAD ON
    )

    add_library("${ext_name_re2}" INTERFACE)
    # add_dependencies("${ext_name_re2}" "${ext_name_abseil}" extlib_re2_source)
    # add_dependencies("${ext_name_re2}" "${ext_name_abseil}")
    add_dependencies("${ext_name_re2}" extlib_re2_source)

    target_include_directories(
        "${ext_name_re2}" INTERFACE
        ${EXTERNALS_PREFIX_PATH}/include
    )
    target_link_libraries(
        "${ext_name_re2}" INTERFACE
        ${EXTERNALS_PREFIX_PATH}/lib/libre2.a
    )
endif()

