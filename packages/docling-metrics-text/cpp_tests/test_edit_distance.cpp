#include <cassert>
#include <cmath>
#include <iostream>
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

void test_longer_sequence() {
  docling::TextManager tm;
  std::vector<std::string> a = {"the", "quick", "brown", "fox", "jumps"};
  std::vector<std::string> b = {"the", "slow", "brown", "fox", "sits"};
  double dist = tm.edit_distance(a, b);
  // 2 substitutions (quick->slow, jumps->sits), edit distance = 2, max len = 5
  std::cout << "test_longer_sequence: dist=" << dist << "\n";
  assert_near(dist, 2.0 / 5.0, 1e-9, "longer sequence");
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
  test_longer_sequence();

  std::cout << "\nAll edit_distance tests passed!\n";
  return 0;
}
