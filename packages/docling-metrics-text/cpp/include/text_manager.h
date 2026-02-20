#pragma once
#include <string>
#include <vector>

#include "edit_distance.h"
#include "treebank.h"

namespace docling {

class TextManager {
public:
  std::vector<std::string> tokenize(const std::string &text, bool convert_parentheses);

  double edit_distance(const std::vector<std::string> &tokens_a,
                       const std::vector<std::string> &tokens_b);

private:
  TreeBankTokenizer treebank_tokenizer_;
  EditDistanceCalculator ed_calculator_;
};

} // namespace docling
