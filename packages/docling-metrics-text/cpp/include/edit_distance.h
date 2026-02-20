#pragma once

#include <string>
#include <vector>

namespace docling {

using Word = uint64_t;

class EditDistanceCalculator {
public:
  EditDistanceCalculator();

  // Normalized edit distance: raw distance divided by max(|query|, |target|).
  // Returns 0.0 when both sequences are empty.
  double edit_distance(const std::vector<std::string> &query,
                       const std::vector<std::string> &target);

private:
  // Myers bit-vector edit distance on token sequences (Needleman-Wunsch / global).
  // Returns the raw edit distance (number of insertions, deletions, substitutions).
  int edit_distance_raw(const std::vector<std::string> &query,
                        const std::vector<std::string> &target);

  inline int calculate_block(Word Pv, Word Mv, Word Eq, int hin, Word &PvOut, Word &MvOut);

  inline int ceil_div(int x, int y) { return x % y ? x / y + 1 : x / y; }
};

} // namespace docling
