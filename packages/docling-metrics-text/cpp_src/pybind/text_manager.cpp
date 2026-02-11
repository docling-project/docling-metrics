#include "text_manager.h"

namespace docling {

TextManager::TextManager() {}

std::vector<std::string> TextManager::tokenize(const std::string &text, bool convert_parentheses) {
  return tokenizer_.tokenize(text, convert_parentheses);
}

} // namespace docling
