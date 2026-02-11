#include <iostream>
#include <string>
#include <vector>

#include "re2/re2.h"

#include "treebank.h"

void demo_regex() {
  int i;
  std::string s;
  RE2 re("(\\w+):(\\d+)");
  assert(re.ok()); // compiled; if not, see re.error();

  assert(RE2::FullMatch("ruby:1234", re, &s, &i));
  assert(RE2::FullMatch("ruby:1234", re, &s));
  assert(RE2::FullMatch("ruby:1234", re, (void *)NULL, &i));
  assert(!RE2::FullMatch("ruby:123456789123", re, &s, &i));
}

void test_tokenizer() {
  std::string text = "Good muffins cost $3.88 (roughly 3,36 euros)\nin New York.  Please buy "
                     "me\ntwo of them.\nThanks.";
  std::vector<std::string> expected_tokens{
      "Good", "muffins", "cost",   "$",   "3.88", "(",   "roughly", "3,36",  "euros",  ")", "in",
      "New",  "York.",   "Please", "buy", "me",   "two", "of",      "them.", "Thanks", "."};
  std::vector<std::string> expected_tokens_with_parenthesis{
      "Good", "muffins", "cost",  "$",  "3.88",  "-LRB-",  "roughly",
      "3,36", "euros",   "-RRB-", "in", "New",   "York.",  "Please",
      "buy",  "me",      "two",   "of", "them.", "Thanks", "."};

  docling::TreeBankTokenizer tokenizer;
  std::vector<std::string> tokens = tokenizer.tokenize(text);

  // Print tokens
  std::cout << "Text: \n" << text;
  std::cout << "\n\nTokens: \n";
  for (int i = 0; i < tokens.size(); ++i) {
    std::cout << i << ": " << tokens[i] << "\n";
  }

  // Assert the tokens
  std::cout << "Testing if tokens match: ";
  assert(expected_tokens.size() == tokens.size() && "Mismatch in the produced tokens");
  for (int i = 0; i < tokens.size(); ++i) {
    assert(tokens[i] == expected_tokens[i] &&
           ("Mismatch in the token: " + std::to_string(i)).c_str());
  }
  std::cout << "OK!\n";

  std::vector<std::string> tokens_with_parenthesis = tokenizer.tokenize(text, true);
  std::cout << "\n\nTokens with parenthesis: \n";
  for (int i = 0; i < tokens_with_parenthesis.size(); ++i) {
    std::cout << i << ": " << tokens_with_parenthesis[i] << "\n";
  }

  std::cout << "Testing if tokens with parenthesis match: ";
  assert(expected_tokens_with_parenthesis.size() == tokens_with_parenthesis.size() &&
         "Mismatch in the produced tokens with parenthesis");
  for (int i = 0; i < tokens_with_parenthesis.size(); ++i) {
    assert(tokens_with_parenthesis[i] == expected_tokens_with_parenthesis[i] &&
           ("Mismatch in the token with parenthesis: " + std::to_string(i)).c_str());
  }
  std::cout << "OK!\n";
}

int main(int argc, char *argv[]) {
  // demo_regex();
  test_tokenizer();

  return 0;
}
