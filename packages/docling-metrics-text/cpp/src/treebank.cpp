#include <memory>
#include <sstream>
#include <string>
#include <vector>

#include "treebank.h"
#include <re2/re2.h>

namespace docling {

TreeBankTokenizer::TreeBankTokenizer() {
  // Starting quotes - compile regex patterns
  starting_quotes_.emplace_back(std::make_unique<re2::RE2>(R"(^")", re2::RE2::Quiet), "``");
  starting_quotes_.emplace_back(std::make_unique<re2::RE2>(R"((``))", re2::RE2::Quiet), R"( \1 )");
  starting_quotes_.emplace_back(
      std::make_unique<re2::RE2>(R"(([ \(\[{<])("|\'{2}))", re2::RE2::Quiet), R"(\1 `` )");

  // Punctuation
  punctuation_.emplace_back(std::make_unique<re2::RE2>(R"(([:,])([^\d]))", re2::RE2::Quiet),
                            R"( \1 \2)");
  punctuation_.emplace_back(std::make_unique<re2::RE2>(R"(([:,])$)", re2::RE2::Quiet), R"( \1 )");
  punctuation_.emplace_back(std::make_unique<re2::RE2>(R"(\.\.\.)", re2::RE2::Quiet), R"( ... )");
  punctuation_.emplace_back(std::make_unique<re2::RE2>(R"([;@#$%&])", re2::RE2::Quiet), R"( \0 )");
  punctuation_.emplace_back(
      std::make_unique<re2::RE2>(R"(([^\.])(\.)([\]\)}>"\']*)\s*$)", re2::RE2::Quiet),
      R"(\1 \2\3 )");
  punctuation_.emplace_back(std::make_unique<re2::RE2>(R"([?!])", re2::RE2::Quiet), R"( \0 )");
  punctuation_.emplace_back(std::make_unique<re2::RE2>(R"(([^'])' )", re2::RE2::Quiet), R"(\1 ' )");

  // Parentheses and brackets
  parens_brackets_ = {std::make_unique<re2::RE2>(R"([\]\[\(\)\{\}\<\>])", re2::RE2::Quiet),
                      R"( \0 )"};

  // Convert parentheses (optional)
  convert_parentheses_.emplace_back(std::make_unique<re2::RE2>(R"(\()", re2::RE2::Quiet), "-LRB-");
  convert_parentheses_.emplace_back(std::make_unique<re2::RE2>(R"(\))", re2::RE2::Quiet), "-RRB-");
  convert_parentheses_.emplace_back(std::make_unique<re2::RE2>(R"(\[)", re2::RE2::Quiet), "-LSB-");
  convert_parentheses_.emplace_back(std::make_unique<re2::RE2>(R"(\])", re2::RE2::Quiet), "-RSB-");
  convert_parentheses_.emplace_back(std::make_unique<re2::RE2>(R"(\{)", re2::RE2::Quiet), "-LCB-");
  convert_parentheses_.emplace_back(std::make_unique<re2::RE2>(R"(\})", re2::RE2::Quiet), "-RCB-");

  // Double dashes
  double_dashes_ = {std::make_unique<re2::RE2>(R"(--)", re2::RE2::Quiet), R"( -- )"};

  // Ending quotes
  ending_quotes_.emplace_back(std::make_unique<re2::RE2>(R"('')", re2::RE2::Quiet), " '' ");
  ending_quotes_.emplace_back(std::make_unique<re2::RE2>(R"(")", re2::RE2::Quiet), " '' ");
  ending_quotes_.emplace_back(
      std::make_unique<re2::RE2>(R"(([^' ])('[sS]|'[mM]|'[dD]|') )", re2::RE2::Quiet), R"(\1 \2 )");
  ending_quotes_.emplace_back(
      std::make_unique<re2::RE2>(R"(([^' ])('ll|'LL|'re|'RE|'ve|'VE|n't|N'T) )", re2::RE2::Quiet),
      R"(\1 \2 )");

  // Contractions (case-insensitive)
  // Note: RE2 doesn't support lookaheads, so we adjust patterns
  contractions2_.emplace_back(std::make_unique<re2::RE2>(R"((?i)\b(can)(not)\b)", re2::RE2::Quiet));
  contractions2_.emplace_back(std::make_unique<re2::RE2>(R"((?i)\b(d)('ye)\b)", re2::RE2::Quiet));
  contractions2_.emplace_back(std::make_unique<re2::RE2>(R"((?i)\b(gim)(me)\b)", re2::RE2::Quiet));
  contractions2_.emplace_back(std::make_unique<re2::RE2>(R"((?i)\b(gon)(na)\b)", re2::RE2::Quiet));
  contractions2_.emplace_back(std::make_unique<re2::RE2>(R"((?i)\b(got)(ta)\b)", re2::RE2::Quiet));
  contractions2_.emplace_back(std::make_unique<re2::RE2>(R"((?i)\b(lem)(me)\b)", re2::RE2::Quiet));
  contractions2_.emplace_back(std::make_unique<re2::RE2>(R"((?i)\b(more)('n)\b)", re2::RE2::Quiet));
  contractions2_.emplace_back(std::make_unique<re2::RE2>(R"((?i)\b(wan)(na)\s)", re2::RE2::Quiet));

  contractions3_.emplace_back(std::make_unique<re2::RE2>(R"((?i) ('t)(is)\b)", re2::RE2::Quiet));
  contractions3_.emplace_back(std::make_unique<re2::RE2>(R"((?i) ('t)(was)\b)", re2::RE2::Quiet));
}

/**
 * Implementation of the TreeBankTokenizer using regular expressions
 * The logic is ported from the NLTK tokenizer
 * The implementation is based on the RE2 regex library
 */
std::vector<std::string> TreeBankTokenizer::tokenize(const std::string &text,
                                                     bool convert_parentheses) {
  std::string result = text;

  // Apply starting quotes
  for (const auto &pair : starting_quotes_) {
    re2::RE2::GlobalReplace(&result, *pair.first, pair.second);
  }

  // Apply punctuation rules
  for (const auto &pair : punctuation_) {
    re2::RE2::GlobalReplace(&result, *pair.first, pair.second);
  }

  // Handle parentheses and brackets
  re2::RE2::GlobalReplace(&result, *parens_brackets_.first, parens_brackets_.second);

  // Optionally convert parentheses
  if (convert_parentheses) {
    for (const auto &pair : convert_parentheses_) {
      re2::RE2::GlobalReplace(&result, *pair.first, pair.second);
    }
  }

  // Handle double dashes
  re2::RE2::GlobalReplace(&result, *double_dashes_.first, double_dashes_.second);

  // Add extra space to make things easier
  result = " " + result + " ";

  // Apply ending quotes
  for (const auto &pair : ending_quotes_) {
    re2::RE2::GlobalReplace(&result, *pair.first, pair.second);
  }

  // Apply contractions2
  for (const auto &regex : contractions2_) {
    re2::RE2::GlobalReplace(&result, *regex, R"( \1 \2 )");
  }

  // Apply contractions3
  for (const auto &regex : contractions3_) {
    re2::RE2::GlobalReplace(&result, *regex, R"( \1 \2 )");
  }

  // Split by whitespace
  std::vector<std::string> tokens;
  std::istringstream iss(result);
  std::string token;
  while (iss >> token) {
    tokens.push_back(token);
  }

  return tokens;
}

} // namespace docling
