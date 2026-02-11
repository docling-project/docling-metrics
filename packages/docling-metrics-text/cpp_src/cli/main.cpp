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

void demo_tokenizer() {
  std::string text = "Good muffins cost $3.88 (roughly 3,36 euros)\nin New York.  Please buy "
                     "me\ntwo of them.\nThanks.";
  docling::TreeBankTokenizer tokenizer;
  std::vector<std::string> tokens = tokenizer.tokenize(text);

  std::cout << "Text: \n" << text;
  std::cout << "\n\nTokens: \n";
  for (const std::string &token : tokens) {
    std::cout << token << " ";
  }
}

int main(int argc, char *argv[]) {
  // demo_regex();
  demo_tokenizer();

  return 0;
}
