#include <cassert>
#include <iostream>

#include "utils.h"

void test_system_memory_gt_1gb() {
  uint64_t total_gb = docling::GetTotalSystemGB();
  std::cout << "Total system memory: " << total_gb << " GB\n";
  assert(total_gb > 1 && "Expected system memory to be greater than 1 GB");
  std::cout << "  OK!\n";
}

int main(int argc, char *argv[]) {
  test_system_memory_gt_1gb();
  return 0;
}
