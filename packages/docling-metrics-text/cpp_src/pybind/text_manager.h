#pragma once
#include <string>
#include <vector>

#include "treebank.h"

namespace docling {

class TextManager {
public:
  TextManager();

  std::vector<std::string> tokenize(const std::string &text, bool convert_parentheses = false);

private:
  TreeBankTokenizer tokenizer_;
};

} // namespace docling
