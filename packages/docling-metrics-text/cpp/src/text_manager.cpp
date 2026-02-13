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
  // int text_a_size = text_a.size();
  // int text_b_size = text_b.size();

  // EdlibAlignResult result =
  //     edlibAlign(text_a.c_str(), text_a.size(), text_b.c_str(), text_b.size(), *ed_config_ptr_);

  // if (result.status != EDLIB_STATUS_OK) {
  //   return -1.0;
  // }

  // int levenshtein = result.editDistance;
  // int max_length = std::max(tokens_a_size, len(tokens_b))
  // edlibFreeAlignResult(result);

  return -1.;
}

} // namespace docling
