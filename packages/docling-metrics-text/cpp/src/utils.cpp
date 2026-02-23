#include "utils.h"
#include "loguru.hpp"
#include <stdexcept>
#include <string>

#if defined(_WIN32)
#include <windows.h>
#else
#include <unistd.h>
#endif

namespace docling {

const uint64_t kBytesPerGB = 1024ULL * 1024 * 1024;

#if defined(_WIN32)
uint64_t GetTotalSystemGB() {
  MEMORYSTATUSEX status;
  status.dwLength = sizeof(status);
  GlobalMemoryStatusEx(&status);
  return status.ullTotalPhys / kBytesPerGB;
}
#else
uint64_t GetTotalSystemGB() {
  long pages = sysconf(_SC_PHYS_PAGES);
  long page_size = sysconf(_SC_PAGE_SIZE);
  return (static_cast<uint64_t>(pages) * page_size) / kBytesPerGB;
}
#endif

void set_loglevel(std::string level) {
  if (level == "info") {
    loguru::g_stderr_verbosity = loguru::Verbosity_INFO;
  } else if (level == "warning") {
    loguru::g_stderr_verbosity = loguru::Verbosity_WARNING;
  } else if (level == "error") {
    loguru::g_stderr_verbosity = loguru::Verbosity_ERROR;
  } else if (level == "fatal") {
    loguru::g_stderr_verbosity = loguru::Verbosity_FATAL;
  } else {
    throw std::invalid_argument("Unsupported log level: " + level);
  }
}

} // namespace docling