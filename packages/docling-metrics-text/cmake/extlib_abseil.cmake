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

    # Collect all abseil base names (without platform-specific prefix/suffix).
    # Must be defined before ExternalProject_Add so the paths can be used in BUILD_BYPRODUCTS.
    # CMAKE_STATIC_LIBRARY_PREFIX/SUFFIX resolve to:
    #   Linux/macOS: "lib" / ".a"  →  libabsl_base.a
    #   Windows MSVC: ""   / ".lib" →  absl_base.lib
    set(abseil_base_names
        absl_base
        absl_borrowed_fixup_buffer
        absl_city
        absl_civil_time
        absl_cord_internal
        absl_cord
        absl_cordz_functions
        absl_cordz_handle
        absl_cordz_info
        absl_cordz_sample_token
        absl_crc_cord_state
        absl_crc_cpu_detect
        absl_crc_internal
        absl_crc32c
        absl_debugging_internal
        absl_decode_rust_punycode
        absl_demangle_internal
        absl_demangle_rust
        absl_die_if_null
        absl_examine_stack
        absl_exponential_biased
        absl_failure_signal_handler
        absl_flags_commandlineflag_internal
        absl_flags_commandlineflag
        absl_flags_config
        absl_flags_internal
        absl_flags_marshalling
        absl_flags_parse
        absl_flags_private_handle_accessor
        absl_flags_program_name
        absl_flags_reflection
        absl_flags_usage_internal
        absl_flags_usage
        absl_generic_printer_internal
        absl_graphcycles_internal
        absl_hash
        absl_hashtable_profiler
        absl_hashtablez_sampler
        absl_int128
        absl_kernel_timeout_internal
        absl_leak_check
        absl_log_entry
        absl_log_flags
        absl_log_globals
        absl_log_initialize
        absl_log_internal_check_op
        absl_log_internal_conditions
        absl_log_internal_fnmatch
        absl_log_internal_format
        absl_log_internal_globals
        absl_log_internal_log_sink_set
        absl_log_internal_message
        absl_log_internal_nullguard
        absl_log_internal_proto
        absl_log_internal_structured_proto
        absl_log_severity
        absl_log_sink
        absl_malloc_internal
        absl_periodic_sampler
        absl_poison
        absl_profile_builder
        absl_random_distributions
        absl_random_internal_distribution_test_util
        absl_random_internal_entropy_pool
        absl_random_internal_platform
        absl_random_internal_randen_hwaes_impl
        absl_random_internal_randen_hwaes
        absl_random_internal_randen_slow
        absl_random_internal_randen
        absl_random_internal_seed_material
        absl_random_seed_gen_exception
        absl_random_seed_sequences
        absl_raw_hash_set
        absl_raw_logging_internal
        absl_scoped_set_env
        absl_spinlock_wait
        absl_stacktrace
        absl_status
        absl_statusor
        absl_str_format_internal
        absl_strerror
        absl_strings_internal
        absl_strings
        absl_symbolize
        absl_synchronization
        absl_throw_delegate
        absl_time_zone
        absl_time
        absl_tracing_internal
        absl_utf8_for_code_point
        absl_vlog_config_internal
    )

    set(abseil_lib_paths "")
    foreach(name ${abseil_base_names})
        list(APPEND abseil_lib_paths
            "${EXTERNALS_LIB_PATH}/${CMAKE_STATIC_LIBRARY_PREFIX}${name}${CMAKE_STATIC_LIBRARY_SUFFIX}")
    endforeach()

    # Abseil GitHub
    set(abseil_git_url https://github.com/abseil/abseil-cpp.git)
    set(abseil_git_tag 20260107.0)
    ExternalProject_Add(extlib_abseil_source
        PREFIX extlib_abseil

        UPDATE_COMMAND ""
        GIT_REPOSITORY "${abseil_git_url}"
        GIT_TAG "${abseil_git_tag}"

        BUILD_ALWAYS OFF

        INSTALL_DIR ${EXTERNALS_PREFIX_PATH}

        # By default it builds static *.a files
        # Add flag to switch into dynamic libraries -DBUILD_SHARED_LIBS=ON \\
        CMAKE_ARGS \\
        -DCMAKE_POSITION_INDEPENDENT_CODE=ON \\
        -DCMAKE_INSTALL_PREFIX=${EXTERNALS_PREFIX_PATH} \\
        -DCMAKE_INSTALL_LIBDIR=${CMAKE_INSTALL_LIBDIR} \\
        -DCMAKE_CXX_STANDARD=20

        BUILD_IN_SOURCE ON
        LOG_DOWNLOAD ON

        # Declare outputs so Ninja knows this ExternalProject produces the abseil static libs.
        # Without BUILD_BYPRODUCTS, Ninja treats these paths as required inputs with no
        # build rule and fails with "missing and no known rule to make it".
        BUILD_BYPRODUCTS ${abseil_lib_paths}
    )

    add_library("${ext_name_abseil}" INTERFACE)
    add_dependencies("${ext_name_abseil}" extlib_abseil_source)
    target_include_directories(
        "${ext_name_abseil}" INTERFACE
        ${EXTERNALS_PREFIX_PATH}/include
    )

    if(APPLE)
        find_library(COREFOUNDATION_LIBRARY CoreFoundation REQUIRED)
        target_link_libraries(
            "${ext_name_abseil}" INTERFACE
            ${abseil_lib_paths}
            ${COREFOUNDATION_LIBRARY}
        )
    elseif(WIN32)
        # MSVC does not support -Wl,--start-group / --end-group; the MSVC linker
        # handles static library ordering automatically.
        target_link_libraries(
            "${ext_name_abseil}" INTERFACE
            ${abseil_lib_paths}
        )
    else()
        # Use linker group to handle circular dependencies between abseil static libs.
        # ${CMAKE_DL_LIBS} is required on Linux (glibc < 2.34) because libabsl_symbolize
        # calls dladdr, which lives in libdl on those systems.
        target_link_libraries(
            "${ext_name_abseil}" INTERFACE
            -Wl,--start-group
            ${abseil_lib_paths}
            -Wl,--end-group
            ${CMAKE_DL_LIBS}
        )
    endif()
endif()

