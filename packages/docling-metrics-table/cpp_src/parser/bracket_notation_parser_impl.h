// The MIT License (MIT)
// Copyright (c) 2017 Mateusz Pawlik, Nikolaus Augsten, and Daniel Kocher.
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

/// \file parser/bracket_notation_parser_impl.h
///
/// \details
/// Contains the implementation of the BracketNotationParser class.

#pragma once

/// This is currently a copy of the previous version but with the efficient
/// tokanization.
template <class Label>
node::Node<Label> BracketNotationParser<Label>::parse_single(const std::string &tree_string) {

  std::vector<std::string> tokens = get_tokens(tree_string);

  // Ensure that malformed input stops here
  if (!validate_tokens(tree_string, tokens)) {
    throw std::invalid_argument("Malformed bracket notation: '" + tree_string + "'");
  }

  // A stack to store nodes on a path to the root from the current node in the parsing process.
  std::vector<std::reference_wrapper<node::Node<Label>>> node_stack;

  // Tokenize the input string - get iterator over tokens.
  auto tokens_begin = tokens.begin();
  auto tokens_end = tokens.end();

  // Deal with the root node separately.
  ++tokens_begin; // Advance tokens to label.
  if (tokens_begin == tokens_end) {
    throw std::invalid_argument("Truncated bracket notation: '" + tree_string + "'");
  }
  std::string match_str = *tokens_begin;
  if (match_str == kLeftBracket || match_str == kRightBracket) { // Root has an empty label.
    match_str = "";
    // Do not advance tokens - we're already at kLeftBracket or kRightBracket.
  } else {          // Non-empty label.
    ++tokens_begin; // Advance tokens.
  }
  Label root_label(match_str);
  node::Node<Label> root(root_label);
  node_stack.push_back(std::ref(root));

  bool consumed_token = false;

  // Iterate all remaining tokens.
  while (tokens_begin != tokens_end) {
    match_str = *tokens_begin;
    consumed_token = false;

    if (match_str == kLeftBracket) { // Enter node.
      consumed_token = true;
      ++tokens_begin; // Advance tokens to label.
      if (tokens_begin == tokens_end) {
        throw std::invalid_argument("Truncated bracket notation: '" + tree_string + "'");
      }
      match_str = *tokens_begin;

      if (match_str == kLeftBracket || match_str == kRightBracket) { // Node has an empty label.
        match_str = "";
        // Do not advance tokens - we're already at kLeftBracket or kRightBracket.
      } else {          // Non-empty label.
        ++tokens_begin; // Advance tokens.
      }

      // Create new node.
      Label node_label(match_str);
      node::Node<Label> n(node_label);

      // Move n to become a child.
      // Return reference from add_child to the 'new-located' object.
      // Put a reference to just-moved n (last child of its parent) on a stack.
      if (node_stack.empty()) {
        throw std::invalid_argument("Unbalanced bracket notation: '" + tree_string + "'");
      }
      node_stack.push_back(std::ref(node_stack.back().get().add_child(n)));
    }

    if (match_str == kRightBracket) { // Exit node.
      consumed_token = true;
      if (node_stack.empty()) {
        throw std::invalid_argument("Unbalanced bracket notation: '" + tree_string + "'");
      }
      node_stack.pop_back();
      ++tokens_begin; // Advance tokens.
    }

    // Skip incorrect token.
    if (consumed_token == false) {
      ++tokens_begin; // Advance tokens.
    }
  }
  return root;
}

template <class Label>
void BracketNotationParser<Label>::parse_collection(
    std::vector<node::Node<Label>> &trees_collection, const std::string &file_path) {
  std::ifstream trees_file(file_path);
  if (!trees_file) {
    throw std::runtime_error("ERROR: Problem with opening the file '" + file_path +
                             "' in BracketNotationParser::parse_collection_efficient.");
  }
  // Read the trees line by line, parse, and move into the container.
  std::string tree_string;
  while (std::getline(trees_file, tree_string)) {
    // parse_single validates the input itself, so a separate validate_input call here would
    // only tokenize every line twice. Malformed lines are skipped, as before.
    try {
      trees_collection.push_back(parse_single(
          tree_string)); // -> This invokes a move constructor (due to push_back(<rvalue>)).
    } catch (const std::invalid_argument &) {
      continue;
    }
  }
  trees_file.close();
}

