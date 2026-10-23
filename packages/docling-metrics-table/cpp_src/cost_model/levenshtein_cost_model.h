#pragma once

#include <algorithm>
#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

#include "../label/label_dictionary.h"

namespace cost_model {

/// TEDS cost model with a graded rename cost, the C++ twin of CustomConfig.rename in
/// docling_metrics_table/utils/teds.py.
/**
 * Labels are the strings written by TableTree._label():
 *   "tag": td, "colspan": 1, "rowspan": 1, "text": ['a', '<b', 'x', '</b>']
 * escaped with \\, \{ and \}. Everything before ', "text": ' is the head (tag and spans), the
 * rest is the Python repr of the token list. Rename costs:
 * - 1 if the heads differ,
 * - Levenshtein distance of the token lists / the longer list, if the heads are equal,
 * - 0 if both lists are empty or the label has no text (structure nodes).
 * Insert and delete cost 1.
 *
 * The tokens are never decoded. The repr of a token is unique, so equal reprs are equal tokens
 * and the Levenshtein distance runs over the same token units as apted, whatever their encoding.
 * A text that is not a valid repr list counts as empty, like TableTree.from_bracket does.
 */
template <typename Label> class LevenshteinCostModelLD {
public:
  explicit LevenshteinCostModelLD(label::LabelDictionary<Label> &ld) : ld_(ld) {}

  double ren(const int label_id_1, const int label_id_2) const {
    if (label_id_1 == label_id_2) {
      return 0.0;
    }
    // Resize first: a later resize would invalidate the reference to the first entry.
    if (parsed_.size() < static_cast<size_t>(ld_.size())) {
      parsed_.resize(ld_.size());
    }
    const Parsed &a = get_parsed(label_id_1);
    const Parsed &b = get_parsed(label_id_2);
    if (a.head != b.head) {
      return 1.0;
    }
    const size_t longest = std::max(a.tokens.size(), b.tokens.size());
    if (longest == 0) {
      return 0.0;
    }
    return static_cast<double>(distance(a.tokens, b.tokens)) / static_cast<double>(longest);
  }

  double del(const int) const { return 1.0; }
  double ins(const int) const { return 1.0; }

private:
  struct Parsed {
    bool done = false;
    std::string head;
    std::vector<uint32_t> tokens;
  };

  const Parsed &get_parsed(const int label_id) const {
    Parsed &p = parsed_[label_id];
    if (!p.done) {
      parse(ld_.get(label_id).get_label(), p);
    }
    return p;
  }

  void parse(const std::string &label, Parsed &p) const {
    static const std::string kText = ", \"text\": ";
    p.done = true;
    const size_t split = label.find(kText);
    if (split == std::string::npos) {
      p.head = label;
      return;
    }
    p.head = label.substr(0, split);

    // Undo the label escaping, same rule as _unescape_label in teds.py.
    std::string s;
    for (size_t i = split + kText.size(); i < label.size(); ++i) {
      if (label[i] == '\\' && i + 1 < label.size() &&
          (label[i + 1] == '\\' || label[i + 1] == '{' || label[i + 1] == '}')) {
        ++i;
      }
      s += label[i];
    }

    // Split the repr list into its string literals.
    size_t i = 0;
    const auto skip_space = [&] {
      while (i < s.size() && s[i] == ' ') {
        ++i;
      }
    };
    if (s.empty() || s[i++] != '[') {
      return;
    }
    skip_space();
    while (i < s.size() && s[i] != ']') {
      const char quote = s[i];
      if (quote != '\'' && quote != '"') {
        p.tokens.clear();
        return;
      }
      const size_t begin = ++i;
      while (i < s.size() && s[i] != quote) {
        i += (s[i] == '\\') ? 2 : 1;
      }
      if (i >= s.size()) {
        p.tokens.clear();
        return;
      }
      const auto it = token_ids_.emplace(s.substr(begin, i - begin), token_ids_.size()).first;
      p.tokens.push_back(it->second);
      ++i;
      skip_space();
      if (i < s.size() && s[i] == ',') {
        ++i;
        skip_space();
      } else if (i >= s.size() || s[i] != ']') {
        p.tokens.clear();
        return;
      }
    }
    if (i >= s.size()) {
      p.tokens.clear();
    }
  }

  size_t distance(const std::vector<uint32_t> &a, const std::vector<uint32_t> &b) const {
    row_.resize(b.size() + 1);
    for (size_t j = 0; j <= b.size(); ++j) {
      row_[j] = j;
    }
    for (size_t i = 1; i <= a.size(); ++i) {
      size_t diagonal = row_[0];
      row_[0] = i;
      for (size_t j = 1; j <= b.size(); ++j) {
        const size_t above = row_[j];
        row_[j] = std::min({above + 1, row_[j - 1] + 1, diagonal + (a[i - 1] != b[j - 1])});
        diagonal = above;
      }
    }
    return row_[b.size()];
  }

  const label::LabelDictionary<Label> &ld_;
  // Lazily filled caches, indexed by label id / keyed by token repr.
  mutable std::vector<Parsed> parsed_;
  mutable std::unordered_map<std::string, uint32_t> token_ids_;
  mutable std::vector<size_t> row_;
};

} // namespace cost_model
