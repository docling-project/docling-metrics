#pragma once
#include <string>
#include <utility>
#include <vector>

namespace docling {

class TreeBankTokenizer {
public:
  TreeBankTokenizer();

  std::vector<std::string> tokenize(const std::string &text, bool convert_parentheses = false);

private:
  // Pattern pairs: (regex_pattern, replacement)
  std::vector<std::pair<std::string, std::string>> starting_quotes_;
  std::vector<std::pair<std::string, std::string>> punctuation_;
  std::vector<std::pair<std::string, std::string>> ending_quotes_;
  std::vector<std::pair<std::string, std::string>> convert_parentheses_;

  std::pair<std::string, std::string> parens_brackets_;
  std::pair<std::string, std::string> double_dashes_;

  // Contraction patterns (only patterns, replacement is fixed)
  std::vector<std::string> contractions2_;
  std::vector<std::string> contractions3_;
};

} // namespace docling