/// This is only a tokanizer that returns a vector with correct tokens.
template <class Label>
std::vector<std::string>
BracketNotationParser<Label>::get_tokens(const std::string &tree_string) const {
  std::vector<std::string> tokens;

  // Get pointer to the structure elements.
  const char *s_elems = kStructureElements.c_str();

  // Get pointer to the beginning of the input string.
  const char *begin = tree_string.c_str();
  // Pointer to the beginning of consecutive searches.
  const char *next_begin = begin;
  // Remember iter from previous iteration in old_iter - for label begin.
  const char *old_iter = begin;
  // iter is a pointer to consecutive occurences of either '{' or '}'.
  for (const char *iter = strpbrk(next_begin, s_elems); iter != NULL;
       iter = strpbrk(next_begin, s_elems)) {
    // Next iteration will start from the position right of iter.
    next_begin = iter + 1;
    // Count the consecutive escape characters just before the found position. The bracket
    // belongs to a label only if that count is odd - an even count means the escapes escape
    // each other and the bracket itself is a structure element.
    size_t escapes = 0;
    while (escapes < static_cast<size_t>(iter - begin) && *(iter - 1 - escapes) == kEscapeChar) {
      ++escapes;
    }
    if (escapes % 2 == 1) {
      continue;
    }
    // If there is something between two consecutive brackets, it's potentially
    // a label - record it.
    if (iter > old_iter + 1) {
      tokens.push_back(typename std::vector<std::string>::value_type(
          old_iter + 1, iter)); // Calls the allocator of string.
    }
    // Record the found bracket.
    tokens.push_back(typename std::vector<std::string>::value_type(
        iter, iter + 1)); // Calls the allocator of string.
    old_iter = iter;
  }

  return tokens;
}

template <class Label>
bool BracketNotationParser<Label>::validate_input(const std::string &tree_string) const {
  return validate_tokens(tree_string, get_tokens(tree_string));
}

template <class Label>
bool BracketNotationParser<Label>::validate_tokens(const std::string &tree_string,
                                                   const std::vector<std::string> &tokens) const {

  // Rule 1: Text outside the outermost brackets is never tokenized, so it has to be caught on
  // the raw string. Whitespace around the tree is tolerated, anything else is not. A string
  // without any non-whitespace character fails here as well.
  const size_t first = tree_string.find_first_not_of(" \t\n\r\f\v");
  const size_t last = tree_string.find_last_not_of(" \t\n\r\f\v");
  if (first == std::string::npos || tree_string[first] != kLeftBracket[0] ||
      tree_string[last] != kRightBracket[0]) {
    return false;
  }

  // Rule 2: The first token opens the root.
  if (tokens.empty() || tokens.front() != kLeftBracket) {
    return false;
  }

  int depth = 0;
  int node_counter = 0;
  bool root_closed = false;
  bool expect_label = false; // A label is legal only right after kLeftBracket.

  for (const auto &token : tokens) {
    if (token == kLeftBracket) {
      // Rule 5: Nothing may open after the root has closed.
      if (root_closed) {
        return false;
      }
      ++depth;
      ++node_counter;
      expect_label = true;
    } else if (token == kRightBracket) {
      // Rule 4: A closing bracket needs an open node.
      if (depth == 0) {
        return false;
      }
      --depth;
      if (depth == 0) {
        root_closed = true;
      }
      expect_label = false;
    } else {
      // Rule 3: Any other token is a label, and a label may only follow kLeftBracket.
      if (!expect_label) {
        return false;
      }
      expect_label = false;
    }
  }

  // Rule 6: The tree is closed and holds at least one node.
  return depth == 0 && node_counter > 0;
}
