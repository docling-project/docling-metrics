#pragma once
#include <memory>
#include <string>
#include <vector>

#include "edlib.h"
#include "treebank.h"

namespace docling {

class TextManager {
public:
  TextManager();

  std::vector<std::string> tokenize(const std::string &text, bool convert_parentheses);

  double edit_distance(const std::vector<std::string> &tokens_a,
                       const std::vector<std::string> &tokens_b);

private:
  TreeBankTokenizer treebank_tokenizer_;
  std::unique_ptr<EdlibAlignConfig> ed_config_ptr_;
};

} // namespace docling
