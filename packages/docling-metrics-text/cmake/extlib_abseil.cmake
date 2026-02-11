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
    target_link_libraries(
        "${ext_name_abseil}" INTERFACE
        ${EXTERNALS_LIB_PATH}/libabsl_base.a
        ${EXTERNALS_LIB_PATH}/libabsl_borrowed_fixup_buffer.a
        ${EXTERNALS_LIB_PATH}/libabsl_city.a
        ${EXTERNALS_LIB_PATH}/libabsl_civil_time.a
        ${EXTERNALS_LIB_PATH}/libabsl_clock_interface.a
        ${EXTERNALS_LIB_PATH}/libabsl_cord_internal.a
        ${EXTERNALS_LIB_PATH}/libabsl_cord.a
        ${EXTERNALS_LIB_PATH}/libabsl_cordz_functions.a
        ${EXTERNALS_LIB_PATH}/libabsl_cordz_handle.a
        ${EXTERNALS_LIB_PATH}/libabsl_cordz_info.a
        ${EXTERNALS_LIB_PATH}/libabsl_cordz_sample_token.a
        ${EXTERNALS_LIB_PATH}/libabsl_crc_cord_state.a
        ${EXTERNALS_LIB_PATH}/libabsl_crc_cpu_detect.a
        ${EXTERNALS_LIB_PATH}/libabsl_crc_internal.a
        ${EXTERNALS_LIB_PATH}/libabsl_crc32c.a
        ${EXTERNALS_LIB_PATH}/libabsl_debugging_internal.a
        ${EXTERNALS_LIB_PATH}/libabsl_decode_rust_punycode.a
        ${EXTERNALS_LIB_PATH}/libabsl_demangle_internal.a
        ${EXTERNALS_LIB_PATH}/libabsl_demangle_rust.a
        ${EXTERNALS_LIB_PATH}/libabsl_die_if_null.a
        ${EXTERNALS_LIB_PATH}/libabsl_examine_stack.a
        ${EXTERNALS_LIB_PATH}/libabsl_exponential_biased.a
        ${EXTERNALS_LIB_PATH}/libabsl_failure_signal_handler.a
        ${EXTERNALS_LIB_PATH}/libabsl_flags_commandlineflag_internal.a
        ${EXTERNALS_LIB_PATH}/libabsl_flags_commandlineflag.a
        ${EXTERNALS_LIB_PATH}/libabsl_flags_config.a
        ${EXTERNALS_LIB_PATH}/libabsl_flags_internal.a
        ${EXTERNALS_LIB_PATH}/libabsl_flags_marshalling.a
        ${EXTERNALS_LIB_PATH}/libabsl_flags_parse.a
        ${EXTERNALS_LIB_PATH}/libabsl_flags_private_handle_accessor.a
        ${EXTERNALS_LIB_PATH}/libabsl_flags_program_name.a
        ${EXTERNALS_LIB_PATH}/libabsl_flags_reflection.a
        ${EXTERNALS_LIB_PATH}/libabsl_flags_usage_internal.a
        ${EXTERNALS_LIB_PATH}/libabsl_flags_usage.a
        ${EXTERNALS_LIB_PATH}/libabsl_generic_printer_internal.a
        ${EXTERNALS_LIB_PATH}/libabsl_graphcycles_internal.a
        ${EXTERNALS_LIB_PATH}/libabsl_hash.a
        ${EXTERNALS_LIB_PATH}/libabsl_hashtable_profiler.a
        ${EXTERNALS_LIB_PATH}/libabsl_hashtablez_sampler.a
        ${EXTERNALS_LIB_PATH}/libabsl_int128.a
        ${EXTERNALS_LIB_PATH}/libabsl_kernel_timeout_internal.a
        ${EXTERNALS_LIB_PATH}/libabsl_leak_check.a
        ${EXTERNALS_LIB_PATH}/libabsl_log_entry.a
        ${EXTERNALS_LIB_PATH}/libabsl_log_flags.a
        ${EXTERNALS_LIB_PATH}/libabsl_log_globals.a
        ${EXTERNALS_LIB_PATH}/libabsl_log_initialize.a
        ${EXTERNALS_LIB_PATH}/libabsl_log_internal_check_op.a
        ${EXTERNALS_LIB_PATH}/libabsl_log_internal_conditions.a
        ${EXTERNALS_LIB_PATH}/libabsl_log_internal_fnmatch.a
        ${EXTERNALS_LIB_PATH}/libabsl_log_internal_format.a
        ${EXTERNALS_LIB_PATH}/libabsl_log_internal_globals.a
        ${EXTERNALS_LIB_PATH}/libabsl_log_internal_log_sink_set.a
        ${EXTERNALS_LIB_PATH}/libabsl_log_internal_message.a
        ${EXTERNALS_LIB_PATH}/libabsl_log_internal_nullguard.a
        ${EXTERNALS_LIB_PATH}/libabsl_log_internal_proto.a
        ${EXTERNALS_LIB_PATH}/libabsl_log_internal_structured_proto.a
        ${EXTERNALS_LIB_PATH}/libabsl_log_severity.a
        ${EXTERNALS_LIB_PATH}/libabsl_log_sink.a
        ${EXTERNALS_LIB_PATH}/libabsl_malloc_internal.a
        ${EXTERNALS_LIB_PATH}/libabsl_periodic_sampler.a
        ${EXTERNALS_LIB_PATH}/libabsl_poison.a
        ${EXTERNALS_LIB_PATH}/libabsl_profile_builder.a
        ${EXTERNALS_LIB_PATH}/libabsl_random_distributions.a
        ${EXTERNALS_LIB_PATH}/libabsl_random_internal_distribution_test_util.a
        ${EXTERNALS_LIB_PATH}/libabsl_random_internal_entropy_pool.a
        ${EXTERNALS_LIB_PATH}/libabsl_random_internal_platform.a
        ${EXTERNALS_LIB_PATH}/libabsl_random_internal_randen_hwaes_impl.a
        ${EXTERNALS_LIB_PATH}/libabsl_random_internal_randen_hwaes.a
        ${EXTERNALS_LIB_PATH}/libabsl_random_internal_randen_slow.a
        ${EXTERNALS_LIB_PATH}/libabsl_random_internal_randen.a
        ${EXTERNALS_LIB_PATH}/libabsl_random_internal_seed_material.a
        ${EXTERNALS_LIB_PATH}/libabsl_random_seed_gen_exception.a
        ${EXTERNALS_LIB_PATH}/libabsl_random_seed_sequences.a
        ${EXTERNALS_LIB_PATH}/libabsl_raw_hash_set.a
        ${EXTERNALS_LIB_PATH}/libabsl_raw_logging_internal.a
        ${EXTERNALS_LIB_PATH}/libabsl_reflection_internal.a
        ${EXTERNALS_LIB_PATH}/libabsl_scoped_set_env.a
        ${EXTERNALS_LIB_PATH}/libabsl_spinlock_wait.a
        ${EXTERNALS_LIB_PATH}/libabsl_stacktrace.a
        ${EXTERNALS_LIB_PATH}/libabsl_status.a
        ${EXTERNALS_LIB_PATH}/libabsl_statusor.a
        ${EXTERNALS_LIB_PATH}/libabsl_str_format_internal.a
        ${EXTERNALS_LIB_PATH}/libabsl_strerror.a
        ${EXTERNALS_LIB_PATH}/libabsl_strings_internal.a
        ${EXTERNALS_LIB_PATH}/libabsl_strings.a
        ${EXTERNALS_LIB_PATH}/libabsl_symbolize.a
        ${EXTERNALS_LIB_PATH}/libabsl_synchronization.a
        ${EXTERNALS_LIB_PATH}/libabsl_throw_delegate.a
        ${EXTERNALS_LIB_PATH}/libabsl_time_zone.a
        ${EXTERNALS_LIB_PATH}/libabsl_time.a
        ${EXTERNALS_LIB_PATH}/libabsl_tracing_internal.a
        ${EXTERNALS_LIB_PATH}/libabsl_utf8_for_code_point.a
        ${EXTERNALS_LIB_PATH}/libabsl_vlog_config_internal.a
    )

   if(APPLE)
       find_library(COREFOUNDATION_LIBRARY CoreFoundation REQUIRED)
       target_link_libraries("${ext_name_abseil}" INTERFACE ${COREFOUNDATION_LIBRARY})
   endif()
endif()

