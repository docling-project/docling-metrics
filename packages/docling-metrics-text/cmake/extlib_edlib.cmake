message(STATUS "Entering in extlib_edlib.cmake")

set(ext_name_edlib "edlib")

if(USE_SYSTEM_DEPS)
    message(STATUS "Using system-deps in extlib_edlib.cmake")

    find_package(edlib CONFIG REQUIRED)
    pkg_check_modules(edlib REQUIRED edlib)
    add_library(${ext_name_edlib} ALIAS PkgConfig::libedlib)
else()
    message(STATUS "Ignoring system-deps in extlib_edlib.cmake")

    include(ExternalProject)
    include(CMakeParseArguments)

    # Edlib GitHub
    set(edlib_git_url https://github.com/Martinsos/edlib.git)
    set(edlib_git_tag 0ddc23ea06abd95ab6227442acb4c27bd7607b68)  # Use commit to avoid CMAKE version error
    ExternalProject_Add(extlib_edlib_source
        PREFIX extlib_edlib

        UPDATE_COMMAND ""
        GIT_REPOSITORY "${edlib_git_url}"
        GIT_TAG "${edlib_git_tag}"

        BUILD_ALWAYS OFF

        INSTALL_DIR ${EXTERNALS_PREFIX_PATH}

        # By default it builds static *.a files
        CMAKE_ARGS \\
        -DCMAKE_POSITION_INDEPENDENT_CODE=ON \\
        -DCMAKE_INSTALL_PREFIX=${EXTERNALS_PREFIX_PATH} \\
        -DCMAKE_INSTALL_LIBDIR=${CMAKE_INSTALL_LIBDIR}

        BUILD_IN_SOURCE ON
        LOG_DOWNLOAD ON
    )

    add_library("${ext_name_edlib}" INTERFACE)
    add_dependencies("${ext_name_edlib}" extlib_edlib_source)

    target_include_directories(
        "${ext_name_edlib}" INTERFACE
        ${EXTERNALS_PREFIX_PATH}/include
    )
    target_link_libraries(
        "${ext_name_edlib}" INTERFACE
        ${EXTERNALS_LIB_PATH}/libedlib.a
    )
endif()
