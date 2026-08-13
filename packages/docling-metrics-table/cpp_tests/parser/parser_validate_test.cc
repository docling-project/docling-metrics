#include <fstream>
#include <iostream>
#include <string>
#include <vector>

#include "bracket_notation_parser.h"
#include "node.h"
#include "string_label.h"

using Label = label::StringLabel;

/// Check one input against the expected verdict of validate_input.
///
/// \param input Tree in bracket notation.
/// \param expected True if the input is well formed.
/// \param description What the case is about, printed on failure.
/// \return True if validate_input agreed with expected.
bool check(const std::string &input, bool expected, const std::string &description) {
  parser::BracketNotationParser<Label> bnp;
  bool computed = bnp.validate_input(input);
  if (computed != expected) {
    std::cerr << "Wrong verdict for " << description << ": got "
              << (computed ? "valid" : "invalid") << " instead of "
              << (expected ? "valid" : "invalid") << std::endl;
    std::cerr << "Input: '" << input << "'" << std::endl;
    return false;
  }
  // A well formed input must parse without throwing, a malformed one must be rejected before
  // the parsing loop is reached.
  try {
    node::Node<Label> t = bnp.parse_single(input);
    if (!expected) {
      std::cerr << "parse_single accepted the malformed input '" << input << "' and built "
                << t.get_tree_size() << " node(s)" << std::endl;
      return false;
    }
  } catch (const std::invalid_argument &e) {
    if (expected) {
      std::cerr << "parse_single rejected the well formed input '" << input
                << "': " << e.what() << std::endl;
      return false;
    }
  }
  return true;
}

int main() {

  std::cout << "Validation test." << std::endl;

  bool passed = true;

  // Whitespace sensitive cases are kept here rather than in the data file, where leading and
  // trailing spaces would not survive an editor or a formatter.
  passed &= check("", false, "the empty string");
  passed &= check("   ", false, "a whitespace only string");
  passed &= check(" {a} ", true, "whitespace around the root");
  passed &= check("{a}\n", true, "a trailing newline");
  passed &= check("{a}\r", true, "a trailing carriage return, as left by getline on CRLF files");
  passed &= check("{ {} }", false, "whitespace inside the root, which becomes a stray label");

  // Parse the remaining test cases from file.
  std::ifstream test_cases_file("parser_validate_test_data.txt");

  if (!test_cases_file) {
    std::cerr << "ERROR: Problem reading the test file." << std::endl;
    return -1;
  }

  for (std::string line; std::getline(test_cases_file, line);) {
    if (line[0] == '#') {
      std::string description = line.substr(1);
      std::getline(test_cases_file, line);
      std::string input_tree = line;
      std::getline(test_cases_file, line);
      std::string correct_result = line;

      if (correct_result != "valid" && correct_result != "invalid") {
        std::cerr << "Bad test data, expected 'valid' or 'invalid' but found '" << correct_result
                  << "'" << std::endl;
        return -1;
      }
      passed &= check(input_tree, correct_result == "valid", description);
    }
  }

  return passed ? 0 : -1;
}
