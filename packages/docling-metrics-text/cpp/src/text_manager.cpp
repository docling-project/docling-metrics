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
  // TODO: Extend the implementation of edlibAlign from edlib code to accept vectors of strings:
  // - Each token should be mapped to a uint64_t using a lookup map
  // - Check Mayer's bit-vector algorithm

  return -1.;
}

} // namespace docling
