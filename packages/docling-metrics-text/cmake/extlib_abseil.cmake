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
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_base.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_borrowed_fixup_buffer.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_city.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_civil_time.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_clock_interface.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_cord_internal.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_cord.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_cordz_functions.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_cordz_handle.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_cordz_info.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_cordz_sample_token.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_crc_cord_state.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_crc_cpu_detect.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_crc_internal.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_crc32c.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_debugging_internal.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_decode_rust_punycode.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_demangle_internal.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_demangle_rust.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_die_if_null.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_examine_stack.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_exponential_biased.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_failure_signal_handler.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_flags_commandlineflag_internal.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_flags_commandlineflag.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_flags_config.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_flags_internal.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_flags_marshalling.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_flags_parse.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_flags_private_handle_accessor.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_flags_program_name.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_flags_reflection.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_flags_usage_internal.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_flags_usage.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_generic_printer_internal.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_graphcycles_internal.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_hash.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_hashtable_profiler.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_hashtablez_sampler.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_int128.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_kernel_timeout_internal.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_leak_check.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_log_entry.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_log_flags.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_log_globals.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_log_initialize.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_log_internal_check_op.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_log_internal_conditions.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_log_internal_fnmatch.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_log_internal_format.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_log_internal_globals.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_log_internal_log_sink_set.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_log_internal_message.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_log_internal_nullguard.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_log_internal_proto.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_log_internal_structured_proto.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_log_severity.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_log_sink.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_malloc_internal.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_periodic_sampler.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_poison.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_profile_builder.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_random_distributions.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_random_internal_distribution_test_util.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_random_internal_entropy_pool.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_random_internal_platform.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_random_internal_randen_hwaes_impl.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_random_internal_randen_hwaes.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_random_internal_randen_slow.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_random_internal_randen.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_random_internal_seed_material.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_random_seed_gen_exception.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_random_seed_sequences.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_raw_hash_set.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_raw_logging_internal.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_reflection_internal.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_scoped_set_env.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_spinlock_wait.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_stacktrace.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_status.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_statusor.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_str_format_internal.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_strerror.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_strings_internal.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_strings.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_symbolize.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_synchronization.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_throw_delegate.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_time_zone.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_time.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_tracing_internal.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_utf8_for_code_point.a
        ${EXTERNALS_PREFIX_PATH}/lib/libabsl_vlog_config_internal.a
    )

   if(APPLE)
       find_library(COREFOUNDATION_LIBRARY CoreFoundation REQUIRED)
       target_link_libraries("${ext_name_abseil}" INTERFACE ${COREFOUNDATION_LIBRARY})
   endif()
endif()

