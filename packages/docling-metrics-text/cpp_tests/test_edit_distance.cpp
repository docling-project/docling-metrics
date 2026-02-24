#include <cassert>
#include <cmath>
#include <iostream>
#include <random>
#include <string>
#include <vector>

#include "text_manager.h"

static void assert_near(double actual, double expected, double tol, const char *label) {
  if (std::fabs(actual - expected) > tol) {
    std::cerr << label << ": expected " << expected << ", got " << actual << "\n";
    assert(false);
  }
}

void test_identical_tokens() {
  docling::TextManager tm;
  std::vector<std::string> tokens = {"hello", "world"};
  double dist = tm.edit_distance(tokens, tokens);
  std::cout << "test_identical_tokens: dist=" << dist << "\n";
  assert_near(dist, 0.0, 1e-9, "identical tokens");
  std::cout << "  OK!\n";
}

void test_completely_different() {
  docling::TextManager tm;
  std::vector<std::string> a = {"a", "b", "c"};
  std::vector<std::string> b = {"d", "e", "f"};
  double dist = tm.edit_distance(a, b);
  // All 3 tokens differ -> edit distance = 3, normalized = 3/3 = 1.0
  std::cout << "test_completely_different: dist=" << dist << "\n";
  assert_near(dist, 1.0, 1e-9, "completely different");
  std::cout << "  OK!\n";
}

void test_one_insertion() {
  docling::TextManager tm;
  std::vector<std::string> a = {"the", "cat"};
  std::vector<std::string> b = {"the", "big", "cat"};
  double dist = tm.edit_distance(a, b);
  // edit distance = 1, max len = 3, normalized = 1/3
  std::cout << "test_one_insertion: dist=" << dist << "\n";
  assert_near(dist, 1.0 / 3.0, 1e-9, "one insertion");
  std::cout << "  OK!\n";
}

void test_one_deletion() {
  docling::TextManager tm;
  std::vector<std::string> a = {"the", "big", "cat"};
  std::vector<std::string> b = {"the", "cat"};
  double dist = tm.edit_distance(a, b);
  // edit distance = 1, max len = 3, normalized = 1/3
  std::cout << "test_one_deletion: dist=" << dist << "\n";
  assert_near(dist, 1.0 / 3.0, 1e-9, "one deletion");
  std::cout << "  OK!\n";
}

void test_one_substitution() {
  docling::TextManager tm;
  std::vector<std::string> a = {"the", "cat", "sat"};
  std::vector<std::string> b = {"the", "dog", "sat"};
  double dist = tm.edit_distance(a, b);
  // edit distance = 1, max len = 3, normalized = 1/3
  std::cout << "test_one_substitution: dist=" << dist << "\n";
  assert_near(dist, 1.0 / 3.0, 1e-9, "one substitution");
  std::cout << "  OK!\n";
}

void test_empty_both() {
  docling::TextManager tm;
  std::vector<std::string> a;
  std::vector<std::string> b;
  double dist = tm.edit_distance(a, b);
  std::cout << "test_empty_both: dist=" << dist << "\n";
  assert_near(dist, 0.0, 1e-9, "both empty");
  std::cout << "  OK!\n";
}

void test_empty_one() {
  docling::TextManager tm;
  std::vector<std::string> a;
  std::vector<std::string> b = {"hello", "world"};
  double dist = tm.edit_distance(a, b);
  // edit distance = 2, max len = 2, normalized = 1.0
  std::cout << "test_empty_one: dist=" << dist << "\n";
  assert_near(dist, 1.0, 1e-9, "one empty");
  std::cout << "  OK!\n";
}

void test_single_token_match() {
  docling::TextManager tm;
  std::vector<std::string> a = {"hello"};
  std::vector<std::string> b = {"hello"};
  double dist = tm.edit_distance(a, b);
  std::cout << "test_single_token_match: dist=" << dist << "\n";
  assert_near(dist, 0.0, 1e-9, "single token match");
  std::cout << "  OK!\n";
}

void test_single_token_mismatch() {
  docling::TextManager tm;
  std::vector<std::string> a = {"hello"};
  std::vector<std::string> b = {"world"};
  double dist = tm.edit_distance(a, b);
  // edit distance = 1, max len = 1, normalized = 1.0
  std::cout << "test_single_token_mismatch: dist=" << dist << "\n";
  assert_near(dist, 1.0, 1e-9, "single token mismatch");
  std::cout << "  OK!\n";
}

void test_long_sequence() {
  std::cout << "test_long_sequence\n";
  int num_tokens = 100000; // 100k tokens
  int token_size = 20;

  // Generate input_a: num_tokens random strings of length token_size.
  std::mt19937 rng(42);
  std::uniform_int_distribution<int> char_dist('a', 'z');

  std::cout << "Generating input sequence A";
  std::cout << " (num_tokens=" << num_tokens << ", token_size=" << token_size << ") ...\n";
  std::vector<std::string> input_a;
  input_a.reserve(num_tokens);
  for (int i = 0; i < num_tokens; ++i) {
    std::string token(token_size, ' ');
    for (int j = 0; j < token_size; ++j) {
      token[j] = static_cast<char>(char_dist(rng));
    }
    input_a.push_back(std::move(token));
  }
  std::cout << "Input sequence A ready\n";

  // Compute edit distance for input_a vs input_a. Should be 0.
  docling::TextManager tm;
  double dist_same = tm.edit_distance(input_a, input_a);
  std::cout << "test_long_sequence (same): dist=" << dist_same << "\n";
  assert_near(dist_same, 0.0, 1e-9, "long sequence identical");
  std::cout << "  OK!\n";

  // Generate input_b by altering the first character of each token in input_a.
  // This ensures every token in input_b differs from the corresponding token in input_a.
  std::cout << "Generating input sequence B ...\n";
  std::vector<std::string> input_b = input_a;
  for (int i = 0; i < num_tokens; ++i) {
    char c = input_b[i][0];
    input_b[i][0] = (c == 'z') ? 'a' : c + 1;
  }
  std::cout << "Input sequence A ready\n";

  // All tokens in input_a and input_b are unique random strings, so no token
  // from input_b matches any token in input_a. Edit distance = num_tokens,
  // normalized = num_tokens / max(num_tokens, num_tokens) = 1.0.
  double dist_diff = tm.edit_distance(input_a, input_b);
  std::cout << "test_long_sequence (different): dist=" << dist_diff << "\n";
  assert_near(dist_diff, 1.0, 1e-9, "long sequence all different");
  std::cout << "  OK!\n";
}

int main(int argc, char *argv[]) {
  test_identical_tokens();
  test_completely_different();
  test_one_insertion();
  test_one_deletion();
  test_one_substitution();
  test_empty_both();
  test_empty_one();
  test_single_token_match();
  test_single_token_mismatch();
  test_long_sequence();

  std::cout << "\nAll edit_distance tests passed!\n";
  return 0;
}
