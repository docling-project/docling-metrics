#include <iostream>
#include <string>
#include <vector>

#include "re2/re2.h"

void demo_regex() {
  int i;
  std::string s;
  RE2 re("(\\w+):(\\d+)");
  assert(re.ok()); // compiled; if not, see re.error();

  assert(RE2::FullMatch("ruby:1234", re, &s, &i));
  assert(RE2::FullMatch("ruby:1234", re, &s));
  assert(RE2::FullMatch("ruby:1234", re, (void *)NULL, &i));
  assert(!RE2::FullMatch("ruby:123456789123", re, &s, &i));
}

int main(int argc, char *argv[]) {
  demo_regex();
  return 0;
}
