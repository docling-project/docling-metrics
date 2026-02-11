#pragma once
#include <string>
#include <vector>

#include "treebank.h"

namespace docling {

class TextManager {
public:
  TextManager();

  /**
   * Implementation of the TreeBankTokenizer using regular expressions
   * The logic is ported from the NLTK tokenizer
   * The implementation is based on the RE2 regex library
   *
   */
  std::vector<std::string> tokenize(const std::string &text, bool convert_parentheses);

private:
  TreeBankTokenizer tokenizer_;
};

} // namespace docling
