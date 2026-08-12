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

/// \file parser/bracket_notation_parser.h
///
/// \details
/// Implements the parser for bracket notation of the form:
///
/// {LABEL{LABEL}{LABEL}}
///
/// where LABEL allows any character BUT the the structure brackets (by default
/// the curly brackets: {}) must be escaped as follows: \{ \}.
///
/// Example input with complex labels:
/// {a{\{[b],\{key:"value"\}\}{}}}
/// which is a path of three nodes with labels as follows:
///
///                         target LABEL (after removing escapes):
/// a                       -> a
/// |
/// \{[b],\{key:"value"\}\} -> {[b],{key:"value"}}
/// |
/// ""                      -> an empty label
/// TODO: Should the matched label be cleaned by removing escapes?
/// TODO: This parses to StringLabel only. Should the label's type be assigned
///       based on user's choice?

#pragma once

#include "../label/string_label.h"
#include "../node/node.h"

#include <cstring>
#include <fstream>
#include <iostream>
#include <regex>
#include <stdexcept>
#include <string>

namespace parser {

template <class Label> class BracketNotationParser {

  // Member functions
public:
  /// Takes the string of a tree in bracket notation, parses it to the Node
  /// structure with StringLabels, and returns the root.
  ///
  /// \param tree_string The string holding the tree in bracket notation.
  ///
  /// \return Root of the parsed tree.
  node::Node<Label> parse_single(const std::string &tree_string);

  /// Takes a file with one tree (in bracket notation) per line and parses it
  /// to a vector of Node objects with StringLabels.
  ///
  /// NOTE: It executes parse_single for every line in the data file.
  /// NOTE: The notation of trees is assumed correct.
  ///
  /// \param trees_collection Container to store all trees.
  /// \param file_path The path to the file with set of trees.
  void parse_collection(std::vector<node::Node<Label>> &trees_collection,
                        const std::string &file_path);

  /// Generates the tokens for the input string.
  ///
  /// A bracket is a structure element unless it is escaped, that is, unless it is preceded
  /// by an odd number of consecutive escape characters. The escapes are kept in the label.
  ///
  /// \param tree_string The string holding the tree in bracket notation.
  /// \return Vector with all tokens.
  std::vector<std::string> get_tokens(const std::string &tree_string) const;

  /// Validates the bracket notation input.
  ///
  /// \param tree_string Tree in bracket notation.
  /// \return True if the input is correct and false otherwise.
  bool validate_input(const std::string &tree_string) const;

  // Member functions
private:
  /// Validates a tokenized tree.
  ///
  /// Needs the raw string as well as the tokens: text outside the outermost brackets is
  /// never tokenized, so it is invisible to a token-only check.
  ///
  /// \param tree_string Tree in bracket notation.
  /// \param tokens The tokens of tree_string, as returned by get_tokens.
  /// \return True if the input is correct and false otherwise.
  bool validate_tokens(const std::string &tree_string,
                       const std::vector<std::string> &tokens) const;

  // Member variables
private:
  /// Structure brackets for representing nodes relationships. Could be
  /// modified to other types of paretheses if necessary.
  const std::string kLeftBracket = "{";
  const std::string kRightBracket = "}";

  /// Structure elements of the bracket notation.
  const std::string kStructureElements = "{}";

  /// Escape character.
  const char kEscapeChar = '\\';

  /// A regex string to match left and right brackets.
  const std::string kMatchLeftBracket = "\\" + kLeftBracket;
  const std::string kMatchRightBracket = "\\" + kRightBracket;
};

// Implementation details
#include "bracket_notation_parser_impl.h"

} // namespace parser
