#include "text_manager.h"

#include "edit_distance.h"

namespace docling {

std::vector<std::string> TextManager::tokenize(const std::string &text, bool convert_parentheses) {
  // The tokenization should be:
  // 1. PunktTokenizer: Cuts text into sentences.
  // 2. TreeBankTokenizer: Cuts sentences into tokens.

  // TODO: This is an INCOMPLETE tokenization as it calls only the TreeBank tokenizer
  return treebank_tokenizer_.tokenize(text, convert_parentheses);
}

double TextManager::edit_distance(const std::vector<std::string> &tokens_a,
                                  const std::vector<std::string> &tokens_b) {
  return docling::edit_distance(tokens_a, tokens_b);
}

} // namespace docling
