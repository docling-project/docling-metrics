#include <cassert>
#include <iostream>
#include <string>
#include <vector>

#include "treebank.h"

void test_tokenizer() {
  std::string text = "Good muffins cost $3.88 (roughly 3,36 euros)\nin New York.  Please buy "
                     "me\ntwo of them.\nThanks.";
  std::vector<std::string> expected_tokens{
      "Good", "muffins", "cost",   "$",   "3.88", "(",   "roughly", "3,36",  "euros",  ")", "in",
      "New",  "York.",   "Please", "buy", "me",   "two", "of",      "them.", "Thanks", "."};
  std::vector<std::string> expected_tokens_without_parentheses{
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

  std::vector<std::string> tokens_without_parentheses = tokenizer.tokenize(text, true);
  std::cout << "\n\nTokens with parentheses: \n";
  for (int i = 0; i < tokens_without_parentheses.size(); ++i) {
    std::cout << i << ": " << tokens_without_parentheses[i] << "\n";
  }

  std::cout << "Testing if tokens with parentheses match: ";
  assert(expected_tokens_without_parentheses.size() == tokens_without_parentheses.size() &&
         "Mismatch in the produced tokens with parentheses");
  for (int i = 0; i < tokens_without_parentheses.size(); ++i) {
    assert(tokens_without_parentheses[i] == expected_tokens_without_parentheses[i] &&
           ("Mismatch in the token with parentheses: " + std::to_string(i)).c_str());
  }
  std::cout << "OK!\n";
}

int main(int argc, char *argv[]) {
  test_tokenizer();

  return 0;
}
