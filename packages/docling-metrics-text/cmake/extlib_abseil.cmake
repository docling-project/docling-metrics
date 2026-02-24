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

    # Collect all abseil libraries that will be built.
    # Must be defined before ExternalProject_Add so the paths can be used in BUILD_BYPRODUCTS.
    set(abseil_libs
        libabsl_base.a
        libabsl_borrowed_fixup_buffer.a
        libabsl_city.a
        libabsl_civil_time.a
        libabsl_cord_internal.a
        libabsl_cord.a
        libabsl_cordz_functions.a
        libabsl_cordz_handle.a
        libabsl_cordz_info.a
        libabsl_cordz_sample_token.a
        libabsl_crc_cord_state.a
        libabsl_crc_cpu_detect.a
        libabsl_crc_internal.a
        libabsl_crc32c.a
        libabsl_debugging_internal.a
        libabsl_decode_rust_punycode.a
        libabsl_demangle_internal.a
        libabsl_demangle_rust.a
        libabsl_die_if_null.a
        libabsl_examine_stack.a
        libabsl_exponential_biased.a
        libabsl_failure_signal_handler.a
        libabsl_flags_commandlineflag_internal.a
        libabsl_flags_commandlineflag.a
        libabsl_flags_config.a
        libabsl_flags_internal.a
        libabsl_flags_marshalling.a
        libabsl_flags_parse.a
        libabsl_flags_private_handle_accessor.a
        libabsl_flags_program_name.a
        libabsl_flags_reflection.a
        libabsl_flags_usage_internal.a
        libabsl_flags_usage.a
        libabsl_generic_printer_internal.a
        libabsl_graphcycles_internal.a
        libabsl_hash.a
        libabsl_hashtable_profiler.a
        libabsl_hashtablez_sampler.a
        libabsl_int128.a
        libabsl_kernel_timeout_internal.a
        libabsl_leak_check.a
        libabsl_log_entry.a
        libabsl_log_flags.a
        libabsl_log_globals.a
        libabsl_log_initialize.a
        libabsl_log_internal_check_op.a
        libabsl_log_internal_conditions.a
        libabsl_log_internal_fnmatch.a
        libabsl_log_internal_format.a
        libabsl_log_internal_globals.a
        libabsl_log_internal_log_sink_set.a
        libabsl_log_internal_message.a
        libabsl_log_internal_nullguard.a
        libabsl_log_internal_proto.a
        libabsl_log_internal_structured_proto.a
        libabsl_log_severity.a
        libabsl_log_sink.a
        libabsl_malloc_internal.a
        libabsl_periodic_sampler.a
        libabsl_poison.a
        libabsl_profile_builder.a
        libabsl_random_distributions.a
        libabsl_random_internal_distribution_test_util.a
        libabsl_random_internal_entropy_pool.a
        libabsl_random_internal_platform.a
        libabsl_random_internal_randen_hwaes_impl.a
        libabsl_random_internal_randen_hwaes.a
        libabsl_random_internal_randen_slow.a
        libabsl_random_internal_randen.a
        libabsl_random_internal_seed_material.a
        libabsl_random_seed_gen_exception.a
        libabsl_random_seed_sequences.a
        libabsl_raw_hash_set.a
        libabsl_raw_logging_internal.a
        libabsl_scoped_set_env.a
        libabsl_spinlock_wait.a
        libabsl_stacktrace.a
        libabsl_status.a
        libabsl_statusor.a
        libabsl_str_format_internal.a
        libabsl_strerror.a
        libabsl_strings_internal.a
        libabsl_strings.a
        libabsl_symbolize.a
        libabsl_synchronization.a
        libabsl_throw_delegate.a
        libabsl_time_zone.a
        libabsl_time.a
        libabsl_tracing_internal.a
        libabsl_utf8_for_code_point.a
        libabsl_vlog_config_internal.a
    )

    set(abseil_lib_paths "")
    foreach(abseil_lib ${abseil_libs})
        list(APPEND abseil_lib_paths "${EXTERNALS_LIB_PATH}/${abseil_lib}")
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
    else()
        # Use linker group to handle circular dependencies between abseil static libs
        target_link_libraries(
            "${ext_name_abseil}" INTERFACE
            -Wl,--start-group
            ${abseil_lib_paths}
            -Wl,--end-group
        )
    endif()
endif()

