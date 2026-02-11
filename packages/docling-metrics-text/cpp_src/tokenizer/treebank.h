#pragma once
#include <string>
#include <vector>

namespace docling {

class TreeBankTokenizer {
public:
  TreeBankTokenizer();

  std::vector<std::string> tokenize(const std::string &text);
};

} // namespace docling
