#include <sstream>
#include <string>
#include <vector>

#include "treebank.h"
#include <re2/re2.h>

namespace docling {

TreeBankTokenizer::TreeBankTokenizer() {
  // TODO: Compile the regexes

  // Starting quotes
  starting_quotes_.push_back({R"(^")", "``"});
  starting_quotes_.push_back({R"((``))", R"( \1 )"});
  starting_quotes_.push_back({R"(([ \(\[{<])("|\'{2}))", R"(\1 `` )"});

  // Punctuation
  punctuation_.push_back({R"(([:,])([^\d]))", R"( \1 \2)"});
  punctuation_.push_back({R"(([:,])$)", R"( \1 )"});
  punctuation_.push_back({R"(\.\.\.)", R"( ... )"});
  punctuation_.push_back({R"([;@#$%&])", R"( \0 )"});
  punctuation_.push_back({R"(([^\.])(\.)([\]\)}>"\']*)\s*$)", R"(\1 \2\3 )"});
  punctuation_.push_back({R"([?!])", R"( \0 )"});
  punctuation_.push_back({R"(([^'])' )", R"(\1 ' )"});

  // Parentheses and brackets
  parens_brackets_ = {R"([\]\[\(\)\{\}\<\>])", R"( \0 )"};

  // Convert parentheses (optional)
  convert_parentheses_.push_back({R"(\()", "-LRB-"});
  convert_parentheses_.push_back({R"(\))", "-RRB-"});
  convert_parentheses_.push_back({R"(\[)", "-LSB-"});
  convert_parentheses_.push_back({R"(\])", "-RSB-"});
  convert_parentheses_.push_back({R"(\{)", "-LCB-"});
  convert_parentheses_.push_back({R"(\})", "-RCB-"});

  // Double dashes
  double_dashes_ = {R"(--)", R"( -- )"};

  // Ending quotes
  ending_quotes_.push_back({R"('')", " '' "});
  ending_quotes_.push_back({R"(")", " '' "});
  ending_quotes_.push_back({R"(([^' ])('[sS]|'[mM]|'[dD]|') )", R"(\1 \2 )"});
  ending_quotes_.push_back({R"(([^' ])('ll|'LL|'re|'RE|'ve|'VE|n't|N'T) )", R"(\1 \2 )"});

  // TODO: Check it
  // Contractions (case-insensitive)
  // Note: RE2 doesn't support lookaheads, so we adjust patterns
  contractions2_.push_back(R"((?i)\b(can)(not)\b)");
  contractions2_.push_back(R"((?i)\b(d)('ye)\b)");
  contractions2_.push_back(R"((?i)\b(gim)(me)\b)");
  contractions2_.push_back(R"((?i)\b(gon)(na)\b)");
  contractions2_.push_back(R"((?i)\b(got)(ta)\b)");
  contractions2_.push_back(R"((?i)\b(lem)(me)\b)");
  contractions2_.push_back(R"((?i)\b(more)('n)\b)");
  contractions2_.push_back(R"((?i)\b(wan)(na)\s)"); // Changed from lookahead to explicit space

  contractions3_.push_back(R"((?i) ('t)(is)\b)");
  contractions3_.push_back(R"((?i) ('t)(was)\b)");
}

std::vector<std::string> TreeBankTokenizer::tokenize(const std::string &text,
                                                     bool convert_parentheses) {
  std::string result = text;

  // Apply starting quotes
  for (const auto &pair : starting_quotes_) {
    RE2::GlobalReplace(&result, pair.first, pair.second);
  }

  // Apply punctuation rules
  for (const auto &pair : punctuation_) {
    RE2::GlobalReplace(&result, pair.first, pair.second);
  }

  // Handle parentheses and brackets
  RE2::GlobalReplace(&result, parens_brackets_.first, parens_brackets_.second);

  // Optionally convert parentheses
  if (convert_parentheses) {
    for (const auto &pair : convert_parentheses_) {
      RE2::GlobalReplace(&result, pair.first, pair.second);
    }
  }

  // Handle double dashes
  RE2::GlobalReplace(&result, double_dashes_.first, double_dashes_.second);

  // Add extra space to make things easier
  result = " " + result + " ";

  // Apply ending quotes
  for (const auto &pair : ending_quotes_) {
    RE2::GlobalReplace(&result, pair.first, pair.second);
  }

  // Apply contractions2
  for (const auto &pattern : contractions2_) {
    RE2::GlobalReplace(&result, pattern, R"( \1 \2 )");
  }

  // Apply contractions3
  for (const auto &pattern : contractions3_) {
    RE2::GlobalReplace(&result, pattern, R"( \1 \2 )");
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