#include "text_manager.h"
#include "utils.h"

namespace docling {

TextManager::TextManager(const std::string &level) {
  std::string lower_level = level;
  std::transform(lower_level.begin(), lower_level.end(), lower_level.begin(),
                 [](unsigned char c) { return std::tolower(c); });
  set_loglevel(lower_level);
}

std::vector<std::string> TextManager::tokenize(const std::string &text, bool convert_parentheses) {
  // The tokenization should be:
  // 1. PunktTokenizer: Cuts text into sentences.
  // 2. TreeBankTokenizer: Cuts sentences into tokens.

  // TODO: This is an INCOMPLETE tokenization as it calls only the TreeBank tokenizer
  return treebank_tokenizer_.tokenize(text, convert_parentheses);
}

double TextManager::edit_distance(const std::vector<std::string> &tokens_a,
                                  const std::vector<std::string> &tokens_b) {
  return ed_calculator_.edit_distance(tokens_a, tokens_b);
}

} // namespace docling
