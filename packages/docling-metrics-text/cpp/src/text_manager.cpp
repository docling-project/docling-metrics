#include <memory>

#include "edlib.h"

#include "text_manager.h"

namespace docling {

TextManager::TextManager()
    : ed_config_ptr_(std::make_unique<EdlibAlignConfig>(edlibDefaultAlignConfig())) {}

std::vector<std::string> TextManager::tokenize(const std::string &text, bool convert_parentheses) {
  // The tokenization should be:
  // 1. PunktTokenizer: Cuts text into sentences.
  // 2. TreeBankTokenizer: Cuts sentences into tokens.

  // TODO: This is an INCOMPLETE tokenization as it calls only the TreeBank tokenizer
  return treebank_tokenizer_.tokenize(text, convert_parentheses);
}

double TextManager::edit_distance(const std::vector<std::string> &tokens_a,
                                  const std::vector<std::string> &tokens_b) {
  EdlibAlignResult result = edlibAlignStrings(tokens_a, tokens_b, *ed_config_ptr_);
  int maxLen = std::max(static_cast<int>(tokens_a.size()), static_cast<int>(tokens_b.size()));
  double normalized = (maxLen > 0) ? static_cast<double>(result.editDistance) / maxLen : 0.0;
  edlibFreeAlignResult(result);
  return normalized;
}

} // namespace docling
