#pragma once

namespace docling {

static constexpr uint64_t kBytesPerGB = 1024ULL * 1024 * 1024;

/**
 * Get total physical system memory in GB
 */
#if defined(_WIN32)
#include <windows.h>
inline uint64_t GetTotalSystemGB() {
  MEMORYSTATUSEX status;
  status.dwLength = sizeof(status);
  GlobalMemoryStatusEx(&status);
  return status.ullTotalPhys / kBytesPerGB;
}
#else
#include <unistd.h>
inline uint64_t GetTotalSystemGB() {
  long pages = sysconf(_SC_PHYS_PAGES);
  long page_size = sysconf(_SC_PAGE_SIZE);
  return (static_cast<uint64_t>(pages) * page_size) / kBytesPerGB;
}

#endif

} // namespace docling